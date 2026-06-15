import DeleteOutlineRoundedIcon from "@mui/icons-material/DeleteOutlineRounded";
import ArrowBackRoundedIcon from "@mui/icons-material/ArrowBackRounded";
import RateReviewRoundedIcon from "@mui/icons-material/RateReviewRounded";
import { Alert, Box, Chip, Grid, MenuItem, Rating, Stack, Typography } from "@mui/material";
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import CustomButton from "../components/CustomButton";
import CustomCard from "../components/CustomCard";
import EmptyState from "../components/EmptyState";
import FormInput from "../components/FormInput";
import SectionHeader from "../components/SectionHeader";
import { useAuth } from "../hooks/useAuth";
import { restaurantService } from "../services/restaurantService";
import { reviewService } from "../services/reviewService";
import { formatDate } from "../utils/helpers";

const initialFormValues = {
  restaurantId: "",
  rating: 5,
  comment: "",
};

const normalizeReview = (review) => ({
  ...review,
  id: review.id ?? review.review_id,
  reviewId: review.review_id ?? review.id,
  restaurantId: review.restaurantId ?? review.restaurant_id,
  customerId: review.customerId ?? review.customer_id,
  rating: Number(review.rating || 0),
  comment: review.comment ?? "",
  userName: review.userName ?? review.user_name ?? "Khách hàng",
  createdAt: review.createdAt ?? review.created_at,
});

function ReviewPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [restaurants, setRestaurants] = useState([]);
  const [myReviews, setMyReviews] = useState([]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [deletingReviewId, setDeletingReviewId] = useState(null);
  const [values, setValues] = useState(initialFormValues);

  const isCustomer = String(user?.role || "").toLowerCase() === "customer";

  const handleGoBack = () => {
    if (window.history.length > 1) {
      navigate(-1);
      return;
    }
    navigate("/");
  };

  const loadData = async () => {
    setLoading(true);
    setError("");
    try {
      const restaurantData = await restaurantService.getRestaurants();
      setRestaurants(restaurantData);

      if (isCustomer) {
        const reviewData = await reviewService.getMyReviews();
        setMyReviews(reviewData.map(normalizeReview));
      } else {
        setMyReviews([]);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.id, user?.role, user?.isGuest]);

  useEffect(() => {
    const restaurantId = searchParams.get("restaurantId");
    if (restaurantId) {
      setValues((prev) => (prev.restaurantId === restaurantId ? prev : { ...prev, restaurantId }));
    }
  }, [searchParams]);

  const restaurantMap = useMemo(
    () => Object.fromEntries(restaurants.map((restaurant) => [String(restaurant.id), restaurant])),
    [restaurants]
  );

  const myReviewMap = useMemo(
    () => Object.fromEntries(myReviews.map((review) => [String(review.restaurantId), review])),
    [myReviews]
  );

  const handleSubmit = async (event) => {
    event.preventDefault();
    setMessage("");
    setError("");

    if (!user) {
      setError("Vui lòng đăng nhập để gửi đánh giá.");
      return;
    }

    if (!isCustomer) {
      setError("Chỉ khách hàng mới được đánh giá nhà hàng.");
      return;
    }

    if (!values.restaurantId) {
      setError("Vui lòng chọn nhà hàng cần đánh giá.");
      return;
    }

    if (myReviewMap[String(values.restaurantId)]) {
      setError("Bạn chỉ được đánh giá mỗi nhà hàng một lần.");
      return;
    }

    setSubmitting(true);
    try {
      await reviewService.create({
        restaurantId: values.restaurantId,
        rating: values.rating,
        comment: values.comment,
      });
      setMessage("Đánh giá của bạn đã được lưu vào hệ thống.");
      setValues(initialFormValues);
      await loadData();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (reviewId) => {
    setError("");
    setMessage("");
    setDeletingReviewId(reviewId);
    try {
      await reviewService.delete(reviewId);
      setMessage("Đã xoá đánh giá.");
      await loadData();
    } catch (err) {
      setError(err.message);
    } finally {
      setDeletingReviewId(null);
    }
  };

  if (loading) return <Typography>Đang tải đánh giá...</Typography>;

  return (
    <Stack spacing={3}>
      <SectionHeader
        title="Đánh giá nhà hàng"
        description="Bạn cần đăng nhập bằng tài khoản khách để gửi đánh giá. Mỗi nhà hàng chỉ có một đánh giá cho mỗi khách."
      />

      <Stack direction="row" justifyContent="flex-start">
        <CustomButton
          onClick={handleGoBack}
          variant="outlined"
          startIcon={<ArrowBackRoundedIcon />}
          sx={{ alignSelf: "flex-start" }}
        >
          Quay lại
        </CustomButton>
      </Stack>

      {!user ? <Alert severity="warning">Bạn cần đăng nhập để tạo hoặc xoá đánh giá.</Alert> : null}
      {message ? <Alert severity="success">{message}</Alert> : null}
      {error ? <Alert severity="error">{error}</Alert> : null}

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 7 }}>
          <CustomCard>
            <Stack component="form" spacing={2.5} onSubmit={handleSubmit}>
              <Typography variant="h4">Viết đánh giá mới</Typography>

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

              {values.restaurantId && myReviewMap[String(values.restaurantId)] ? (
                <Alert severity="info">Bạn đã đánh giá nhà hàng này rồi. Có thể xoá đánh giá cũ để tạo lại.</Alert>
              ) : null}

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

              <CustomButton type="submit" startIcon={<RateReviewRoundedIcon />} disabled={submitting || !isCustomer}>
                {submitting ? "Đang gửi..." : "Gửi đánh giá"}
              </CustomButton>
            </Stack>
          </CustomCard>
        </Grid>

        <Grid size={{ xs: 12, md: 5 }}>
          <CustomCard>
            <Stack spacing={2}>
              <Typography variant="h4">Đánh giá của bạn</Typography>
              {myReviews.length ? (
                <Stack spacing={1.5}>
                  {myReviews.map((review) => {
                    const restaurant = restaurantMap[String(review.restaurantId)];
                    return (
                      <Box
                        key={review.id}
                        sx={{
                          p: 1.5,
                          borderRadius: 2,
                          bgcolor: "rgba(248,250,255,0.92)",
                          border: "1px solid rgba(15,23,42,0.06)",
                        }}
                      >
                        <Stack spacing={0.8}>
                          <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={1}>
                            <Box>
                              <Typography fontWeight={800}>{restaurant?.name || "Nhà hàng"}</Typography>
                              <Typography variant="body2" color="text.secondary">
                                {formatDate(review.createdAt)}
                              </Typography>
                            </Box>
                            <Chip
                              size="small"
                              label={Number(review.rating || 0).toFixed(1)}
                              sx={{
                                bgcolor: "color-mix(in srgb, var(--app-primary) 10%, white)",
                                color: "var(--app-primary)",
                              }}
                            />
                          </Stack>

                          <Typography color="text.secondary">{review.comment || "Không có nội dung đánh giá."}</Typography>

                          <CustomButton
                            variant="outlined"
                            color="error"
                            startIcon={<DeleteOutlineRoundedIcon />}
                            onClick={() => handleDelete(review.id)}
                            disabled={deletingReviewId === review.id}
                            sx={{ alignSelf: "flex-start" }}
                          >
                            {deletingReviewId === review.id ? "Đang xoá..." : "Xoá"}
                          </CustomButton>
                        </Stack>
                      </Box>
                    );
                  })}
                </Stack>
              ) : (
                <EmptyState
                  title="Chưa có đánh giá nào"
                  description="Bạn hãy chọn một nhà hàng và gửi nhận xét đầu tiên."
                />
              )}
            </Stack>
          </CustomCard>
        </Grid>
      </Grid>
    </Stack>
  );
}

export default ReviewPage;
