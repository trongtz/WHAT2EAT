import RateReviewRoundedIcon from "@mui/icons-material/RateReviewRounded";
import { Alert, Grid, MenuItem, Rating, Stack, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import CustomButton from "../components/CustomButton";
import CustomCard from "../components/CustomCard";
import FormInput from "../components/FormInput";
import SectionHeader from "../components/SectionHeader";
import { useAuth } from "../hooks/useAuth";
import { restaurantService } from "../services/restaurantService";
import { reviewService } from "../services/reviewService";
import { createGuestReview } from "../utils/guestSession";

function ReviewPage() {
  const { user } = useAuth();
  const [restaurants, setRestaurants] = useState([]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [values, setValues] = useState({ restaurantId: "", rating: 5, comment: "" });

  useEffect(() => {
    const fetchData = async () => {
      const data = await restaurantService.getRestaurants();
      setRestaurants(data);
    };
    fetchData();
  }, []);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setMessage("");
    setError("");

    if (!user) {
      setError("Vui lòng đăng nhập để gửi đánh giá.");
      return;
    }

    if (!values.restaurantId) {
      setError("Vui lòng chọn nhà hàng cần đánh giá.");
      return;
    }

    try {
      if (user.isGuest) {
        createGuestReview({
          restaurantId: values.restaurantId,
          rating: values.rating,
          comment: values.comment,
          userName: user.fullName,
        });
        setMessage("Đánh giá của bạn đã được lưu trong phiên khách.");
      } else {
        await reviewService.create({
          restaurantId: values.restaurantId,
          rating: values.rating,
          comment: values.comment,
          userName: user.fullName,
        });
        setMessage("Đánh giá của bạn đã được ghi nhận.");
      }

      setValues({ restaurantId: "", rating: 5, comment: "" });
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <Stack spacing={3}>
      <SectionHeader
        title="Đánh giá nhà hàng"
        description="Chia sẻ trải nghiệm để cộng đồng có thêm thông tin trước khi đặt bàn."
      />
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 7 }}>
          <CustomCard>
            <Stack component="form" spacing={2.5} onSubmit={handleSubmit}>
              {message ? <Alert severity="success">{message}</Alert> : null}
              {error ? <Alert severity="error">{error}</Alert> : null}
              <FormInput
                select
                label="Nhà hàng"
                value={values.restaurantId}
                onChange={(event) => setValues((prev) => ({ ...prev, restaurantId: event.target.value }))}
              >
                <MenuItem value="">Chọn nhà hàng</MenuItem>
                {restaurants.map((restaurant) => (
                  <MenuItem key={restaurant.id} value={restaurant.id}>
                    {restaurant.name}
                  </MenuItem>
                ))}
              </FormInput>
              <Stack spacing={1}>
                <Typography>Điểm đánh giá</Typography>
                <Rating
                  value={values.rating}
                  onChange={(_, nextValue) => setValues((prev) => ({ ...prev, rating: nextValue || 5 }))}
                />
              </Stack>
              <FormInput
                multiline
                rows={5}
                label="Nhận xét"
                value={values.comment}
                onChange={(event) => setValues((prev) => ({ ...prev, comment: event.target.value }))}
              />
              <CustomButton type="submit" startIcon={<RateReviewRoundedIcon />}>
                Gửi đánh giá
              </CustomButton>
            </Stack>
          </CustomCard>
        </Grid>
      </Grid>
    </Stack>
  );
}

export default ReviewPage;
