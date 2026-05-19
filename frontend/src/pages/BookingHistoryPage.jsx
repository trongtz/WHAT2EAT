import { Chip, Stack, Typography } from "@mui/material";
import { useCallback, useEffect, useState } from "react";
import CustomCard from "../components/CustomCard";
import EmptyState from "../components/EmptyState";
import LoadingScreen from "../components/LoadingScreen";
import SectionHeader from "../components/SectionHeader";
import { useAuth } from "../hooks/useAuth";
import { bookingService } from "../services/bookingService";
import { restaurantService } from "../services/restaurantService";
import { getGuestBookings } from "../utils/guestSession";
import { formatDate, getStatusColor } from "../utils/helpers";

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

      setHistory(bookingData);
      setRestaurantMap(Object.fromEntries(restaurantData.map((item) => [item.id, item])));
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
                  <Typography variant="h4">{restaurantMap[booking.restaurantId]?.name || "Nhà hàng"}</Typography>
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
