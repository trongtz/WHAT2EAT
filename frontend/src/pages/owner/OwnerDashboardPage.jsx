import NotificationsRoundedIcon from "@mui/icons-material/NotificationsRounded";
import PlaceRoundedIcon from "@mui/icons-material/PlaceRounded";
import StarRoundedIcon from "@mui/icons-material/StarRounded";
import { Alert, Box, Chip, Grid, Stack, Typography } from "@mui/material";
import { useEffect, useMemo, useState } from "react";
import { Link as RouterLink } from "react-router-dom";
import CustomButton from "../../components/CustomButton";
import CustomCard from "../../components/CustomCard";
import EmptyState from "../../components/EmptyState";
import LoadingScreen from "../../components/LoadingScreen";
import StatsCard from "../../components/StatsCard";
import { useAuth } from "../../hooks/useAuth";
import { dashboardService } from "../../services/dashboardService";

const staticNotifications = [
  {
    id: 1,
    title: "Trà Hương đã đánh giá 5 sao cho món Jolibee",
    body: '"tôi đã ăn món ngày 1 tuần liên tục"',
    color: "rgba(245,158,11,0.12)",
  },
  {
    id: 2,
    title: "Minh Anh đã đánh giá 4 sao cho món Gà rán sốt cay",
    body: '"vỏ giòn, sốt ngon nhưng mình muốn phần salad nhiều hơn một chút"',
    color: "rgba(47,107,255,0.12)",
  },
];

