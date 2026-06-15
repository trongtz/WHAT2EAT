import FilterAltRoundedIcon from "@mui/icons-material/FilterAltRounded";
import SearchRoundedIcon from "@mui/icons-material/SearchRounded";
import { Alert, Grid, InputAdornment, MenuItem, Stack } from "@mui/material";
import { useEffect, useState } from "react";
import { Link as RouterLink, useSearchParams } from "react-router-dom";
import CustomButton from "../components/CustomButton";
import EmptyState from "../components/EmptyState";
import FormInput from "../components/FormInput";
import LoadingScreen from "../components/LoadingScreen";
import RestaurantCard from "../components/RestaurantCard";
import SectionHeader from "../components/SectionHeader";
import { useAuth } from "../hooks/useAuth";
import { favoriteService } from "../services/favoriteService";
import { restaurantService } from "../services/restaurantService";
import { getGuestFavoriteIds, toggleGuestFavorite } from "../utils/guestSession";

function SearchPage() {
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [filters, setFilters] = useState({
    keyword: searchParams.get("keyword") || "",
    category: searchParams.get("category") || "",
    price: searchParams.get("price") || "",
  });
  const [restaurants, setRestaurants] = useState([]);
  const [favoriteIds, setFavoriteIds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadFavorites = async () => {
    if (!user) {
      setFavoriteIds([]);
      return;
    }

    if (user.isGuest) {
      setFavoriteIds(getGuestFavoriteIds().map(String));
      return;
    }

    if (user.role !== "customer") {
      setFavoriteIds([]);
      return;
    }

    const ids = await favoriteService.getFavoriteRestaurantIds();
    setFavoriteIds(ids.map(String));
  };

  const loadRestaurants = async (currentFilters = filters) => {
    setLoading(true);
    setError("");
    try {
      const data = await restaurantService.getRestaurants(currentFilters);
      setRestaurants(data);
      setSearchParams(currentFilters);

      try {
        await loadFavorites();
      } catch (favoriteError) {
        // Favorites only enhance the UI; don't block search results if auth is stale.
        setFavoriteIds([]);
        if (!favoriteError.message?.toLowerCase?.().includes("token")) {
          setError(favoriteError.message);
        }
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRestaurants();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.id, user?.isGuest, user?.role]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFilters((prev) => ({ ...prev, [name]: value }));
  };

  const handleToggleFavorite = async (restaurant) => {
    try {
      if (!user) {
        setError("Vui lòng đăng nhập để lưu yêu thích.");
        return;
      }

      if (user.isGuest) {
        setFavoriteIds(toggleGuestFavorite(restaurant.id).map(String));
        return;
      }

      if (user.role !== "customer") {
        return;
      }

      const result = await favoriteService.toggle(restaurant.id);
      setFavoriteIds((currentValue) => {
        const currentIds = currentValue.map(String);
        if (result.isFavorite) {
          return currentIds.includes(String(restaurant.id)) ? currentIds : [...currentIds, String(restaurant.id)];
        }
        return currentIds.filter((item) => item !== String(restaurant.id));
      });
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) return <LoadingScreen message="Đang lọc nhà hàng phù hợp..." />;

  return (
    <Stack spacing={3}>
      <SectionHeader
        title="Tìm kiếm và bộ lọc"
        description="Lọc theo từ khóa, loại món và mức ngân sách để ra kết quả sát nhu cầu hơn."
      />

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, md: 5 }}>
          <FormInput
            label="Tìm món hoặc nhà hàng"
            name="keyword"
            value={filters.keyword}
            onChange={handleChange}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchRoundedIcon />
                </InputAdornment>
              ),
            }}
          />
        </Grid>
        <Grid size={{ xs: 12, md: 3 }}>
          <FormInput select label="Danh mục" name="category" value={filters.category} onChange={handleChange}>
            <MenuItem value="">Tất cả</MenuItem>
            <MenuItem value="Lẩu">Lẩu</MenuItem>
            <MenuItem value="Nhật Bản">Nhật Bản</MenuItem>
            <MenuItem value="Nướng">Nướng</MenuItem>
            <MenuItem value="Đồ uống">Đồ uống</MenuItem>
          </FormInput>
        </Grid>
        <Grid size={{ xs: 12, md: 2 }}>
          <FormInput select label="Ngân sách" name="price" value={filters.price} onChange={handleChange}>
            <MenuItem value="">Không giới hạn</MenuItem>
            <MenuItem value="cheap">Dưới 100.000đ</MenuItem>
            <MenuItem value="mid">100.000đ - 300.000đ</MenuItem>
            <MenuItem value="expensive">Trên 300.000đ</MenuItem>
          </FormInput>
        </Grid>
        <Grid size={{ xs: 12, md: 2 }}>
          <CustomButton onClick={() => loadRestaurants()} fullWidth startIcon={<FilterAltRoundedIcon />}>
            Áp dụng
          </CustomButton>
        </Grid>
      </Grid>

      {error ? <Alert severity="error">{error}</Alert> : null}

      {restaurants.length ? (
        <Grid container spacing={3}>
          {restaurants.map((restaurant) => (
            <Grid key={restaurant.id} size={{ xs: 12, md: 6 }}>
              <RestaurantCard
                compact
                restaurant={restaurant}
                isFavorite={favoriteIds.includes(String(restaurant.id))}
                onToggleFavorite={handleToggleFavorite}
                hideTopLabel
                action={
                  <CustomButton component={RouterLink} to={`/nha-hang/${restaurant.id}`}>
                    Xem ngay
                  </CustomButton>
                }
              />
            </Grid>
          ))}
        </Grid>
      ) : (
        <EmptyState
          title="Chưa có kết quả phù hợp"
          description="Bạn thử nới rộng khoảng giá hoặc đổi từ khóa tìm kiếm nhé."
        />
      )}
    </Stack>
  );
}

export default SearchPage;
