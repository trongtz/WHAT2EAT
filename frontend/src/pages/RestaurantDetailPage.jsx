import AccessTimeRoundedIcon from "@mui/icons-material/AccessTimeRounded";
import FavoriteRoundedIcon from "@mui/icons-material/FavoriteRounded";
import LocationOnRoundedIcon from "@mui/icons-material/LocationOnRounded";
import StarRoundedIcon from "@mui/icons-material/StarRounded";
import { Alert, Box, Chip, Divider, Grid, Stack, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import { Link as RouterLink, useParams } from "react-router-dom";
import CustomButton from "../components/CustomButton";
import CustomCard from "../components/CustomCard";
import LoadingScreen from "../components/LoadingScreen";
import SectionHeader from "../components/SectionHeader";
import { useAuth } from "../hooks/useAuth";
import { favoriteService } from "../services/favoriteService";
import { restaurantService } from "../services/restaurantService";
import { formatCurrency, formatDate } from "../utils/helpers";

function RestaurantDetailPage() {
  const { id } = useParams();
  const { user } = useAuth();
  const [restaurant, setRestaurant] = useState(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");

  useEffect(() => {
    const fetchRestaurant = async () => {
      try {
        const data = await restaurantService.getRestaurantDetail(id);
        setRestaurant(data);
      } finally {
        setLoading(false);
      }
    };
    fetchRestaurant();
  }, [id]);

  const handleFavorite = async () => {
    if (!user) {
      setMessage("Vui lòng đăng nhập để lưu yêu thích.");
      return;
    }
    await favoriteService.toggle({ userId: user.id, restaurantId: Number(id) });
    setMessage("Đã cập nhật danh sách yêu thích.");
  };

  if (loading) return <LoadingScreen message="Đang tải chi tiết nhà hàng..." />;
  if (!restaurant) return <Alert severity="error">Không tìm thấy nhà hàng.</Alert>;

  return (
    <Stack spacing={4}>
      <Box
        sx={{
          borderRadius: 2,
          minHeight: 340,
          backgroundImage: `linear-gradient(180deg, rgba(18,22,44,0.08), rgba(18,22,44,0.42)), url(${restaurant.image})`,
          backgroundPosition: "center",
          backgroundSize: "cover",
          display: "flex",
          alignItems: "end",
          p: { xs: 3, md: 5 },
        }}
      >
        <Stack spacing={1.5}>
          <Chip label={restaurant.category} color="secondary" sx={{ alignSelf: "flex-start", fontWeight: 700 }} />
          <Typography variant="h1" color="white">
            {restaurant.name}
          </Typography>
          <Stack direction="row" spacing={2} flexWrap="wrap" useFlexGap>
            <Chip icon={<StarRoundedIcon />} label={`${restaurant.rating} • ${restaurant.reviews} đánh giá`} />
            <Chip icon={<LocationOnRoundedIcon />} label={restaurant.distance} />
            <Chip icon={<AccessTimeRoundedIcon />} label={restaurant.status} />
          </Stack>
        </Stack>
      </Box>

      <SectionHeader title="Thông tin chi tiết" description={restaurant.description} />

      {message ? <Alert severity="success">{message}</Alert> : null}

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 8 }}>
          <CustomCard>
            <Stack spacing={2.5}>
              <Typography variant="h4">Giới thiệu</Typography>
              <Typography color="text.secondary">{restaurant.description}</Typography>
              <Typography color="text.secondary">
                <LocationOnRoundedIcon sx={{ verticalAlign: "middle", mr: 1 }} />
                {restaurant.address}
              </Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                {restaurant.tags.map((tag) => (
                  <Chip key={tag} label={tag} color="primary" variant="outlined" />
                ))}
              </Stack>
              <Divider />
              <Typography variant="h4">Menu nổi bật</Typography>
              <Stack spacing={1.25}>
                {restaurant.menu.map((item) => (
                  <Stack key={item.id} direction="row" justifyContent="space-between">
                    <Typography>{item.name}</Typography>
                    <Typography fontWeight={700}>{formatCurrency(item.price)}</Typography>
                  </Stack>
                ))}
              </Stack>
            </Stack>
          </CustomCard>
        </Grid>

        <Grid size={{ xs: 12, md: 4 }}>
          <Stack spacing={3}>
            <CustomCard>
              <Stack spacing={2}>
                <Typography variant="h4">Thao tác nhanh</Typography>
                <Typography color="text.secondary">Khoảng giá: {restaurant.priceRange}</Typography>
                <CustomButton component={RouterLink} to={`/dat-ban?nhaHang=${restaurant.id}`}>
                  Đặt bàn ngay
                </CustomButton>
                <CustomButton
                  onClick={handleFavorite}
                  startIcon={<FavoriteRoundedIcon />}
                  sx={{ background: "linear-gradient(135deg, #FF7A90 0%, #FF9C8A 100%)", boxShadow: "0 14px 28px rgba(232,93,117,0.22)" }}
                >
                  Lưu yêu thích
                </CustomButton>
              </Stack>
            </CustomCard>

            <CustomCard>
              <Stack spacing={2}>
                <Typography variant="h4">Đánh giá gần đây</Typography>
                {restaurant.reviewsList.map((review) => (
                  <Box key={review.id}>
                    <Typography fontWeight={700}>{review.userName}</Typography>
                    <Typography color="text.secondary">{review.comment}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      {formatDate(review.createdAt)}
                    </Typography>
                  </Box>
                ))}
              </Stack>
            </CustomCard>
          </Stack>
        </Grid>
      </Grid>
    </Stack>
  );
}

export default RestaurantDetailPage;
