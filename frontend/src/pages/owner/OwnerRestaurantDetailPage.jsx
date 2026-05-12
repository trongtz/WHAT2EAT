import ArrowBackRoundedIcon from "@mui/icons-material/ArrowBackRounded";
import LocalPhoneRoundedIcon from "@mui/icons-material/LocalPhoneRounded";
import StarRoundedIcon from "@mui/icons-material/StarRounded";
import TableRestaurantRoundedIcon from "@mui/icons-material/TableRestaurantRounded";
import { Alert, Box, Chip, Grid, Stack, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import { Link as RouterLink, useParams } from "react-router-dom";
import CustomButton from "../../components/CustomButton";
import CustomCard from "../../components/CustomCard";
import LoadingScreen from "../../components/LoadingScreen";
import SectionHeader from "../../components/SectionHeader";
import { restaurantService } from "../../services/restaurantService";
import {
  formatDateTime,
  formatOpenHours,
  getPriceRangeLabel,
  getRestaurantStatusLabel,
  getStatusColor,
} from "../../utils/helpers";

const getCuisineLabels = (value) =>
  String(value || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);

const getRestaurantRatingLabel = (restaurant) =>
  Number(restaurant.reviewCount || 0) > 0
    ? `${Number(restaurant.averageRating || 0).toFixed(1)} sao`
    : "Không có đánh giá";

function MenuImage({ imageUrl, size = 76 }) {
  return (
    <Box
      sx={{
        width: size,
        height: size,
        borderRadius: 2,
        flexShrink: 0,
        border: "1px solid rgba(15,23,42,0.08)",
        background: imageUrl
          ? `linear-gradient(180deg, rgba(18,22,44,0.05), rgba(18,22,44,0.16)), url(${imageUrl})`
          : "linear-gradient(135deg, rgba(255,159,28,0.18), rgba(47,107,255,0.14))",
        backgroundPosition: "center",
        backgroundSize: "cover",
        boxShadow: "inset 0 1px 0 rgba(255,255,255,0.72)",
      }}
    />
  );
}

function DetailMetric({ label, value, icon }) {
  return (
    <Box
      sx={{
        p: 1.6,
        borderRadius: 2,
        bgcolor: "rgba(248,250,255,0.92)",
        border: "1px solid rgba(15,23,42,0.06)",
      }}
    >
      <Typography color="text.secondary" sx={{ fontSize: "0.92rem" }}>
        {label}
      </Typography>
      <Stack direction="row" spacing={0.7} alignItems="center" sx={{ mt: 0.5 }}>
        {icon}
        <Typography fontWeight={800}>{value}</Typography>
      </Stack>
    </Box>
  );
}

function OwnerRestaurantDetailPage() {
  const { id } = useParams();
  const [restaurant, setRestaurant] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      const data = await restaurantService.getManageRestaurant(id);
      setRestaurant(data);
      setLoading(false);
    };

    loadData();
  }, [id]);

  if (loading) return <LoadingScreen message="Đang tải chi tiết chi nhánh..." />;
  if (!restaurant) return <Alert severity="error">Không tìm thấy chi nhánh.</Alert>;

  const cuisineLabels = getCuisineLabels(restaurant.cuisineType);

  return (
    <Stack spacing={3}>
      <SectionHeader
        title={restaurant.name}
        action={
          <CustomButton
            component={RouterLink}
            to="/chu-nha-hang/nha-hang"
            startIcon={<ArrowBackRoundedIcon />}
            sx={{ background: "linear-gradient(135deg, #64748B 0%, #94A3B8 100%)" }}
          >
            Quay lại
          </CustomButton>
        }
      />

      <Alert severity={restaurant.status === "APPROVED" ? "success" : restaurant.status === "REJECTED" ? "error" : "info"}>
        {restaurant.status === "APPROVED"
          ? "Chi nhánh đã được admin duyệt. Bạn có thể sửa thông tin, quản lý menu và theo dõi sức chứa đặt bàn."
          : restaurant.status === "PENDING"
            ? "Chi nhánh đang chờ admin duyệt. Bạn có thể xem chi tiết hồ sơ đã gửi."
            : "Chi nhánh đang ở trạng thái bị từ chối."}
      </Alert>

      <CustomCard>
        <Stack spacing={2.5}>
          <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
            <Box
              sx={{
                width: { xs: "100%", md: 220 },
                height: 170,
                borderRadius: 2,
                flexShrink: 0,
                background: restaurant.image
                  ? `linear-gradient(180deg, rgba(18,22,44,0.08), rgba(18,22,44,0.24)), url(${restaurant.image})`
                  : "linear-gradient(135deg, rgba(255,159,28,0.22), rgba(47,107,255,0.18))",
                backgroundPosition: "center",
                backgroundSize: "cover",
              }}
            />

            <Stack spacing={1.1} flex={1}>
              <Typography variant="h4">{restaurant.name}</Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                {cuisineLabels.length ? (
                  cuisineLabels.map((label) => <Chip key={label} label={label} />)
                ) : (
                  <Chip label="Chưa có loại ẩm thực" />
                )}
                <Chip label={getPriceRangeLabel(restaurant.priceRange)} variant="outlined" />
                <Chip
                  label={getRestaurantStatusLabel(restaurant.status)}
                  color={getStatusColor(restaurant.status)}
                />
                <Chip
                  icon={<StarRoundedIcon sx={{ fontSize: 18 }} />}
                  label={getRestaurantRatingLabel(restaurant)}
                  variant="outlined"
                  color="warning"
                />
              </Stack>
              <Typography color="text.secondary">{restaurant.address}</Typography>
              <Stack direction="row" spacing={0.9} alignItems="center">
                <LocalPhoneRoundedIcon sx={{ color: "text.secondary", fontSize: 18 }} />
                <Typography color="text.secondary">{restaurant.phone || "Chưa cập nhật"}</Typography>
              </Stack>
              <Typography color="text.secondary">
                {restaurant.description || "Chi nhánh chưa có mô tả."}
              </Typography>
            </Stack>
          </Stack>

          <Grid container spacing={1.5}>
            <Grid size={{ xs: 12, sm: 6, lg: 3 }}>
              <DetailMetric label="Cập nhật gần nhất" value={formatDateTime(restaurant.updatedAt)} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6, lg: 3 }}>
              <DetailMetric label="Giờ mở cửa" value={formatOpenHours(restaurant.openHours)} />
            </Grid>
            <Grid size={{ xs: 12, sm: 6, lg: 3 }}>
              <DetailMetric
                label="Chỗ ngồi"
                value={`${restaurant.availableCapacity || 0}/${restaurant.maxCapacity || 0}`}
                icon={<TableRestaurantRoundedIcon sx={{ fontSize: 18 }} />}
              />
            </Grid>
          </Grid>
        </Stack>
      </CustomCard>

      <CustomCard>
        <Stack spacing={2}>
          <Typography variant="h4">Menu hiện tại</Typography>
          {restaurant.menu.length ? (
            <Grid container spacing={2}>
              {restaurant.menu.map((item) => (
                <Grid key={item.id} size={{ xs: 12, md: 6 }}>
                  <Box
                    sx={{
                      p: 2,
                      borderRadius: 2,
                      bgcolor: "rgba(248,250,255,0.92)",
                      border: "1px solid rgba(15,23,42,0.06)",
                    }}
                  >
                    <Stack direction="row" spacing={1.25} alignItems="flex-start">
                      <MenuImage imageUrl={item.imageUrl} />
                      <Stack spacing={0.75}>
                        <Typography fontWeight={800}>{item.name}</Typography>
                        <Typography color="text.secondary">
                          {item.description || "Chưa có mô tả món ăn."}
                        </Typography>
                        <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                          <Chip label={item.category || "Chưa phân loại"} />
                          <Chip
                            label={item.isAvailable ? "Đang phục vụ" : "Tạm ẩn"}
                            color={item.isAvailable ? "success" : "default"}
                          />
                        </Stack>
                      </Stack>
                    </Stack>
                  </Box>
                </Grid>
              ))}
            </Grid>
          ) : (
            <Alert severity="info">Chi nhánh này chưa có món ăn nào được khai báo.</Alert>
          )}
        </Stack>
      </CustomCard>
    </Stack>
  );
}

export default OwnerRestaurantDetailPage;
