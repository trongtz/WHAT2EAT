import AccessTimeRoundedIcon from "@mui/icons-material/AccessTimeRounded";
import FavoriteBorderRoundedIcon from "@mui/icons-material/FavoriteBorderRounded";
import FavoriteRoundedIcon from "@mui/icons-material/FavoriteRounded";
import LocalPhoneRoundedIcon from "@mui/icons-material/LocalPhoneRounded";
import LocationOnRoundedIcon from "@mui/icons-material/LocationOnRounded";
import RestaurantRoundedIcon from "@mui/icons-material/RestaurantRounded";
import StarRoundedIcon from "@mui/icons-material/StarRounded";
import { Alert, Box, Chip, Divider, Grid, Stack, Typography } from "@mui/material";
import { useEffect, useMemo, useState } from "react";
import { Link as RouterLink, useParams } from "react-router-dom";
import CustomButton from "../components/CustomButton";
import CustomCard from "../components/CustomCard";
import LoadingScreen from "../components/LoadingScreen";
import SectionHeader from "../components/SectionHeader";
import { useAuth } from "../hooks/useAuth";
import { favoriteService } from "../services/favoriteService";
import { restaurantService } from "../services/restaurantService";
import { getGuestFavoriteIds, getGuestReviewsByRestaurant, toggleGuestFavorite } from "../utils/guestSession";
import { formatCurrency, formatDate, formatOpenHours, formatPriceRangeDisplay, getTableAvailabilityLabel } from "../utils/helpers";

const buildFallbackImage = () =>
  "linear-gradient(135deg, color-mix(in srgb, var(--app-primary) 18%, white), color-mix(in srgb, var(--app-secondary) 14%, white))";

