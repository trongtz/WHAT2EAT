import { Chip, Stack, Typography } from "@mui/material";
import { useCallback, useEffect, useState } from "react";
import CustomCard from "../components/CustomCard";
import EmptyState from "../components/EmptyState";
import LoadingScreen from "../components/LoadingScreen";
import SectionHeader from "../components/SectionHeader";
import { useAuth } from "../hooks/useAuth";
import { bookingService, getRecentAiBookings } from "../services/bookingService";
import { restaurantService } from "../services/restaurantService";
import { getGuestBookings } from "../utils/guestSession";
import { formatDate, getStatusColor } from "../utils/helpers";

const mergeBookings = (primaryBookings, secondaryBookings) => {
  const merged = [...primaryBookings];
  const seenIds = new Set(primaryBookings.map((item) => item.id || item.reservationId));

  for (const booking of secondaryBookings) {
    const bookingId = booking.id || booking.reservationId;
    if (seenIds.has(bookingId)) continue;
    merged.unshift(booking);
    seenIds.add(bookingId);
  }

  return merged;
};

function BookingHistoryPage() {
  const { user } = useAuth();
  const [history, setHistory] = useState([]);
  const [restaurantMap, setRestaurantMap] = useState({});
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(
    async ({ showLoading = true } = {}) => {
      if (showLoading) setLoading(true);
      const [bookingData, restaurantData] = await Promise.all([
        user.isGuest ? Promise.resolve(getGuestBookings()) : bookingService.getHistory(user.id),
        restaurantService.getRestaurants(),
      ]);

      const recentAiBookings = user.isGuest ? [] : getRecentAiBookings();
      const mergedBookings = mergeBookings(bookingData, recentAiBookings);
      const restaurantMapSeed = Object.fromEntries(restaurantData.map((item) => [String(item.id), item]));
      const missingRestaurantIds = [...new Set(mergedBookings.map((item) => String(item.restaurantId)).filter((id) => id && !restaurantMapSeed[id]))];

      if (missingRestaurantIds.length) {
        const missingRestaurants = await Promise.allSettled(
          missingRestaurantIds.map((restaurantId) => restaurantService.getRestaurantDetail(restaurantId))
        );

        for (const result of missingRestaurants) {
          if (result.status !== "fulfilled") continue;
          const restaurant = result.value;
          restaurantMapSeed[String(restaurant.id)] = restaurant;
        }
      }

      setHistory(mergedBookings);
      setRestaurantMap(restaurantMapSeed);
      if (showLoading) setLoading(false);
    },
    [user.id, user.isGuest]
  );

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    if (user.isGuest) return undefined;

    const intervalId = window.setInterval(() => {
      loadData({ showLoading: false });
    }, 10000);

    return () => window.clearInterval(intervalId);
  }, [loadData, user.isGuest]);

  if (loading) return <LoadingScreen message="Đang tải lịch sử đặt bàn..." />;

  return (
    <Stack spacing={3}>
      <SectionHeader title="Lịch sử đặt bàn" description="Theo dõi các lần đặt gần đây và trạng thái xác nhận." />
      {history.length ? (
        <Stack spacing={2}>
          {history.map((booking) => (
            <CustomCard key={booking.id}>
              <Stack direction={{ xs: "column", md: "row" }} justifyContent="space-between" spacing={2}>
                <Stack spacing={0.5}>
                  <Typography variant="h4">{restaurantMap[String(booking.restaurantId)]?.name || "Nhà hàng"}</Typography>
                  <Typography color="text.secondary">
                    {formatDate(booking.date)} • {booking.time} • {booking.guests} khách
                  </Typography>
                  <Typography color="text.secondary">Ghi chú: {booking.note || "Không có"}</Typography>
                </Stack>
                <Stack alignItems={{ xs: "flex-start", md: "flex-end" }} spacing={1}>
                  <Chip label={booking.statusLabel || booking.status} color={getStatusColor(booking.statusLabel || booking.status)} />
                </Stack>
              </Stack>
            </CustomCard>
          ))}
        </Stack>
      ) : (
        <EmptyState title="Bạn chưa có lịch sử đặt bàn" description="Hãy chọn một nhà hàng yêu thích và đặt bàn ngay." />
      )}
    </Stack>
  );
}

export default BookingHistoryPage;
