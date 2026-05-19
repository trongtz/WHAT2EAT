import { Alert, Grid, MenuItem, Stack, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import CustomButton from "../components/CustomButton";
import CustomCard from "../components/CustomCard";
import FormInput from "../components/FormInput";
import SectionHeader from "../components/SectionHeader";
import { useAuth } from "../hooks/useAuth";
import { bookingService } from "../services/bookingService";
import { restaurantService } from "../services/restaurantService";
import { createGuestBooking } from "../utils/guestSession";
import { validateBooking } from "../utils/validators";

function BookingPage() {
  const { user } = useAuth();
  const [params] = useSearchParams();
  const [restaurants, setRestaurants] = useState([]);
  const [message, setMessage] = useState("");
  const [errors, setErrors] = useState({});
  const [values, setValues] = useState({
    restaurantId: params.get("nhaHang") || "",
    date: "",
    time: "",
    guests: 2,
    note: "",
  });

  useEffect(() => {
    const fetchRestaurants = async () => {
      const data = await restaurantService.getRestaurants();
      setRestaurants(data);
    };
    fetchRestaurants();
  }, []);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setValues((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    const nextErrors = validateBooking(values);
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length) return;

    if (!user) {
      setMessage("Vui lòng đăng nhập trước khi đặt bàn.");
      return;
    }

    if (user.isGuest) {
      createGuestBooking(values);
      setMessage("Đặt bàn tạm thời đã được lưu trong phiên khách này.");
    } else {
      await bookingService.create({ ...values, userId: user.id, guests: Number(values.guests) });
      setMessage("Đặt bàn thành công. Bạn có thể xem trạng thái ở lịch sử đặt bàn.");
    }

    setValues({ ...values, date: "", time: "", guests: 2, note: "" });
  };

  return (
    <Stack spacing={3}>
      <SectionHeader title="Đặt bàn" description="Hoàn tất thông tin để giữ chỗ nhanh chóng tại nhà hàng bạn yêu thích." />
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 7 }}>
          <CustomCard>
            <Stack component="form" spacing={2.5} onSubmit={handleSubmit}>
              {message ? <Alert severity="success">{message}</Alert> : null}
              <FormInput select label="Nhà hàng" name="restaurantId" value={values.restaurantId} onChange={handleChange} error={!!errors.restaurantId} helperText={errors.restaurantId}>
                <MenuItem value="">Chọn nhà hàng</MenuItem>
                {restaurants.map((restaurant) => (
                  <MenuItem key={restaurant.id} value={restaurant.id}>
                    {restaurant.name}
                  </MenuItem>
                ))}
              </FormInput>
              <Grid container spacing={2}>
                <Grid size={{ xs: 12, md: 4 }}>
                  <FormInput type="date" label="Ngày" name="date" value={values.date} onChange={handleChange} InputLabelProps={{ shrink: true }} error={!!errors.date} helperText={errors.date} />
                </Grid>
                <Grid size={{ xs: 12, md: 4 }}>
                  <FormInput type="time" label="Giờ" name="time" value={values.time} onChange={handleChange} InputLabelProps={{ shrink: true }} error={!!errors.time} helperText={errors.time} />
                </Grid>
                <Grid size={{ xs: 12, md: 4 }}>
                  <FormInput type="number" label="Số khách" name="guests" value={values.guests} onChange={handleChange} error={!!errors.guests} helperText={errors.guests} />
                </Grid>
              </Grid>
              <FormInput multiline rows={4} label="Ghi chú" name="note" value={values.note} onChange={handleChange} />
              <CustomButton type="submit">
                Xác nhận đặt bàn
              </CustomButton>
            </Stack>
          </CustomCard>
        </Grid>
        <Grid size={{ xs: 12, md: 5 }}>
          <CustomCard>
            <Stack spacing={1.5}>
              <Typography variant="h4">Lưu ý khi đặt bàn</Typography>
              <Typography color="text.secondary">Bạn nên đặt trước ít nhất 30 phút để hệ thống dễ gợi ý bàn phù hợp.</Typography>
              <Typography color="text.secondary">Với nhóm đông, hãy ghi chú yêu cầu vị trí ngồi hoặc khu vực riêng nếu cần.</Typography>
              <Typography color="text.secondary">Chế độ Khách sẽ chỉ lưu đặt bàn trong phiên hiện tại và không ghi vào database.</Typography>
            </Stack>
          </CustomCard>
        </Grid>
      </Grid>
    </Stack>
  );
}

export default BookingPage;
