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

function FavoritesPage() {
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadFavorites = async () => {
      if (!user) {
        setLoading(false);
        return;
      }
      const data = await favoriteService.getFavorites(user.id);
      setItems(data);
      setLoading(false);
    };
    loadFavorites();
  }, [user]);

  if (!user) return <Alert severity="info">Vui lòng đăng nhập để xem danh sách yêu thích của bạn.</Alert>;
  if (loading) return <LoadingScreen message="Đang tải danh sách yêu thích..." />;

  return (
    <Stack spacing={3}>
      <SectionHeader title="Danh sách yêu thích" description="Những nơi bạn đã lưu để quay lại sau." />
      {items.length ? (
        <Grid container spacing={3}>
          {items.map((restaurant) => (
            <Grid key={restaurant.id} size={{ xs: 12, md: 6 }}>
              <RestaurantCard
                compact
                restaurant={restaurant}
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
        <EmptyState title="Chưa có nhà hàng yêu thích" description="Bạn có thể lưu từ trang chi tiết nhà hàng để xem lại nhanh hơn." />
      )}
    </Stack>
  );
}

export default FavoritesPage;
