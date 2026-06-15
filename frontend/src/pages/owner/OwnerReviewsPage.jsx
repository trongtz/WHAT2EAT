import StarRoundedIcon from "@mui/icons-material/StarRounded";
import { Alert, Box, Grid, Stack, Typography } from "@mui/material";
import { useEffect, useMemo, useState } from "react";
import CustomButton from "../../components/CustomButton";
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
  const [expandedRestaurants, setExpandedRestaurants] = useState({});
  const [loadingMoreRestaurantId, setLoadingMoreRestaurantId] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [reviewData, restaurantData] = await Promise.all([
          dashboardService.getOwnerReviews({ skip: 0, limit: 1000 }),
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

  const toggleExpanded = (restaurantId) => {
    setExpandedRestaurants((current) => ({
      ...current,
      [restaurantId]: !current[restaurantId],
    }));
  };

  const loadMoreRestaurantReviews = async (restaurantId) => {
    if (loadingMoreRestaurantId) return;

    const currentCount = groupedReviews.find(([id]) => String(id) === String(restaurantId))?.[1]?.length || 0;
    setLoadingMoreRestaurantId(restaurantId);
    try {
      const nextPage = await dashboardService.getOwnerReviews({ skip: currentCount, limit: 8, restaurantId });
      if (!nextPage.length) {
        setExpandedRestaurants((current) => ({ ...current, [restaurantId]: true }));
        return;
      }
      setReviews((current) => [...current, ...nextPage]);
      setExpandedRestaurants((current) => ({ ...current, [restaurantId]: true }));
    } finally {
      setLoadingMoreRestaurantId(null);
    }
  };

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
                    {(expandedRestaurants[restaurantId] ? restaurantReviews : restaurantReviews.slice(0, 4)).map((review) => (
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
                  {restaurantReviews.length > 4 ? (
                    <CustomButton
                      variant="outlined"
                      onClick={() => (expandedRestaurants[restaurantId] ? toggleExpanded(restaurantId) : loadMoreRestaurantReviews(restaurantId))}
                      disabled={loadingMoreRestaurantId === restaurantId}
                      sx={{
                        alignSelf: "flex-start",
                        background: "transparent",
                        color: "var(--app-primary)",
                        borderColor: "color-mix(in srgb, var(--app-primary) 24%, white)",
                        boxShadow: "none",
                      }}
                    >
                      {loadingMoreRestaurantId === restaurantId
                        ? "Đang tải..."
                        : expandedRestaurants[restaurantId]
                          ? "Thu gọn"
                          : "Xem thêm"}
                    </CustomButton>
                  ) : null}
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
