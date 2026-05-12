import ArrowBackRoundedIcon from "@mui/icons-material/ArrowBackRounded";
import LocalPhoneRoundedIcon from "@mui/icons-material/LocalPhoneRounded";
import StarRoundedIcon from "@mui/icons-material/StarRounded";
import { Alert, Box, Chip, Grid, Stack, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import { Link as RouterLink, useParams } from "react-router-dom";
import CustomButton from "../../components/CustomButton";
import CustomCard from "../../components/CustomCard";
import LoadingScreen from "../../components/LoadingScreen";
import { restaurantService } from "../../services/restaurantService";
import { formatCurrency, formatOpenHours, getPriceRangeLabel, getRestaurantStatusLabel } from "../../utils/helpers";

function OwnerRestaurantDetailPage() {
  const { restaurantId } = useParams();
  const [restaurant, setRestaurant] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadData = async () => {
      try {
        const data = await restaurantService.getManageRestaurant(restaurantId);
        setRestaurant(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [restaurantId]);

  if (loading) return <LoadingScreen message="Đang tải chi tiết chi nhánh..." />;
  if (error) return <Alert severity="error">{error}</Alert>;
  if (!restaurant) return <Alert severity="error">Không tìm thấy chi nhánh.</Alert>;

  return (
    <Stack spacing={3}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" flexWrap="wrap" useFlexGap>
        <Typography variant="h2">{restaurant.name}</Typography>
        <CustomButton
          component={RouterLink}
          to="/chu-nha-hang/nha-hang"
          startIcon={<ArrowBackRoundedIcon />}
          sx={{ background: "linear-gradient(135deg, #64748B 0%, #94A3B8 100%)" }}
        >
          Quay lại
        </CustomButton>
      </Stack>

      <Alert severity={restaurant.status === "APPROVED" ? "success" : restaurant.status === "REJECTED" ? "error" : "warning"}>
        {restaurant.status === "APPROVED"
          ? "Chi nhánh đã được admin duyệt. Bạn có thể sửa thông tin và quản lý menu."
          : restaurant.status === "REJECTED"
            ? "Chi nhánh đã bị từ chối. Bạn cần tạo hồ sơ mới hoặc liên hệ admin."
            : "Chi nhánh đang chờ admin duyệt trước khi mở quyền cập nhật."}
      </Alert>

      <CustomCard>
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, lg: 4 }}>
            <Box
              sx={{
                height: 240,
                borderRadius: 2.5,
                overflow: "hidden",
                background: restaurant.image
                  ? `linear-gradient(180deg, rgba(18,22,44,0.05), rgba(18,22,44,0.18)), url(${restaurant.image})`
                  : "linear-gradient(135deg, color-mix(in srgb, var(--app-primary) 18%, white), color-mix(in srgb, var(--app-secondary) 16%, white))",
                backgroundSize: "cover",
                backgroundPosition: "center",
              }}
            />
          </Grid>

          <Grid size={{ xs: 12, lg: 8 }}>
            <Stack spacing={1.25}>
              <Typography variant="h3">{restaurant.name}</Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                {restaurant.cuisineType
                  .split(",")
                  .map((item) => item.trim())
                  .filter(Boolean)
                  .map((item) => (
                    <Chip key={item} label={item} />
                  ))}
                <Chip label={getPriceRangeLabel(restaurant.priceRange)} variant="outlined" />
                <Chip
                  label={getRestaurantStatusLabel(restaurant.status)}
                  color={restaurant.status === "APPROVED" ? "success" : restaurant.status === "REJECTED" ? "error" : "warning"}
                />
                <Chip
                  icon={<StarRoundedIcon sx={{ color: "#F6B500 !important" }} />}
                  label={
                    restaurant.averageRating > 0 ? `${restaurant.averageRating.toFixed(1)} sao` : "Không có đánh giá"
                  }
                  sx={{
                    bgcolor: "color-mix(in srgb, var(--app-primary) 10%, white)",
                    color: "var(--app-primary)",
                  }}
                />
              </Stack>

              <Typography color="text.secondary">{restaurant.address}</Typography>
              <Stack direction="row" spacing={1} alignItems="center">
                <LocalPhoneRoundedIcon sx={{ color: "var(--app-secondary)" }} />
                <Typography color="text.secondary">{restaurant.phone}</Typography>
              </Stack>

              <Grid container spacing={2}>
                <Grid size={{ xs: 6, md: 3 }}>
                  <Typography color="text.secondary">Giờ mở cửa</Typography>
                  <Typography fontWeight={800}>{formatOpenHours(restaurant.openHours)}</Typography>
                </Grid>
                <Grid size={{ xs: 6, md: 3 }}>
                  <Typography color="text.secondary">Chỗ ngồi</Typography>
                  <Typography fontWeight={800}>
                    {restaurant.availableCapacity}/{restaurant.maxCapacity}
                  </Typography>
                </Grid>
                <Grid size={{ xs: 6, md: 3 }}>
                  <Typography color="text.secondary">Số món ăn</Typography>
                  <Typography fontWeight={800}>{restaurant.menu.length}</Typography>
                </Grid>
                <Grid size={{ xs: 6, md: 3 }}>
                  <Typography color="text.secondary">Đánh giá</Typography>
                  <Typography fontWeight={800}>
                    {restaurant.averageRating > 0 ? restaurant.averageRating.toFixed(1) : "Không có"}
                  </Typography>
                </Grid>
              </Grid>

              <Typography color="text.secondary">
                {restaurant.description || "Nhà hàng này chưa có mô tả chi tiết."}
              </Typography>
            </Stack>
          </Grid>
        </Grid>
      </CustomCard>

      <CustomCard>
        <Stack spacing={2}>
          <Stack direction="row" justifyContent="space-between" alignItems="center" flexWrap="wrap" useFlexGap>
            <Typography variant="h4">Menu của chi nhánh</Typography>
            {restaurant.status === "APPROVED" ? (
              <CustomButton component={RouterLink} to={`/chu-nha-hang/menu?restaurantId=${restaurant.id}&focus=create`}>
                Thêm món
              </CustomButton>
            ) : null}
          </Stack>

          {restaurant.menu.length ? (
            <Grid container spacing={1.5}>
              {restaurant.menu.map((item) => (
                <Grid key={item.id} size={{ xs: 12, md: 6 }}>
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
                          width: 84,
                          minWidth: 84,
                          height: 84,
                          borderRadius: 1.5,
                          overflow: "hidden",
                          background: item.imageUrl
                            ? `linear-gradient(180deg, rgba(18,22,44,0.04), rgba(18,22,44,0.16)), url(${item.imageUrl})`
                            : "linear-gradient(135deg, color-mix(in srgb, var(--app-primary) 16%, white), color-mix(in srgb, var(--app-secondary) 12%, white))",
                          backgroundSize: "cover",
                          backgroundPosition: "center",
                        }}
                      />
                      <Stack spacing={0.45} sx={{ minWidth: 0, flex: 1 }}>
                        <Typography fontWeight={800}>{item.name}</Typography>
                        <Typography color="text.secondary" sx={{ fontSize: "0.9rem" }}>
                          {item.description || "Chưa có mô tả món ăn."}
                        </Typography>
                        <Stack direction="row" spacing={0.75} flexWrap="wrap" useFlexGap>
                          {item.category ? <Chip size="small" label={item.category} /> : null}
                          <Chip size="small" label={item.isAvailable ? "Đang phục vụ" : "Tạm hết"} />
                        </Stack>
                        <Typography fontWeight={800}>{formatCurrency(item.price)}</Typography>
                      </Stack>
                    </Stack>
                  </Box>
                </Grid>
              ))}
            </Grid>
          ) : (
            <Typography color="text.secondary">Chi nhánh này chưa có món ăn nào.</Typography>
          )}
        </Stack>
      </CustomCard>
    </Stack>
  );
}

export default OwnerRestaurantDetailPage;
