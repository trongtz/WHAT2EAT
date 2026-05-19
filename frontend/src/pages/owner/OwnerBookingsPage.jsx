import { Alert, Box, Chip, Grid, Stack, Typography } from "@mui/material";
import { useCallback, useEffect, useMemo, useState } from "react";
import CustomButton from "../../components/CustomButton";
import CustomCard from "../../components/CustomCard";
import EmptyState from "../../components/EmptyState";
import LoadingScreen from "../../components/LoadingScreen";
import SectionHeader from "../../components/SectionHeader";
import { useAuth } from "../../hooks/useAuth";
import { dashboardService } from "../../services/dashboardService";
import { restaurantService } from "../../services/restaurantService";
import { formatDateTime, getStatusColor } from "../../utils/helpers";

const BOOKING_STATUS_LABELS = {
  PENDING: "Chờ duyệt",
  CONFIRMED: "Đã xác nhận",
  REJECTED: "Từ chối",
  CANCELLED: "Đã hủy",
  COMPLETED: "Hoàn thành",
};

function OwnerBookingsPage() {
  const { user } = useAuth();
  const [restaurants, setRestaurants] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const loadData = useCallback(
    async ({ showLoading = true } = {}) => {
      if (showLoading) setLoading(true);
      try {
        const [restaurantData, bookingData] = await Promise.all([
          restaurantService.getOwnerRestaurants(user.id),
          dashboardService.getOwnerBookings(),
        ]);
        setRestaurants(restaurantData);
        setBookings(bookingData);
        setError("");
      } catch (err) {
        setError(err.message);
      } finally {
        if (showLoading) setLoading(false);
      }
    },
    [user.id]
  );

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      loadData({ showLoading: false });
    }, 10000);

    return () => window.clearInterval(intervalId);
  }, [loadData]);

  const groupedBookings = useMemo(() => {
    return restaurants
      .map((restaurant) => ({
        restaurant,
        bookings: bookings.filter((booking) => booking.restaurantId === restaurant.id),
      }))
      .filter((item) => item.bookings.length > 0);
  }, [bookings, restaurants]);

  const handleStatus = async (bookingId, status) => {
    try {
      await dashboardService.updateBookingStatus({ bookingId, status });
      setMessage("Đã cập nhật trạng thái đặt bàn.");
      setError("");
      await loadData({ showLoading: false });
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) return <LoadingScreen message="Đang tải lịch đặt bàn..." />;

  return (
    <Stack spacing={3}>
      <SectionHeader title="Đặt bàn" />
      {message ? <Alert severity="success">{message}</Alert> : null}
      {error ? <Alert severity="error">{error}</Alert> : null}

      {groupedBookings.length ? (
        <Grid container spacing={3}>
          {groupedBookings.map(({ restaurant, bookings: restaurantBookings }) => {
            const confirmedCount = restaurantBookings.filter((item) => item.status === "CONFIRMED").length;
            const pendingCount = restaurantBookings.filter((item) => item.status === "PENDING").length;

            return (
              <Grid key={restaurant.id} size={{ xs: 12 }}>
                <CustomCard>
                  <Stack spacing={2}>
                    <Stack direction={{ xs: "column", lg: "row" }} spacing={2.5}>
                      <Box
                        sx={{
                          width: { xs: "100%", lg: 220 },
                          minWidth: { lg: 220 },
                          height: 160,
                          borderRadius: 2,
                          overflow: "hidden",
                          background: restaurant.image
                            ? `linear-gradient(180deg, rgba(18,22,44,0.05), rgba(18,22,44,0.18)), url(${restaurant.image})`
                            : "linear-gradient(135deg, color-mix(in srgb, var(--app-primary) 18%, white), color-mix(in srgb, var(--app-secondary) 14%, white))",
                          backgroundSize: "cover",
                          backgroundPosition: "center",
                        }}
                      />

                      <Stack spacing={1.1} flex={1}>
                        <Typography variant="h3">{restaurant.name}</Typography>
                        <Typography color="text.secondary">{restaurant.address}</Typography>
                        <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                          <Chip label={restaurant.status === "APPROVED" ? "Đã duyệt" : "Chờ duyệt"} color={restaurant.status === "APPROVED" ? "success" : "warning"} />
                          <Chip label={`${restaurant.averageRating > 0 ? restaurant.averageRating.toFixed(1) : "Chưa có"} sao`} />
                        </Stack>

                        <Grid container spacing={2}>
                          <Grid size={{ xs: 4 }}>
                            <Typography color="text.secondary">Lượt đặt bàn</Typography>
                            <Typography fontWeight={800}>{restaurantBookings.length}</Typography>
                          </Grid>
                          <Grid size={{ xs: 4 }}>
                            <Typography color="text.secondary">Đã xác nhận</Typography>
                            <Typography fontWeight={800}>{confirmedCount}</Typography>
                          </Grid>
                          <Grid size={{ xs: 4 }}>
                            <Typography color="text.secondary">Chờ xử lý</Typography>
                            <Typography fontWeight={800}>{pendingCount}</Typography>
                          </Grid>
                        </Grid>
                      </Stack>
                    </Stack>

                    <Grid container spacing={1.5}>
                      {restaurantBookings.map((booking) => {
                        const statusLabel = booking.statusLabel || BOOKING_STATUS_LABELS[booking.status] || booking.status;

                        return (
                          <Grid key={booking.id} size={{ xs: 12, xl: 6 }}>
                            <Box
                              sx={{
                                p: 1.5,
                                borderRadius: 2,
                                bgcolor: "rgba(248,250,255,0.92)",
                                border: "1px solid rgba(15,23,42,0.06)",
                              }}
                            >
                              <Stack spacing={1}>
                                <Stack direction="row" justifyContent="space-between" alignItems="center">
                                  <Typography fontWeight={800}>{booking.customerName}</Typography>
                                  <Chip label={statusLabel} color={getStatusColor(statusLabel)} />
                                </Stack>
                                <Typography color="text.secondary">
                                  {formatDateTime(booking.reservationTime)} - {booking.guestCount} khách
                                </Typography>
                                <Typography color="text.secondary">Ghi chú: {booking.notes || "Không có"}</Typography>
                                <Chip label={booking.status === "CONFIRMED" ? "Đã sẵn sàng phục vụ" : "Cần xử lý"} sx={{ alignSelf: "flex-start" }} />
                                <Stack direction="row" spacing={1.25} flexWrap="wrap" useFlexGap>
                                  <CustomButton onClick={() => handleStatus(booking.id, "CONFIRMED")}>
                                    Xác nhận
                                  </CustomButton>
                                  <CustomButton
                                    onClick={() => handleStatus(booking.id, "REJECTED")}
                                    sx={{ background: "linear-gradient(135deg, #E85D75 0%, #FB7185 100%)" }}
                                  >
                                    Từ chối
                                  </CustomButton>
                                  <CustomButton
                                    onClick={() => handleStatus(booking.id, "PENDING")}
                                    sx={{ background: "linear-gradient(135deg, #64748B 0%, #94A3B8 100%)" }}
                                  >
                                    Chờ duyệt lại
                                  </CustomButton>
                                </Stack>
                              </Stack>
                            </Box>
                          </Grid>
                        );
                      })}
                    </Grid>
                  </Stack>
                </CustomCard>
              </Grid>
            );
          })}
        </Grid>
      ) : (
        <EmptyState title="Hiện chưa có khách đặt bàn" description="" />
      )}
    </Stack>
  );
}

export default OwnerBookingsPage;
