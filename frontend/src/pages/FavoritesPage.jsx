import FavoriteRoundedIcon from "@mui/icons-material/FavoriteRounded";
import { Alert, Grid, Stack } from "@mui/material";
import { useEffect, useState } from "react";
import { Link as RouterLink } from "react-router-dom";
import CustomButton from "../components/CustomButton";
import EmptyState from "../components/EmptyState";
import LoadingScreen from "../components/LoadingScreen";
import RestaurantCard from "../components/RestaurantCard";
import SectionHeader from "../components/SectionHeader";
import { useAuth } from "../hooks/useAuth";
import { favoriteService } from "../services/favoriteService";
import { restaurantService } from "../services/restaurantService";
import { getGuestFavoriteIds, toggleGuestFavorite } from "../utils/guestSession";

function FavoritesPage() {
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadFavorites = async () => {
      try {
        if (!user) {
          setItems([]);
          return;
        }

        if (user.isGuest) {
          const [favoriteIds, restaurants] = await Promise.all([
            Promise.resolve(getGuestFavoriteIds().map(String)),
            restaurantService.getRestaurants(),
          ]);
          setItems(restaurants.filter((restaurant) => favoriteIds.includes(String(restaurant.id))));
          return;
        }

        if (user.role !== "customer") {
          setItems([]);
          return;
        }

        const data = await favoriteService.getFavoriteRestaurants();
        setItems(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    loadFavorites();
  }, [user]);

  const handleToggleFavorite = async (restaurant) => {
    try {
      if (!user) return;

      if (user.isGuest) {
        toggleGuestFavorite(restaurant.id);
        setItems((currentValue) => currentValue.filter((item) => String(item.id) !== String(restaurant.id)));
        return;
      }

      if (user.role !== "customer") {
        return;
      }

      await favoriteService.toggle(restaurant.id);
      setItems((currentValue) => currentValue.filter((item) => String(item.id) !== String(restaurant.id)));
    } catch (err) {
      setError(err.message);
    }
  };

  if (!user) return <Alert severity="info">Vui lòng đăng nhập để xem danh sách yêu thích của bạn.</Alert>;
  if (loading) return <LoadingScreen message="Đang tải danh sách yêu thích..." />;

  return (
    <Stack spacing={3}>
      <SectionHeader title="Danh sách yêu thích" description="Những nơi bạn đã lưu để quay lại sau." />
      {error ? <Alert severity="error">{error}</Alert> : null}

      {items.length ? (
        <Grid container spacing={3}>
          {items.map((restaurant) => (
            <Grid key={restaurant.id} size={{ xs: 12, md: 6 }}>
              <RestaurantCard
                compact
                restaurant={restaurant}
                isFavorite
                onToggleFavorite={handleToggleFavorite}
                action={
                  <CustomButton component={RouterLink} to={`/nha-hang/${restaurant.id}`} startIcon={<FavoriteRoundedIcon />}>
                    Xem lại
                  </CustomButton>
                }
              />
            </Grid>
          ))}
        </Grid>
      ) : (
        <EmptyState
          title="Chưa có nhà hàng yêu thích"
          description="Bạn có thể lưu từ trang chi tiết nhà hàng để xem lại nhanh hơn."
        />
      )}
    </Stack>
  );
}

export default FavoritesPage;
