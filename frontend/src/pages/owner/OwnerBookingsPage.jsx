import EventAvailableRoundedIcon from "@mui/icons-material/EventAvailableRounded";
import PlaceRoundedIcon from "@mui/icons-material/PlaceRounded";
import StarRoundedIcon from "@mui/icons-material/StarRounded";
import VisibilityRoundedIcon from "@mui/icons-material/VisibilityRounded";
import { Alert, Box, Chip, Grid, Stack, Typography } from "@mui/material";
import { useEffect, useMemo, useState } from "react";
import { Link as RouterLink } from "react-router-dom";
import CustomButton from "../../components/CustomButton";
import CustomCard from "../../components/CustomCard";
import EmptyState from "../../components/EmptyState";
import LoadingScreen from "../../components/LoadingScreen";
import SectionHeader from "../../components/SectionHeader";
import { useAuth } from "../../hooks/useAuth";
import { dashboardService } from "../../services/dashboardService";
import { restaurantService } from "../../services/restaurantService";
import { getRestaurantStatusLabel, getStatusColor } from "../../utils/helpers";

const normalizeStatusToken = (status) =>
  String(status || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toUpperCase()
    .trim();

const getBookingRestaurantId = (booking) => booking.restaurantId ?? booking.restaurant_id ?? booking.restaurant?.id;
const getBookingGuests = (booking) => booking.guests ?? booking.guestCount ?? booking.guest_count ?? 0;
const getBookingNote = (booking) => booking.note ?? booking.notes ?? "";

const getBookingDateTimeValue = (booking) => {
  if (booking.reservationTime) return booking.reservationTime;
  if (booking.reservation_time) return booking.reservation_time;
  if (booking.date && booking.time) return `${booking.date}T${booking.time}`;
  return booking.date ?? null;
};

const formatBookingDate = (booking) => {
  const value = getBookingDateTimeValue(booking);
  if (!value) return "--";
  return new Intl.DateTimeFormat("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(new Date(value));
};

const formatBookingTime = (booking) => {
  if (booking.time) return booking.time;
  const value = getBookingDateTimeValue(booking);
  if (!value) return "--";
  return new Intl.DateTimeFormat("vi-VN", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
};

const getRestaurantRatingLabel = (restaurant) =>
  Number(restaurant.reviewCount || 0) > 0
    ? `${Number(restaurant.averageRating || 0).toFixed(1)} sao`
    : "Không có đánh giá";

const getStatusLabel = (status) => {
  const token = normalizeStatusToken(status);

  if (token === "PENDING" || token === "CHO DUYET") return "Chờ duyệt";
  if (token === "CONFIRMED" || token === "DA XAC NHAN") return "Đã xác nhận";
  if (token === "REJECTED" || token === "TU CHOI") return "Từ chối";
  if (token === "CANCELLED" || token === "DA HUY") return "Đã hủy";

  return status || "--";
};

const getPendingCount = (bookings) =>
  bookings.filter((booking) => {
    const token = normalizeStatusToken(booking.status);
    return token === "PENDING" || token === "CHO DUYET";
  }).length;

const getConfirmedCount = (bookings) =>
  bookings.filter((booking) => {
    const token = normalizeStatusToken(booking.status);
    return token === "CONFIRMED" || token === "DA XAC NHAN";
  }).length;

const sortBookings = (bookings) =>
  [...bookings].sort((left, right) => {
    const leftToken = normalizeStatusToken(left.status);
    const rightToken = normalizeStatusToken(right.status);
    const leftWeight = leftToken === "PENDING" || leftToken === "CHO DUYET" ? 0 : 1;
    const rightWeight = rightToken === "PENDING" || rightToken === "CHO DUYET" ? 0 : 1;

    if (leftWeight !== rightWeight) {
      return leftWeight - rightWeight;
    }

    const leftTime = new Date(getBookingDateTimeValue(left) || 0).getTime();
    const rightTime = new Date(getBookingDateTimeValue(right) || 0).getTime();
    return rightTime - leftTime;
  });

function OwnerBookingsPage() {
  const { user } = useAuth();
  const [bookings, setBookings] = useState([]);
  const [restaurants, setRestaurants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");

  const loadData = async () => {
    const [bookingData, ownerRestaurants] = await Promise.all([
      dashboardService.getOwnerBookings(user.id),
      restaurantService.getOwnerRestaurants(user.id),
    ]);

    setBookings(Array.isArray(bookingData) ? bookingData : []);
    setRestaurants(ownerRestaurants);
    setLoading(false);
  };

  useEffect(() => {
    loadData();
  }, [user.id]);

  const groupedRestaurants = useMemo(() => {
    return restaurants
      .map((restaurant) => {
        const restaurantBookings = sortBookings(
          bookings.filter((booking) => String(getBookingRestaurantId(booking)) === String(restaurant.id))
        );

        return {
          ...restaurant,
          bookings: restaurantBookings,
          pendingCount: getPendingCount(restaurantBookings),
          confirmedCount: getConfirmedCount(restaurantBookings),
        };
      })
      .filter((restaurant) => restaurant.bookings.length > 0);
  }, [bookings, restaurants]);

  const handleStatus = async (bookingId, status) => {
    await dashboardService.updateBookingStatus({ bookingId, status });
    setMessage("Đã cập nhật trạng thái đặt bàn.");
    await loadData();
  };

  if (loading) return <LoadingScreen message="Đang tải dữ liệu đặt bàn theo chi nhánh..." />;

  if (!restaurants.length) {
    return (
      <Stack spacing={3}>
        <SectionHeader
          title="Quản lý đặt bàn"
          description="Mỗi chi nhánh sẽ có khu vực đặt bàn riêng để bạn quan sát và xử lý dễ hơn."
        />
        <EmptyState
          title="Chưa có chi nhánh để quản lý đặt bàn"
          description="Khi bạn tạo chi nhánh và được admin duyệt, khu vực đặt bàn của từng chi nhánh sẽ xuất hiện tại đây."
        />
      </Stack>
    );
  }

  if (!bookings.length || !groupedRestaurants.length) {
    return (
      <Stack spacing={3}>
        <SectionHeader
          title="Quản lý đặt bàn theo chi nhánh"
          description="Khi có khách đặt bàn, hệ thống sẽ hiển thị từng đơn theo đúng chi nhánh để bạn theo dõi."
        />
        <EmptyState
          title="Hiện chưa có khách đặt bàn"
          description="Nếu chưa có đơn nào thì khu vực này sẽ để trống. Khi có khách đặt, dữ liệu sẽ hiện tại đây."
        />
      </Stack>
    );
  }

  return (
    <Stack spacing={3}>
      <SectionHeader
        title="Quản lý đặt bàn theo chi nhánh"
        description="Chỉ các chi nhánh đang có đơn đặt bàn mới hiển thị tại đây để bạn theo dõi gọn hơn."
      />

      {message ? <Alert severity="success">{message}</Alert> : null}

      <Grid container spacing={3}>
        {groupedRestaurants.map((restaurant) => (
          <Grid key={restaurant.id} size={{ xs: 12, xl: 6 }}>
            <CustomCard contentSx={{ p: 2.5, "&:last-child": { pb: 2.5 } }} sx={{ height: "100%" }}>
              <Stack spacing={2.25}>
                <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
                  <Box
                    sx={{
                      width: { xs: "100%", md: 168 },
                      height: 128,
                      borderRadius: 2,
                      flexShrink: 0,
                      background: restaurant.image
                        ? `linear-gradient(180deg, rgba(18,22,44,0.08), rgba(18,22,44,0.24)), url(${restaurant.image})`
                        : "linear-gradient(135deg, rgba(255,159,28,0.22), rgba(47,107,255,0.18))",
                      backgroundPosition: "center",
                      backgroundSize: "cover",
                      border: "1px solid rgba(15,23,42,0.06)",
                    }}
                  />

                  <Stack spacing={1} flex={1}>
                    <Stack
                      direction={{ xs: "column", sm: "row" }}
                      spacing={1}
                      justifyContent="space-between"
                      alignItems={{ xs: "flex-start", sm: "flex-start" }}
                    >
                      <Stack spacing={0.4}>
                        <Typography variant="h4">{restaurant.name}</Typography>
                        <Typography color="text.secondary" sx={{ lineHeight: 1.55 }}>
                          {restaurant.description || "Chi nhánh này đang sẵn sàng nhận và xử lý các lượt đặt bàn."}
                        </Typography>
                      </Stack>

                      <CustomButton
                        component={RouterLink}
                        to={`/chu-nha-hang/nha-hang/${restaurant.id}`}
                        startIcon={<VisibilityRoundedIcon />}
                        sx={{ alignSelf: { xs: "stretch", sm: "flex-start" } }}
                      >
                        Xem chi tiết
                      </CustomButton>
                    </Stack>

                    <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                      <Chip icon={<PlaceRoundedIcon />} label={restaurant.address || "Chưa có địa chỉ"} variant="outlined" />
                      <Chip icon={<StarRoundedIcon />} label={getRestaurantRatingLabel(restaurant)} variant="outlined" />
                      <Chip label={getRestaurantStatusLabel(restaurant.status)} color={getStatusColor(restaurant.status)} />
                    </Stack>
                  </Stack>
                </Stack>

                <Grid container spacing={1.5}>
                  <Grid size={{ xs: 12, sm: 4 }}>
                    <Box
                      sx={{
                        p: 1.5,
                        borderRadius: 2,
                        bgcolor: "rgba(255, 248, 238, 0.95)",
                        border: "1px solid rgba(255, 159, 28, 0.14)",
                      }}
                    >
                      <Typography color="text.secondary" sx={{ fontSize: "0.92rem" }}>
                        Lượt đặt bàn
                      </Typography>
                      <Typography sx={{ fontSize: "1.9rem", fontWeight: 800, lineHeight: 1.1 }}>
                        {restaurant.bookings.length}
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid size={{ xs: 12, sm: 4 }}>
                    <Box
                      sx={{
                        p: 1.5,
                        borderRadius: 2,
                        bgcolor: "rgba(236, 252, 245, 0.96)",
                        border: "1px solid rgba(45, 181, 111, 0.14)",
                      }}
                    >
                      <Typography color="text.secondary" sx={{ fontSize: "0.92rem" }}>
                        Đã xác nhận
                      </Typography>
                      <Typography sx={{ fontSize: "1.9rem", fontWeight: 800, lineHeight: 1.1 }}>
                        {restaurant.confirmedCount}
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid size={{ xs: 12, sm: 4 }}>
                    <Box
                      sx={{
                        p: 1.5,
                        borderRadius: 2,
                        bgcolor: "rgba(248, 250, 255, 0.96)",
                        border: "1px solid rgba(47, 107, 255, 0.10)",
                      }}
                    >
                      <Typography color="text.secondary" sx={{ fontSize: "0.92rem" }}>
                        Chờ xử lý
                      </Typography>
                      <Typography sx={{ fontSize: "1.9rem", fontWeight: 800, lineHeight: 1.1 }}>
                        {restaurant.pendingCount}
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>

                <Stack spacing={1.25}>
                  {restaurant.bookings.map((booking) => (
                    <Box
                      key={booking.id}
                      sx={{
                        p: 1.6,
                        borderRadius: 2,
                        bgcolor: "rgba(248,250,255,0.92)",
                        border: "1px solid rgba(15,23,42,0.06)",
                      }}
                    >
                      <Stack spacing={1.2}>
                        <Stack
                          direction={{ xs: "column", sm: "row" }}
                          spacing={1.2}
                          justifyContent="space-between"
                          alignItems={{ xs: "flex-start", sm: "center" }}
                        >
                          <Stack spacing={0.45}>
                            <Typography sx={{ fontWeight: 800, fontSize: "1rem" }}>
                              {booking.customerName || "Khách hàng"}
                            </Typography>
                            <Typography color="text.secondary">
                              {formatBookingDate(booking)} • {formatBookingTime(booking)} • {getBookingGuests(booking)} khách
                            </Typography>
                          </Stack>

                          <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap" useFlexGap>
                            <Chip label={getStatusLabel(booking.status)} color={getStatusColor(booking.status)} />
                            <Chip
                              icon={<EventAvailableRoundedIcon />}
                              label={restaurant.pendingCount ? "Đang cần theo dõi" : "Đã ổn định"}
                              variant="outlined"
                            />
                          </Stack>
                        </Stack>

                        <Typography color="text.secondary">
                          Ghi chú: {getBookingNote(booking) || "Không có"}
                        </Typography>

                        <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                          <CustomButton onClick={() => handleStatus(booking.id, "Đã xác nhận")}>
                            Xác nhận
                          </CustomButton>
                          <CustomButton
                            onClick={() => handleStatus(booking.id, "Đã hủy")}
                            sx={{ background: "linear-gradient(135deg, #E85D75 0%, #FB7185 100%)" }}
                          >
                            Hủy lịch
                          </CustomButton>
                          <CustomButton
                            onClick={() => handleStatus(booking.id, "Chờ duyệt")}
                            sx={{ background: "linear-gradient(135deg, #64748B 0%, #94A3B8 100%)" }}
                          >
                            Chờ duyệt lại
                          </CustomButton>
                        </Stack>
                      </Stack>
                    </Box>
                  ))}
                </Stack>
              </Stack>
            </CustomCard>
          </Grid>
        ))}
      </Grid>
    </Stack>
  );
}

export default OwnerBookingsPage;
