import EventAvailableRoundedIcon from "@mui/icons-material/EventAvailableRounded";
import { Alert, Chip, Grid, Stack, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import CustomButton from "../../components/CustomButton";
import CustomCard from "../../components/CustomCard";
import EmptyState from "../../components/EmptyState";
import LoadingScreen from "../../components/LoadingScreen";
import SectionHeader from "../../components/SectionHeader";
import { useAuth } from "../../hooks/useAuth";
import { dashboardService } from "../../services/dashboardService";
import { restaurantService } from "../../services/restaurantService";
import { formatDate, getStatusColor } from "../../utils/helpers";

function OwnerBookingsPage() {
  const { user } = useAuth();
  const [bookings, setBookings] = useState([]);
  const [restaurantMap, setRestaurantMap] = useState({});
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");

  const loadData = async () => {
    const [bookingData, restaurantData] = await Promise.all([
      dashboardService.getOwnerBookings(user.id),
      restaurantService.getRestaurants(),
    ]);
    setBookings(bookingData);
    setRestaurantMap(Object.fromEntries(restaurantData.map((item) => [item.id, item])));
    setLoading(false);
  };

  useEffect(() => {
    loadData();
  }, [user.id]);

  const handleStatus = async (bookingId, status) => {
    await dashboardService.updateBookingStatus({ bookingId, status });
    setMessage("Đã cập nhật trạng thái đặt bàn.");
    await loadData();
  };

  if (loading) return <LoadingScreen message="Đang tải lịch đặt bàn của nhà hàng..." />;

  return (
    <Stack spacing={3}>
      <SectionHeader
        title="Quản lý đặt bàn"
        description="Xác nhận hoặc hủy các lượt đặt bàn và theo dõi yêu cầu từ khách."
      />
      {message ? <Alert severity="success">{message}</Alert> : null}
      {bookings.length ? (
        <Grid container spacing={3}>
          {bookings.map((booking) => (
            <Grid key={booking.id} size={{ xs: 12, xl: 6 }}>
              <CustomCard>
                <Stack spacing={1.5}>
                  <Stack direction="row" justifyContent="space-between" alignItems="center">
                    <Typography variant="h4">
                      {restaurantMap[booking.restaurantId]?.name || "Nhà hàng"}
                    </Typography>
                    <Chip label={booking.status} color={getStatusColor(booking.status)} />
                  </Stack>
                  <Typography color="text.secondary">Khách hàng: {booking.customerName}</Typography>
                  <Typography color="text.secondary">
                    {formatDate(booking.date)} • {booking.time} • {booking.guests} khách
                  </Typography>
                  <Typography color="text.secondary">Ghi chú: {booking.note || "Không có"}</Typography>
                  <Chip
                    icon={<EventAvailableRoundedIcon />}
                    label={booking.status === "Đã xác nhận" ? "Đã sẵn sàng phục vụ" : "Cần xử lý"}
                    sx={{ alignSelf: "flex-start" }}
                  />
                  <Stack direction="row" spacing={1.25} flexWrap="wrap" useFlexGap>
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
                      Đưa về chờ duyệt
                    </CustomButton>
                  </Stack>
                </Stack>
              </CustomCard>
            </Grid>
          ))}
        </Grid>
      ) : (
        <EmptyState
          title="Chưa có lượt đặt bàn nào"
          description="Khi có khách đặt bàn, dữ liệu sẽ hiển thị tại đây."
        />
      )}
    </Stack>
  );
}

export default OwnerBookingsPage;
