import { Chip, Stack, Typography } from "@mui/material";
import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import CustomButton from "../components/CustomButton";
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
  const navigate = useNavigate();
  const [history, setHistory] = useState([]);
  const [restaurantMap, setRestaurantMap] = useState({});
  const [loading, setLoading] = useState(true);
  const [busyBookingId, setBusyBookingId] = useState(null);
  const actionWidth = 154;

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

  const handleCancel = async (booking) => {
    setBusyBookingId(booking.id);
    try {
      await bookingService.cancel(booking.id);
      await loadData({ showLoading: false });
    } finally {
      setBusyBookingId(null);
    }
  };

  const handleChange = (booking) => {
    const restaurantId = booking.restaurantId || "";
    const date = booking.date || "";
    const time = booking.time || "";
    const guests = booking.guests || booking.guestCount || 2;
    const note = booking.note || booking.notes || "";
    const params = new URLSearchParams({
      bookingId: booking.id,
      nhaHang: restaurantId,
      date,
      time,
      guests: String(guests),
      note,
    });
    navigate(`/dat-ban?${params.toString()}`);
  };

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
                <Stack
                  alignItems={{ xs: "flex-start", md: "flex-end" }}
                  spacing={0.9}
                  sx={{ minWidth: { xs: "100%", md: actionWidth } }}
                >
                  <Chip
                    label={booking.statusLabel || booking.status}
                    color={getStatusColor(booking.statusLabel || booking.status)}
                    sx={{
                      width: actionWidth,
                      alignSelf: { xs: "flex-start", md: "flex-end" },
                      justifyContent: "center",
                    }}
                  />
                  {booking.status === "PENDING" ? (
                    <Stack spacing={0.9} sx={{ width: actionWidth }}>
                      <CustomButton
                        variant="outlined"
                        onClick={() => handleChange(booking)}
                        sx={{
                          width: actionWidth,
                          minHeight: 40,
                          py: 0.75,
                          background: "transparent",
                          color: "var(--app-primary)",
                          borderColor: "color-mix(in srgb, var(--app-primary) 28%, white)",
                          boxShadow: "none",
                        }}
                      >
                        Thay đổi thông tin
                      </CustomButton>
                      <CustomButton
                        onClick={() => handleCancel(booking)}
                        disabled={busyBookingId === booking.id}
                        sx={{
                          width: actionWidth,
                          minHeight: 40,
                          py: 0.75,
                          background: "linear-gradient(135deg, #E85D75 0%, #FB7185 100%)",
                          boxShadow: "0 14px 28px rgba(232,93,117,0.22)",
                        }}
                      >
                        {busyBookingId === booking.id ? "Đang hủy..." : "Hủy"}
                      </CustomButton>
                    </Stack>
                  ) : null}
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
