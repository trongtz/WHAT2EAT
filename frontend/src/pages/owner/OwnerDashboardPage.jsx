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
    customer: "Trà Hương",
    title: "đã đánh giá 5 sao cho món Jolibee",
    body: '"tôi đã ăn món này 1 tuần liên tục"',
    tone: "rgba(245,158,11,0.10)",
  },
  {
    id: 2,
    customer: "Minh Anh",
    title: "đã đánh giá 4 sao cho món Gà rán sốt cay",
    body: '"vỏ giòn, sốt ngon nhưng mình muốn phần salad nhiều hơn một chút"',
    tone: "rgba(96,165,250,0.12)",
  },
];

const getStatusConfig = (status) => {
  if (status === "APPROVED") {
    return { label: "Đã duyệt", color: "success" };
  }
  if (status === "REJECTED") {
    return { label: "Từ chối", color: "error" };
  }
  return { label: "Chờ duyệt", color: "warning" };
};

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
    const totalMenuItems = approvedRestaurants.reduce(
      (sum, item) => sum + Number(item.menuCount ?? item.menu?.length ?? 0),
      0
    );

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
        <Grid container spacing={3} alignItems="stretch">
          <Grid size={{ xs: 12, lg: 8 }}>
            <CustomCard sx={{ height: "100%" }}>
              <Stack spacing={2}>
                <Typography variant="h4">Chi nhánh nổi bật</Typography>

                <Stack spacing={1.5}>
                  {data.restaurants.map((restaurant) => {
                    const statusConfig = getStatusConfig(restaurant.status);

                    return (
                      <Box
                        key={restaurant.id}
                        sx={{
                          p: 1.6,
                          borderRadius: 2.25,
                          border: "1px solid rgba(15,23,42,0.08)",
                          bgcolor: "rgba(255,255,255,0.84)",
                        }}
                      >
                        <Stack direction={{ xs: "column", md: "row" }} spacing={1.6}>
                          <Box
                            sx={{
                              width: { xs: "100%", md: 156 },
                              minWidth: { xs: "100%", md: 156 },
                              height: 132,
                              borderRadius: 2,
                              overflow: "hidden",
                              background: restaurant.image
                                ? `linear-gradient(180deg, rgba(18,22,44,0.05), rgba(18,22,44,0.18)), url(${restaurant.image})`
                                : "linear-gradient(135deg, color-mix(in srgb, var(--app-primary) 18%, white), color-mix(in srgb, var(--app-secondary) 14%, white))",
                              backgroundSize: "cover",
                              backgroundPosition: "center",
                              flexShrink: 0,
                            }}
                          />

                          <Stack spacing={1.1} sx={{ minWidth: 0, flex: 1 }}>
                            <Stack spacing={0.55}>
                              <Typography
                                sx={{
                                  fontSize: "1.15rem",
                                  fontWeight: 800,
                                  lineHeight: 1.3,
                                  wordBreak: "break-word",
                                }}
                              >
                                {restaurant.name}
                              </Typography>

                              <Stack direction="row" spacing={0.75} alignItems="flex-start">
                                <PlaceRoundedIcon
                                  sx={{
                                    mt: "2px",
                                    fontSize: 17,
                                    color: "var(--app-secondary)",
                                    flexShrink: 0,
                                  }}
                                />
                                <Typography
                                  color="text.secondary"
                                  sx={{
                                    fontSize: "0.95rem",
                                    lineHeight: 1.55,
                                    wordBreak: "break-word",
                                  }}
                                >
                                  {restaurant.address}
                                </Typography>
                              </Stack>
                            </Stack>

                            <Stack direction="row" spacing={0.85} flexWrap="wrap" useFlexGap>
                              <Chip
                                size="small"
                                icon={<StarRoundedIcon sx={{ color: "#F6B500 !important" }} />}
                                label={
                                  restaurant.averageRating > 0
                                    ? `${restaurant.averageRating.toFixed(1)} sao`
                                    : "Không có đánh giá"
                                }
                                sx={{
                                  bgcolor: "rgba(15,23,42,0.05)",
                                  "& .MuiChip-label": {
                                    fontWeight: 700,
                                  },
                                }}
                              />
                              <Chip
                                size="small"
                                label={statusConfig.label}
                                color={statusConfig.color}
                                sx={{
                                  "& .MuiChip-label": {
                                    fontWeight: 700,
                                  },
                                }}
                              />
                            </Stack>

                            <Typography
                              color="text.secondary"
                              sx={{
                                fontSize: "0.95rem",
                                lineHeight: 1.65,
                                display: "-webkit-box",
                                WebkitBoxOrient: "vertical",
                                WebkitLineClamp: 2,
                                overflow: "hidden",
                              }}
                            >
                              {restaurant.description || "Chưa có mô tả ngắn cho chi nhánh này."}
                            </Typography>

                            <CustomButton
                              component={RouterLink}
                              to={`/chu-nha-hang/nha-hang/${restaurant.id}`}
                              sx={{ alignSelf: "flex-start", minWidth: 150 }}
                            >
                              Xem chi tiết
                            </CustomButton>
                          </Stack>
                        </Stack>
                      </Box>
                    );
                  })}
                </Stack>
              </Stack>
            </CustomCard>
          </Grid>

          <Grid size={{ xs: 12, lg: 4 }}>
            <CustomCard sx={{ height: "100%" }}>
              <Stack spacing={2}>
                <Stack direction="row" spacing={1} alignItems="center">
                  <NotificationsRoundedIcon sx={{ color: "var(--app-primary)", fontSize: 24 }} />
                  <Typography variant="h4">Thông báo</Typography>
                </Stack>

                <Stack spacing={1.1}>
                  {staticNotifications.map((item) => (
                    <Box
                      key={item.id}
                      sx={{
                        p: 1.25,
                        borderRadius: 2,
                        bgcolor: item.tone,
                        border: "1px solid rgba(15,23,42,0.08)",
                      }}
                    >
                      <Stack spacing={0.45} sx={{ minWidth: 0 }}>
                        <Typography
                          sx={{
                            fontSize: "0.98rem",
                            fontWeight: 800,
                            lineHeight: 1.45,
                            wordBreak: "break-word",
                          }}
                        >
                          {item.customer} {item.title}
                        </Typography>
                        <Typography
                          color="text.secondary"
                          sx={{
                            fontSize: "0.94rem",
                            lineHeight: 1.6,
                            display: "-webkit-box",
                            WebkitBoxOrient: "vertical",
                            WebkitLineClamp: 3,
                            overflow: "hidden",
                          }}
                        >
                          {item.body}
                        </Typography>
                      </Stack>
                    </Box>
                  ))}
                </Stack>

                <CustomButton sx={{ alignSelf: "flex-start", minWidth: 140 }}>Xem thêm</CustomButton>
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
