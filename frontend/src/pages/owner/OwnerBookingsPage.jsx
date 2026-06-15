import AccessTimeRoundedIcon from "@mui/icons-material/AccessTimeRounded";
import CancelRoundedIcon from "@mui/icons-material/CancelRounded";
import CheckCircleRoundedIcon from "@mui/icons-material/CheckCircleRounded";
import EventAvailableRoundedIcon from "@mui/icons-material/EventAvailableRounded";
import ReplayRoundedIcon from "@mui/icons-material/ReplayRounded";
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
import { formatDateTime } from "../../utils/helpers";

const BOOKING_STATUS_LABELS = {
  PENDING: "Chờ duyệt",
  CONFIRMED: "Đã xác nhận",
  REJECTED: "Đã từ chối",
  CANCELLED: "Đã huỷ",
  COMPLETED: "Hoàn thành",
};

const getBookingVisualConfig = (status) => {
  if (status === "CONFIRMED") {
    return {
      label: BOOKING_STATUS_LABELS.CONFIRMED,
      hint: "Bàn đã chốt, ưu tiên chuẩn bị phục vụ.",
      surface: "linear-gradient(135deg, rgba(34,197,94,0.14) 0%, rgba(255,255,255,0.97) 100%)",
      border: "rgba(34,197,94,0.30)",
      accent: "#16a34a",
      chipColor: "success",
      icon: <CheckCircleRoundedIcon sx={{ fontSize: 20 }} />,
    };
  }

  if (status === "REJECTED") {
    return {
      label: BOOKING_STATUS_LABELS.REJECTED,
      hint: "Đã từ chối, nên xem lại lý do trước khi mở lại.",
      surface: "linear-gradient(135deg, rgba(244,63,94,0.14) 0%, rgba(255,255,255,0.97) 100%)",
      border: "rgba(244,63,94,0.30)",
      accent: "#e11d48",
      chipColor: "error",
      icon: <CancelRoundedIcon sx={{ fontSize: 20 }} />,
    };
  }

  if (status === "CANCELLED") {
    return {
      label: BOOKING_STATUS_LABELS.CANCELLED,
      hint: "Khách đã huỷ, không cần thao tác tiếp.",
      surface: "linear-gradient(135deg, rgba(100,116,139,0.14) 0%, rgba(255,255,255,0.97) 100%)",
      border: "rgba(100,116,139,0.25)",
      accent: "#475569",
      chipColor: "default",
      icon: <ReplayRoundedIcon sx={{ fontSize: 20 }} />,
    };
  }

  if (status === "COMPLETED") {
    return {
      label: BOOKING_STATUS_LABELS.COMPLETED,
      hint: "Đơn đã hoàn tất và được lưu trong lịch sử.",
      surface: "linear-gradient(135deg, rgba(59,130,246,0.12) 0%, rgba(255,255,255,0.97) 100%)",
      border: "rgba(59,130,246,0.25)",
      accent: "#2563eb",
      chipColor: "info",
      icon: <EventAvailableRoundedIcon sx={{ fontSize: 20 }} />,
    };
  }

  return {
    label: BOOKING_STATUS_LABELS.PENDING,
    hint: "Cần xác nhận hoặc từ chối để khách thấy ngay.",
    surface: "linear-gradient(135deg, rgba(245,158,11,0.16) 0%, rgba(255,255,255,0.97) 100%)",
    border: "rgba(245,158,11,0.30)",
    accent: "#d97706",
    chipColor: "warning",
    icon: <AccessTimeRoundedIcon sx={{ fontSize: 20 }} />,
  };
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
                          borderRadius: 2.25,
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
                          <Chip
                            label={restaurant.status === "APPROVED" ? "Đã duyệt" : "Chờ duyệt"}
                            color={restaurant.status === "APPROVED" ? "success" : "warning"}
                            sx={{ fontWeight: 700 }}
                          />
                          <Chip
                            label={`${restaurant.averageRating > 0 ? restaurant.averageRating.toFixed(1) : "Chưa có"} sao`}
                            sx={{ fontWeight: 700 }}
                          />
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
                        const statusKey = (booking.status || "PENDING").toUpperCase();
                        const visual = getBookingVisualConfig(statusKey);
                        const statusLabel = booking.statusLabel || BOOKING_STATUS_LABELS[statusKey] || statusKey;
                        const canAct = statusKey === "PENDING" || statusKey === "CONFIRMED" || statusKey === "REJECTED";

                        return (
                          <Grid key={booking.id} size={{ xs: 12, xl: 6 }}>
                            <Box
                              sx={{
                                p: 1.7,
                                borderRadius: 2.5,
                                background: visual.surface,
                                border: `1px solid ${visual.border}`,
                                boxShadow: "0 16px 28px rgba(15,23,42,0.06)",
                                position: "relative",
                                overflow: "hidden",
                                "&::before": {
                                  content: '""',
                                  position: "absolute",
                                  left: 0,
                                  top: 0,
                                  bottom: 0,
                                  width: 6,
                                  background: visual.accent,
                                },
                              }}
                            >
                              <Stack spacing={1.15} sx={{ pl: 0.6, position: "relative", zIndex: 1 }}>
                                <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={1}>
                                  <Stack spacing={0.4}>
                                    <Typography fontWeight={800} sx={{ fontSize: "1.05rem" }}>
                                      {booking.customerName}
                                    </Typography>
                                    <Typography color="text.secondary" sx={{ fontSize: "0.93rem" }}>
                                      {formatDateTime(booking.reservationTime)} - {booking.guestCount} khách
                                    </Typography>
                                  </Stack>
                                  <Chip
                                    icon={visual.icon}
                                    label={statusLabel}
                                    color={visual.chipColor}
                                    sx={{
                                      fontWeight: 800,
                                      "& .MuiChip-icon": { ml: 0.6 },
                                    }}
                                  />
                                </Stack>

                                <Typography color="text.secondary">Ghi chú: {booking.notes || "Không có"}</Typography>

                                <Chip
                                  label={visual.hint}
                                  sx={{
                                    alignSelf: "flex-start",
                                    fontWeight: 700,
                                    bgcolor: "rgba(15,23,42,0.06)",
                                  }}
                                />

                                {canAct ? (
                                  <Stack direction="row" spacing={1.25} flexWrap="wrap" useFlexGap>
                                    {statusKey !== "CONFIRMED" ? (
                                      <CustomButton
                                        onClick={() => handleStatus(booking.id, "CONFIRMED")}
                                        startIcon={<CheckCircleRoundedIcon />}
                                      >
                                        Xác nhận
                                      </CustomButton>
                                    ) : (
                                      <CustomButton
                                        onClick={() => handleStatus(booking.id, "PENDING")}
                                        startIcon={<ReplayRoundedIcon />}
                                        sx={{ background: "linear-gradient(135deg, #64748B 0%, #94A3B8 100%)" }}
                                      >
                                        Chuyển về chờ duyệt
                                      </CustomButton>
                                    )}

                                    {statusKey !== "REJECTED" ? (
                                      <CustomButton
                                        onClick={() => handleStatus(booking.id, "REJECTED")}
                                        startIcon={<CancelRoundedIcon />}
                                        sx={{ background: "linear-gradient(135deg, #E85D75 0%, #FB7185 100%)" }}
                                      >
                                        Từ chối
                                      </CustomButton>
                                    ) : (
                                      <CustomButton
                                        onClick={() => handleStatus(booking.id, "PENDING")}
                                        startIcon={<ReplayRoundedIcon />}
                                        sx={{ background: "linear-gradient(135deg, #64748B 0%, #94A3B8 100%)" }}
                                      >
                                        Chờ duyệt lại
                                      </CustomButton>
                                    )}
                                  </Stack>
                                ) : (
                                  <Chip
                                    label="Không còn thao tác"
                                    sx={{
                                      alignSelf: "flex-start",
                                      fontWeight: 700,
                                      bgcolor: "rgba(15,23,42,0.06)",
                                    }}
                                  />
                                )}
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
