import StarRoundedIcon from "@mui/icons-material/StarRounded";
import { Chip, Grid, Stack, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import CustomCard from "../../components/CustomCard";
import EmptyState from "../../components/EmptyState";
import LoadingScreen from "../../components/LoadingScreen";
import SectionHeader from "../../components/SectionHeader";
import { useAuth } from "../../hooks/useAuth";
import { dashboardService } from "../../services/dashboardService";
import { restaurantService } from "../../services/restaurantService";
import { formatDate } from "../../utils/helpers";

function OwnerReviewsPage() {
  const { user } = useAuth();
  const [reviews, setReviews] = useState([]);
  const [restaurantMap, setRestaurantMap] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      const [reviewData, restaurantData] = await Promise.all([
        dashboardService.getOwnerReviews(user.id),
        restaurantService.getOwnerRestaurants(user.id),
      ]);

      setReviews(Array.isArray(reviewData) ? reviewData : []);
      setRestaurantMap(Object.fromEntries(restaurantData.map((item) => [item.id, item])));
      setLoading(false);
    };

    loadData();
  }, [user.id]);

  if (loading) return <LoadingScreen message="Đang tải đánh giá của khách..." />;

  return (
    <Stack spacing={3}>
      <SectionHeader title="Đánh giá nhà hàng" />

      {reviews.length ? (
        <Grid container spacing={3}>
          {reviews.map((review) => (
            <Grid key={review.id} size={{ xs: 12, xl: 6 }}>
              <CustomCard>
                <Stack spacing={1.5}>
                  <Stack direction="row" justifyContent="space-between" spacing={1} alignItems="flex-start">
                    <Stack spacing={0.5}>
                      <Typography variant="h4">
                        {restaurantMap[review.restaurantId]?.name || "Chi nhánh"}
                      </Typography>
                      <Typography color="text.secondary">{review.userName || "Khách hàng"}</Typography>
                    </Stack>

                    <Chip
                      icon={<StarRoundedIcon sx={{ color: "#F59E0B !important" }} />}
                      label={`${Number(review.rating || 0).toFixed(1)} sao`}
                      variant="outlined"
                    />
                  </Stack>

                  <Typography color="text.secondary">
                    {review.comment?.trim() || "Không có nội dung đánh giá."}
                  </Typography>
                  <Typography color="text.secondary">{formatDate(review.createdAt)}</Typography>
                </Stack>
              </CustomCard>
            </Grid>
          ))}
        </Grid>
      ) : (
        <EmptyState title="Không có đánh giá" />
      )}
    </Stack>
  );
}

export default OwnerReviewsPage;