function OwnerDashboardPage() {
  const { user } = useAuth();
  const [data, setData] = useState({
    restaurants: [],
    bookings: [],
    reviews: [],
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadData = async () => {
      try {
        const [restaurants, bookings, reviews] = await Promise.all([
          dashboardService.getOwnerRestaurants(user.id),
          dashboardService.getOwnerBookings(),
          dashboardService.getOwnerReviews(),
        ]);
        setData({ restaurants, bookings, reviews });
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [user.id]);

  const stats = useMemo(() => {
    const approvedRestaurants = data.restaurants.filter((item) => item.status === "APPROVED");
    const pendingRestaurants = data.restaurants.filter((item) => item.status === "PENDING");
    const totalMenuItems = approvedRestaurants.reduce((sum, item) => sum + item.menu.length, 0);
    return {
      totalRestaurants: data.restaurants.length,
      approvedRestaurants: approvedRestaurants.length,
      pendingRestaurants: pendingRestaurants.length,
      totalMenuItems,
    };
  }, [data.restaurants]);

  if (loading) return <LoadingScreen message="Đang tải tổng quan..." />;

  return (
    <Stack spacing={3}>
      <SectionTitle />
      {error ? <Alert severity="error">{error}</Alert> : null}

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 3 }}>
          <StatsCard label="Tổng chi nhánh" value={stats.totalRestaurants} color="rgba(255,159,28,0.18)" />
        </Grid>
        <Grid size={{ xs: 12, md: 3 }}>
          <StatsCard label="Đã duyệt" value={stats.approvedRestaurants} color="rgba(45,212,191,0.18)" />
        </Grid>
        <Grid size={{ xs: 12, md: 3 }}>
          <StatsCard label="Chờ duyệt" value={stats.pendingRestaurants} color="rgba(245,158,11,0.18)" />
        </Grid>
        <Grid size={{ xs: 12, md: 3 }}>
          <StatsCard label="Số món ăn" value={stats.totalMenuItems} color="rgba(96,165,250,0.18)" />
        </Grid>
      </Grid>

      {data.restaurants.length ? (
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, lg: 8 }}>
            <CustomCard>
              <Stack spacing={2}>
                <Typography variant="h4">Chi nhánh nổi bật</Typography>
                <Grid container spacing={1.5}>
                  {data.restaurants.map((restaurant) => (
                    <Grid key={restaurant.id} size={{ xs: 12, md: 6 }}>
                      <Box
                        sx={{
                          p: 1.2,
                          borderRadius: 2,
                          border: "1px solid rgba(15,23,42,0.08)",
                          bgcolor: "rgba(255,255,255,0.78)",
                        }}
                      >
                        <Stack direction="row" spacing={1.2}>
                          <Box
                            sx={{
                              width: 108,
                              minWidth: 108,
                              height: 108,
                              borderRadius: 1.75,
                              overflow: "hidden",
                              background: restaurant.image
                                ? `linear-gradient(180deg, rgba(18,22,44,0.05), rgba(18,22,44,0.18)), url(${restaurant.image})`
                                : "linear-gradient(135deg, color-mix(in srgb, var(--app-primary) 18%, white), color-mix(in srgb, var(--app-secondary) 14%, white))",
                              backgroundSize: "cover",
                              backgroundPosition: "center",
                            }}
                          />
                          <Stack spacing={0.45} sx={{ minWidth: 0, flex: 1 }}>
                            <Typography fontWeight={800}>{restaurant.name}</Typography>
                            <Stack direction="row" spacing={0.65} alignItems="center">
                              <PlaceRoundedIcon sx={{ fontSize: 16, color: "var(--app-secondary)" }} />
                              <Typography color="text.secondary" sx={{ fontSize: "0.9rem" }}>
                                {restaurant.address}
                              </Typography>
                            </Stack>
                            <Stack direction="row" spacing={0.75} flexWrap="wrap" useFlexGap>
                              <Chip
                                size="small"
                                icon={<StarRoundedIcon sx={{ color: "#F6B500 !important" }} />}
                                label={
                                  restaurant.averageRating > 0
                                    ? `${restaurant.averageRating.toFixed(1)} sao`
                                    : "Không có đánh giá"
                                }
                              />
                              <Chip
                                size="small"
                                label={restaurant.status === "APPROVED" ? "Đã duyệt" : restaurant.status === "REJECTED" ? "Từ chối" : "Chờ duyệt"}
                                color={restaurant.status === "APPROVED" ? "success" : restaurant.status === "REJECTED" ? "error" : "warning"}
                              />
                            </Stack>
                            <Typography color="text.secondary" sx={{ fontSize: "0.9rem" }}>
                              {restaurant.description || "Chưa có mô tả ngắn cho chi nhánh này."}
                            </Typography>
                            <CustomButton component={RouterLink} to={`/chu-nha-hang/nha-hang/${restaurant.id}`} sx={{ alignSelf: "flex-start" }}>
                              Xem chi tiết
                            </CustomButton>
                          </Stack>
                        </Stack>
                      </Box>
                    </Grid>
                  ))}
                </Grid>
              </Stack>
            </CustomCard>
          </Grid>

          <Grid size={{ xs: 12, lg: 4 }}>
            <CustomCard>
              <Stack spacing={2}>
                <Typography variant="h4">Thông báo</Typography>
                {staticNotifications.map((item) => (
                  <Box
                    key={item.id}
                    sx={{
                      p: 1.5,
                      borderRadius: 2,
                      bgcolor: item.color,
                      border: "1px solid rgba(15,23,42,0.08)",
                    }}
                  >
                    <Stack spacing={0.65}>
                      <Stack direction="row" spacing={1} alignItems="center">
                        <NotificationsRoundedIcon sx={{ color: "var(--app-primary)" }} />
                        <Typography fontWeight={800}>{item.title}</Typography>
                      </Stack>
                      <Typography color="text.secondary">{item.body}</Typography>
                    </Stack>
                  </Box>
                ))}
                <CustomButton sx={{ alignSelf: "flex-start" }}>Xem thêm</CustomButton>
              </Stack>
            </CustomCard>
          </Grid>
        </Grid>
      ) : (
        <EmptyState title="Chưa có chi nhánh nào" description="" />
      )}
    </Stack>
  );
}

function SectionTitle() {
  return (
    <Stack direction="row" justifyContent="space-between" alignItems="center" flexWrap="wrap" useFlexGap>
      <Typography variant="h2">Tổng quan</Typography>
      <CustomButton component={RouterLink} to="/chu-nha-hang/nha-hang">
        Quản lý chi nhánh
      </CustomButton>
    </Stack>
  );
}

export default OwnerDashboardPage;
