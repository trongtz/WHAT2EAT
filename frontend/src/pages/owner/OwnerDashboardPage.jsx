import CheckCircleRoundedIcon from "@mui/icons-material/CheckCircleRounded";
import PlaceRoundedIcon from "@mui/icons-material/PlaceRounded";
import RestaurantMenuRoundedIcon from "@mui/icons-material/RestaurantMenuRounded";
import StarRoundedIcon from "@mui/icons-material/StarRounded";
import { Box, Chip, Grid, Stack, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import { Link as RouterLink } from "react-router-dom";
import CustomButton from "../../components/CustomButton";
import CustomCard from "../../components/CustomCard";
import EmptyState from "../../components/EmptyState";
import LoadingScreen from "../../components/LoadingScreen";
import SectionHeader from "../../components/SectionHeader";
import StatsCard from "../../components/StatsCard";
import { useAuth } from "../../hooks/useAuth";
import { restaurantService } from "../../services/restaurantService";

function OwnerDashboardPage() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [restaurants, setRestaurants] = useState([]);
  const [menuCount, setMenuCount] = useState(0);

  useEffect(() => {
    const loadData = async () => {
      const ownerRestaurants = await restaurantService.getOwnerRestaurants(user.id);
      const approvedRestaurants = ownerRestaurants.filter((item) => item.status === "APPROVED");
      const menus = await Promise.all(
        approvedRestaurants.map((restaurant) => restaurantService.getRestaurantMenu(restaurant.id))
      );

      setRestaurants(ownerRestaurants);
      setMenuCount(menus.reduce((sum, items) => sum + items.length, 0));
      setLoading(false);
    };

    loadData();
  }, [user.id]);

  if (loading) return <LoadingScreen message="Đang tải tổng quan chi nhánh..." />;

  if (!restaurants.length) {
    return (
      <Stack spacing={3}>
        <SectionHeader title="Khởi tạo hệ thống chi nhánh" />
        <EmptyState title="Chưa có chi nhánh nào" />
        <CustomButton component={RouterLink} to="/chu-nha-hang/nha-hang" sx={{ alignSelf: "flex-start" }}>
          Đăng ký chi nhánh đầu tiên
        </CustomButton>
      </Stack>
    );
  }

  const approvedCount = restaurants.filter((item) => item.status === "APPROVED").length;
  const pendingCount = restaurants.filter((item) => item.status === "PENDING").length;
  const featuredBranches = [...restaurants]
    .sort((a, b) => Number(b.averageRating || 0) - Number(a.averageRating || 0))
    .slice(0, 3);

  return (
    <Stack spacing={3}>
      <SectionHeader
        title="Tổng quan"
        action={
          <CustomButton component={RouterLink} to="/chu-nha-hang/nha-hang">
            Quản lý chi nhánh
          </CustomButton>
        }
      />

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 3 }}>
          <StatsCard label="Tổng chi nhánh" value={restaurants.length} color="rgba(255,159,28,0.22)" />
        </Grid>
        <Grid size={{ xs: 12, md: 3 }}>
          <StatsCard label="Đã duyệt" value={approvedCount} color="rgba(32,180,134,0.18)" />
        </Grid>
        <Grid size={{ xs: 12, md: 3 }}>
          <StatsCard label="Chờ duyệt" value={pendingCount} color="rgba(245,158,11,0.22)" />
        </Grid>
        <Grid size={{ xs: 12, md: 3 }}>
          <StatsCard label="Số món ăn" value={menuCount} color="rgba(47,107,255,0.18)" />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, lg: 8 }}>
          <CustomCard>
            <Stack spacing={2.25}>
              <Stack
                direction={{ xs: "column", md: "row" }}
                justifyContent="space-between"
                alignItems={{ xs: "flex-start", md: "center" }}
                spacing={1}
              >
                <Typography variant="h4">Chi nhánh nổi bật</Typography>
                <Chip
                  icon={<CheckCircleRoundedIcon />}
                  label={`${approvedCount}/${restaurants.length} chi nhánh đã duyệt`}
                  color="success"
                  variant="outlined"
                />
              </Stack>

              <Grid container spacing={2}>
                {featuredBranches.map((restaurant) => (
                  <Grid key={restaurant.id} size={{ xs: 12, md: 6, xl: 4 }}>
                    <Box
                      sx={{
                        height: "100%",
                        overflow: "hidden",
                        borderRadius: 2,
                        border: "1px solid rgba(15,23,42,0.08)",
                        bgcolor: "rgba(248,250,255,0.94)",
                        boxShadow: "inset 0 1px 0 rgba(255,255,255,0.72)",
                      }}
                    >
                      <Box
                        sx={{
                          height: 132,
                          background: restaurant.image
                            ? `linear-gradient(180deg, rgba(18,22,44,0.06), rgba(18,22,44,0.2)), url(${restaurant.image})`
                            : "linear-gradient(135deg, rgba(255,159,28,0.24), rgba(47,107,255,0.18))",
                          backgroundPosition: "center",
                          backgroundSize: "cover",
                        }}
                      />
                      <Stack spacing={1.1} sx={{ p: 1.75 }}>
                        <Stack direction="row" justifyContent="space-between" spacing={1}>
                          <Typography fontWeight={800} sx={{ lineHeight: 1.35 }}>
                            {restaurant.name}
                          </Typography>
                          <Chip
                            size="small"
                            label={restaurant.status === "APPROVED" ? "Đã duyệt" : "Chờ duyệt"}
                            color={restaurant.status === "APPROVED" ? "success" : "warning"}
                          />
                        </Stack>

                        <Stack direction="row" spacing={0.75} alignItems="center">
                          <StarRoundedIcon sx={{ color: "#F59E0B", fontSize: 20 }} />
                          <Typography fontWeight={700}>
                            {Number(restaurant.averageRating || 0) > 0
                              ? `${Number(restaurant.averageRating).toFixed(1)} / 5`
                              : "Không có đánh giá"}
                          </Typography>
                        </Stack>

                        <Stack direction="row" spacing={0.75} alignItems="flex-start">
                          <PlaceRoundedIcon sx={{ color: "text.secondary", fontSize: 20, mt: 0.1 }} />
                          <Typography color="text.secondary" sx={{ lineHeight: 1.5 }}>
                            {restaurant.address || "Chưa cập nhật địa chỉ"}
                          </Typography>
                        </Stack>

                        <Typography color="text.secondary" sx={{ lineHeight: 1.55 }}>
                          {restaurant.description || "Chi nhánh này chưa có mô tả ngắn."}
                        </Typography>
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
            <Stack spacing={1.5}>
              <Typography variant="h4">Thông báo</Typography>

              <Box
                sx={{
                  p: 1.75,
                  borderRadius: 2,
                  bgcolor: "rgba(245,158,11,0.12)",
                  border: "1px solid rgba(245,158,11,0.16)",
                  boxShadow: "inset 0 1px 0 rgba(255,255,255,0.65)",
                }}
              >
                <Stack spacing={0.6}>
                  <Typography fontWeight={700} sx={{ fontSize: "1rem", lineHeight: 1.45 }}>
                    Trà Hương đã đánh giá 5 sao cho món Jolibee
                  </Typography>
                  <Typography color="text.secondary" sx={{ lineHeight: 1.6 }}>
                    "tôi đã ăn món này 1 tuần liên tục"
                  </Typography>
                </Stack>
              </Box>

              <Box
                sx={{
                  p: 1.75,
                  borderRadius: 2,
                  bgcolor: "rgba(47,107,255,0.1)",
                  border: "1px solid rgba(47,107,255,0.14)",
                  boxShadow: "inset 0 1px 0 rgba(255,255,255,0.65)",
                }}
              >
                <Stack spacing={0.6}>
                  <Typography fontWeight={700} sx={{ fontSize: "1rem", lineHeight: 1.45 }}>
                    Minh Anh đã đánh giá 4 sao cho món Gà rán sốt cay
                  </Typography>
                  <Typography color="text.secondary" sx={{ lineHeight: 1.6 }}>
                    "vỏ giòn, sốt ngon nhưng mình muốn phần salad nhiều hơn một chút"
                  </Typography>
                </Stack>
              </Box>

              <CustomButton
                type="button"
                startIcon={<RestaurantMenuRoundedIcon />}
                onClick={(event) => event.preventDefault()}
              >
                Xem thêm
              </CustomButton>
            </Stack>
          </CustomCard>
        </Grid>
      </Grid>
    </Stack>
  );
}

export default OwnerDashboardPage;
