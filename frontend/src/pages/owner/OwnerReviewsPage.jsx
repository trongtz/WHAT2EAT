import StarRoundedIcon from "@mui/icons-material/StarRounded";
import { Alert, Box, Grid, Stack, Typography } from "@mui/material";
import { useEffect, useMemo, useState } from "react";
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
  const [error, setError] = useState("");

  useEffect(() => {
    const loadData = async () => {
      try {
        const [reviewData, restaurantData] = await Promise.all([
          dashboardService.getOwnerReviews(),
          restaurantService.getOwnerRestaurants(user.id),
        ]);
        setReviews(reviewData);
        setRestaurantMap(Object.fromEntries(restaurantData.map((item) => [item.id, item])));
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [user.id]);

  const groupedReviews = useMemo(() => {
    const groups = new Map();
    reviews.forEach((review) => {
      const key = review.restaurantId;
      if (!groups.has(key)) {
        groups.set(key, []);
      }
      groups.get(key).push(review);
    });
    return Array.from(groups.entries());
  }, [reviews]);

  if (loading) return <LoadingScreen message="Đang tải đánh giá của khách..." />;

  return (
    <Stack spacing={3}>
      <SectionHeader title="Đánh giá" />
      {error ? <Alert severity="error">{error}</Alert> : null}

      {groupedReviews.length ? (
        <Grid container spacing={3}>
          {groupedReviews.map(([restaurantId, restaurantReviews]) => (
            <Grid key={restaurantId} size={{ xs: 12 }}>
              <CustomCard>
                <Stack spacing={2}>
                  <Typography variant="h4">{restaurantMap[restaurantId]?.name || "Nhà hàng"}</Typography>
                  <Grid container spacing={1.5}>
                    {restaurantReviews.map((review) => (
                      <Grid key={review.id} size={{ xs: 12, xl: 6 }}>
                        <Box
                          sx={{
                            p: 1.5,
                            borderRadius: 2,
                            bgcolor: "rgba(248,250,255,0.92)",
                            border: "1px solid rgba(15,23,42,0.06)",
                          }}
                        >
                          <Stack spacing={0.75}>
                            <Typography fontWeight={800}>{review.userName || "Khách hàng"}</Typography>
                            <Stack direction="row" spacing={0.5} alignItems="center">
                              <StarRoundedIcon sx={{ color: "#F59E0B" }} />
                              <Typography fontWeight={700}>{review.rating}/5</Typography>
                            </Stack>
                            <Typography color="text.secondary">{review.comment || "Không có nội dung đánh giá."}</Typography>
                            <Typography color="text.secondary">{formatDate(review.createdAt)}</Typography>
                          </Stack>
                        </Box>
                      </Grid>
                    ))}
                  </Grid>
                </Stack>
              </CustomCard>
            </Grid>
          ))}
        </Grid>
      ) : (
        <EmptyState title="Không có đánh giá" description="" />
      )}
    </Stack>
  );
}

export default OwnerReviewsPage;