function RestaurantDetailPage() {
  const { id } = useParams();
  const { user } = useAuth();
  const [restaurant, setRestaurant] = useState(null);
  const [isFavorite, setIsFavorite] = useState(false);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");

  useEffect(() => {
    const fetchRestaurant = async () => {
      try {
        const data = await restaurantService.getRestaurantDetail(id);
        const guestReviews = user?.isGuest ? getGuestReviewsByRestaurant(id) : [];
        const mergedReviews = [...guestReviews, ...(data.reviewsList || [])].sort(
          (firstReview, secondReview) =>
            new Date(secondReview.createdAt || 0).getTime() - new Date(firstReview.createdAt || 0).getTime()
        );
        const mergedRatings = mergedReviews
          .map((review) => Number(review.rating || 0))
          .filter((rating) => Number.isFinite(rating) && rating > 0);

        setRestaurant({
          ...data,
          reviewsList: mergedReviews,
          reviewCount: mergedReviews.length,
          reviews: mergedReviews.length,
          averageRating: mergedRatings.length
            ? mergedRatings.reduce((sum, rating) => sum + rating, 0) / mergedRatings.length
            : Number(data.averageRating || data.rating || 0),
        });
      } finally {
        setLoading(false);
      }
    };

    fetchRestaurant();
  }, [id, user?.isGuest]);

  useEffect(() => {
    const loadFavoriteState = async () => {
      if (!user) {
        setIsFavorite(false);
        return;
      }

      if (user.isGuest) {
        setIsFavorite(getGuestFavoriteIds().map(String).includes(String(id)));
        return;
      }

      if (user.role !== "customer") {
        setIsFavorite(false);
        return;
      }

      const state = await favoriteService.isFavorite(id);
      setIsFavorite(state);
    };

    loadFavoriteState();
  }, [id, user]);

  const handleFavorite = async () => {
    if (!user) {
      setMessage("Vui lòng đăng nhập để lưu yêu thích.");
      return;
    }

    if (user.isGuest) {
      const nextValue = toggleGuestFavorite(id).map(String).includes(String(id));
      setIsFavorite(nextValue);
      setMessage(nextValue ? "Đã thêm vào danh sách yêu thích." : "Đã bỏ khỏi danh sách yêu thích.");
      return;
    }

    if (user.role !== "customer") {
      return;
    }

    const result = await favoriteService.toggle(id);
    setIsFavorite(result.isFavorite);
    setMessage(result.isFavorite ? "Đã thêm vào danh sách yêu thích." : "Đã bỏ khỏi danh sách yêu thích.");
  };

  const ratingText = useMemo(() => {
    if (!restaurant) return "--";
    return Number(restaurant.averageRating || 0) > 0
      ? `${Number(restaurant.averageRating || 0).toFixed(1)} sao`
      : "Chưa có đánh giá";
  }, [restaurant]);

  if (loading) return <LoadingScreen message="Đang tải chi tiết nhà hàng..." />;
  if (!restaurant) return <Alert severity="error">Không tìm thấy nhà hàng.</Alert>;

  return (
    <Stack spacing={4}>
      <Box
        sx={{
          borderRadius: 2.5,
          minHeight: 340,
          backgroundImage: restaurant.image
            ? `linear-gradient(180deg, rgba(18,22,44,0.10), rgba(18,22,44,0.48)), url(${restaurant.image})`
            : buildFallbackImage(),
          backgroundPosition: "center",
          backgroundSize: "cover",
          display: "flex",
          alignItems: "end",
          p: { xs: 3, md: 5 },
        }}
      >
        <Stack spacing={1.5}>
          <Stack direction={{ xs: "column", sm: "row" }} spacing={1} useFlexGap flexWrap="wrap">
            {restaurant.category ? (
              <Chip
                label={restaurant.category}
                sx={{
                  alignSelf: "flex-start",
                  fontWeight: 700,
                  bgcolor: "rgba(255,255,255,0.88)",
                  color: "var(--app-primary)",
                }}
              />
            ) : null}
            <Chip
              icon={<StarRoundedIcon sx={{ color: "#F6B500 !important" }} />}
              label={`${ratingText} • ${restaurant.reviewCount || 0} đánh giá`}
              sx={{ bgcolor: "rgba(255,255,255,0.88)", color: "text.primary" }}
            />
          </Stack>

          <Typography variant="h1" color="white">
            {restaurant.name}
          </Typography>

          <Stack direction={{ xs: "column", sm: "row" }} spacing={2} flexWrap="wrap" useFlexGap>
            <Chip
              icon={<LocationOnRoundedIcon />}
              label={restaurant.address || "Chưa cập nhật địa chỉ"}
              sx={{ bgcolor: "rgba(255,255,255,0.18)", color: "white" }}
            />
            <Chip
              icon={<AccessTimeRoundedIcon />}
              label={formatOpenHours(restaurant.openHours)}
              sx={{ bgcolor: "rgba(255,255,255,0.18)", color: "white" }}
            />
            <Chip
              label={`Bàn trống: ${getTableAvailabilityLabel(restaurant.availableCapacity, restaurant.maxCapacity)}`}
              sx={{ bgcolor: "rgba(255,255,255,0.18)", color: "white" }}
            />
          </Stack>
        </Stack>
      </Box>

      <SectionHeader title="Thông tin chi tiết" description={restaurant.description || undefined} />

      {message ? <Alert severity="success">{message}</Alert> : null}

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 8 }}>
          <CustomCard>
            <Stack spacing={2.5}>
              <Typography variant="h4">Giới thiệu</Typography>
              <Typography color="text.secondary">
                {restaurant.description || "Nhà hàng này chưa có mô tả chi tiết."}
              </Typography>

              <Stack spacing={1.1}>
                <Stack direction="row" spacing={1} alignItems="center">
                  <LocationOnRoundedIcon sx={{ color: "var(--app-secondary)" }} />
                  <Typography color="text.secondary">{restaurant.address || "Chưa cập nhật địa chỉ"}</Typography>
                </Stack>
                <Stack direction="row" spacing={1} alignItems="center">
                  <LocalPhoneRoundedIcon sx={{ color: "var(--app-secondary)" }} />
                  <Typography color="text.secondary">{restaurant.phone || "Chưa cập nhật số điện thoại"}</Typography>
                </Stack>
                <Stack direction="row" spacing={1} alignItems="center">
                  <AccessTimeRoundedIcon sx={{ color: "var(--app-secondary)" }} />
                  <Typography color="text.secondary">{formatOpenHours(restaurant.openHours)}</Typography>
                </Stack>
                <Typography color="text.secondary">
                  Bàn trống: {getTableAvailabilityLabel(restaurant.availableCapacity, restaurant.maxCapacity)}
                </Typography>
              </Stack>

              {restaurant.tags?.length ? (
                <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                  {restaurant.tags.map((tag) => (
                    <Chip key={tag} label={tag} color="primary" variant="outlined" />
                  ))}
                </Stack>
              ) : null}

              <Divider />

              <Stack spacing={1.5}>
                <Typography variant="h4">Menu của nhà hàng</Typography>
                {restaurant.menu.length ? (
                  <Grid container spacing={1.5}>
                    {restaurant.menu.map((item) => (
                      <Grid key={item.id} size={{ xs: 12, sm: 6 }}>
                        <Box
                          sx={{
                            height: "100%",
                            p: 1.35,
                            borderRadius: 2,
                            border: "1px solid rgba(15,23,42,0.08)",
                            bgcolor: "rgba(255,255,255,0.72)",
                          }}
                        >
                          <Stack direction="row" spacing={1.2} alignItems="stretch">
                            <Box
                              sx={{
                                width: 96,
                                minWidth: 96,
                                height: 96,
                                borderRadius: 1.75,
                                overflow: "hidden",
                                background: item.imageUrl
                                  ? `linear-gradient(180deg, rgba(18,22,44,0.05), rgba(18,22,44,0.18)), url(${item.imageUrl})`
                                  : buildFallbackImage(),
                                backgroundSize: "cover",
                                backgroundPosition: "center",
                              }}
                            />

                            <Stack spacing={0.65} sx={{ minWidth: 0, flex: 1 }}>
                              <Typography sx={{ fontWeight: 800, lineHeight: 1.25 }}>{item.name}</Typography>
                              <Typography
                                color="text.secondary"
                                sx={{
                                  fontSize: "0.9rem",
                                  display: "-webkit-box",
                                  WebkitLineClamp: 3,
                                  WebkitBoxOrient: "vertical",
                                  overflow: "hidden",
                                }}
                              >
                                {item.description || "Chưa có mô tả món ăn."}
                              </Typography>

                              <Stack direction="row" spacing={0.75} flexWrap="wrap" useFlexGap>
                                {item.category ? (
                                  <Chip
                                    size="small"
                                    label={item.category}
                                    sx={{
                                      bgcolor: "rgba(15,23,42,0.06)",
                                      color: "text.primary",
                                    }}
                                  />
                                ) : null}
                                <Chip
                                  size="small"
                                  label={item.isAvailable ? "Đang phục vụ" : "Tạm hết"}
                                  sx={{
                                    bgcolor: item.isAvailable
                                      ? "color-mix(in srgb, var(--app-primary) 12%, white)"
                                      : "rgba(15,23,42,0.08)",
                                    color: item.isAvailable ? "var(--app-primary)" : "text.secondary",
                                  }}
                                />
                              </Stack>

                              <Typography fontWeight={800} color="primary.main">
                                {formatCurrency(item.price)}
                              </Typography>
                            </Stack>
                          </Stack>
                        </Box>
                      </Grid>
                    ))}
                  </Grid>
                ) : (
                  <Typography color="text.secondary">Nhà hàng này chưa có món ăn được khai báo.</Typography>
                )}
              </Stack>
            </Stack>
          </CustomCard>
        </Grid>

        <Grid size={{ xs: 12, md: 4 }}>
          <Stack spacing={3}>
            <CustomCard>
              <Stack spacing={2}>
                <Typography variant="h4">Thao tác nhanh</Typography>
                <Typography color="text.secondary">Khoảng giá: {formatPriceRangeDisplay(restaurant.priceRange)}</Typography>
                <Typography color="text.secondary">
                  Bàn trống: {getTableAvailabilityLabel(restaurant.availableCapacity, restaurant.maxCapacity)}
                </Typography>
                <Typography color="text.secondary">Số món hiện có: {restaurant.menu.length}</Typography>
                <CustomButton component={RouterLink} to={`/dat-ban?nhaHang=${restaurant.id}`}>
                  Đặt bàn ngay
                </CustomButton>
                <CustomButton
                  onClick={handleFavorite}
                  startIcon={isFavorite ? <FavoriteRoundedIcon /> : <FavoriteBorderRoundedIcon />}
                  sx={{
                    background: isFavorite
                      ? "linear-gradient(135deg, #E85D75 0%, #FF9C8A 100%)"
                      : "linear-gradient(135deg, #FF7A90 0%, #FF9C8A 100%)",
                    boxShadow: "0 14px 28px rgba(232,93,117,0.22)",
                  }}
                >
                  {isFavorite ? "Đã yêu thích" : "Lưu yêu thích"}
                </CustomButton>
              </Stack>
            </CustomCard>

            <CustomCard>
              <Stack spacing={2}>
                <Typography variant="h4">Đánh giá gần đây</Typography>
                {restaurant.reviewsList.length ? (
                  restaurant.reviewsList.slice(0, 4).map((review) => (
                    <Box key={review.id}>
                      <Stack direction="row" spacing={1} alignItems="center" mb={0.35}>
                        <Typography fontWeight={700}>{review.userName || "Khách hàng"}</Typography>
                        <Chip
                          size="small"
                          icon={<StarRoundedIcon sx={{ color: "#F6B500 !important" }} />}
                          label={Number(review.rating || 0) > 0 ? Number(review.rating || 0).toFixed(1) : "--"}
                          sx={{
                            bgcolor: "color-mix(in srgb, var(--app-primary) 10%, white)",
                            color: "var(--app-primary)",
                          }}
                        />
                      </Stack>
                      <Typography color="text.secondary">{review.comment || "Không có nội dung đánh giá."}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        {formatDate(review.createdAt)}
                      </Typography>
                    </Box>
                  ))
                ) : (
                  <Typography color="text.secondary">Nhà hàng này chưa có đánh giá nào.</Typography>
                )}
              </Stack>
            </CustomCard>

            <CustomCard>
              <Stack spacing={1.5}>
                <Typography variant="h4">Tóm tắt nhanh</Typography>
                <Stack direction="row" spacing={1} alignItems="center">
                  <RestaurantRoundedIcon sx={{ color: "var(--app-secondary)" }} />
                  <Typography color="text.secondary">
                    {restaurant.category || "Nhà hàng"} • {restaurant.menu.length} món
                  </Typography>
                </Stack>
                <Stack direction="row" spacing={1} alignItems="center">
                  <StarRoundedIcon sx={{ color: "#F6B500" }} />
                  <Typography color="text.secondary">
                    {ratingText} • {restaurant.reviewCount || 0} đánh giá
                  </Typography>
                </Stack>
              </Stack>
            </CustomCard>
          </Stack>
        </Grid>
      </Grid>
    </Stack>
  );
}

export default RestaurantDetailPage;
