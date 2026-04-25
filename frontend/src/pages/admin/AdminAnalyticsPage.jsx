import InsightsRoundedIcon from "@mui/icons-material/InsightsRounded";
import RestaurantRoundedIcon from "@mui/icons-material/RestaurantRounded";
import StarRoundedIcon from "@mui/icons-material/StarRounded";
import { Grid, Stack, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import CustomCard from "../../components/CustomCard";
import LoadingScreen from "../../components/LoadingScreen";
import SectionHeader from "../../components/SectionHeader";
import { dashboardService } from "../../services/dashboardService";

function AdminAnalyticsPage() {
  const [overview, setOverview] = useState(null);
  const [restaurants, setRestaurants] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      const [overviewData, restaurantData] = await Promise.all([
        dashboardService.getAdminOverview(),
        dashboardService.getAdminRestaurants(),
      ]);
      setOverview(overviewData);
      setRestaurants(restaurantData);
    };
    loadData();
  }, []);

  if (!overview || !restaurants) return <LoadingScreen message="Dang tai du lieu phan tich..." />;

  const topRated = [...restaurants].sort((a, b) => b.rating - a.rating).slice(0, 3);

  return (
    <Stack spacing={3}>
      <SectionHeader
        title="Phan tich he thong"
        description="So sanh tang truong, chat luong va hieu qua van hanh tren toan bo nen tang."
      />

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, lg: 4 }}>
          <CustomCard>
            <Stack spacing={1.5}>
              <InsightsRoundedIcon color="primary" />
              <Typography variant="h4">Ty le duyet</Typography>
              <Typography variant="h2">
                {Math.round((overview.activeRestaurants / overview.totalRestaurants) * 100)}%
              </Typography>
              <Typography color="text.secondary">
                Phan tram nha hang da dat chuan va hien thi cong khai.
              </Typography>
            </Stack>
          </CustomCard>
        </Grid>
        <Grid size={{ xs: 12, lg: 4 }}>
          <CustomCard>
            <Stack spacing={1.5}>
              <RestaurantRoundedIcon color="warning" />
              <Typography variant="h4">Nha hang dang cho duyet</Typography>
              <Typography variant="h2">{overview.pendingRestaurants}</Typography>
              <Typography color="text.secondary">
                Khoi luong cong viec can admin xu ly trong hang doi.
              </Typography>
            </Stack>
          </CustomCard>
        </Grid>
        <Grid size={{ xs: 12, lg: 4 }}>
          <CustomCard>
            <Stack spacing={1.5}>
              <StarRoundedIcon sx={{ color: "#F59E0B" }} />
              <Typography variant="h4">Danh gia trung binh</Typography>
              <Typography variant="h2">{overview.averageRating}</Typography>
              <Typography color="text.secondary">
                Chat luong trai nghiem tong hop dua tren cac danh gia hien co.
              </Typography>
            </Stack>
          </CustomCard>
        </Grid>
      </Grid>

      <CustomCard>
        <Stack spacing={2}>
          <Typography variant="h4">Top nha hang co rating cao</Typography>
          <Grid container spacing={2}>
            {topRated.map((restaurant) => (
              <Grid key={restaurant.id} size={{ xs: 12, md: 4 }}>
                <Stack
                  spacing={1}
                  sx={{
                    p: 2,
                    borderRadius: 2,
                    bgcolor: "rgba(248,250,255,0.92)",
                    border: "1px solid rgba(15,23,42,0.06)",
                  }}
                >
                  <Typography fontWeight={800}>{restaurant.name}</Typography>
                  <Typography color="text.secondary">{restaurant.category}</Typography>
                  <Typography color="text.secondary">{restaurant.address}</Typography>
                  <Typography fontWeight={700}>Rating {restaurant.rating}</Typography>
                </Stack>
              </Grid>
            ))}
          </Grid>
        </Stack>
      </CustomCard>
    </Stack>
  );
}

export default AdminAnalyticsPage;
