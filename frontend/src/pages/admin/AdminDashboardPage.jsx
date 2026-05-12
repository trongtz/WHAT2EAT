import { Alert, Box, Grid, Stack, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import CustomCard from "../../components/CustomCard";
import LoadingScreen from "../../components/LoadingScreen";
import StatsCard from "../../components/StatsCard";
import { dashboardService } from "../../services/dashboardService";

function AdminDashboardPage() {
  const [overview, setOverview] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadData = async () => {
      try {
        const data = await dashboardService.getAdminOverview();
        setOverview(data);
      } catch (err) {
        setError(err.message);
      }
    };
    loadData();
  }, []);

  if (!overview) return <LoadingScreen message="Đang tải tổng quan..." />;

  return (
    <Stack spacing={3}>
      <Typography variant="h2">Tổng quan</Typography>
      {error ? <Alert severity="error">{error}</Alert> : null}

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 3 }}>
          <StatsCard label="Tổng nhà hàng" value={overview.totalRestaurants} color="rgba(17,24,39,0.14)" />
        </Grid>
        <Grid size={{ xs: 12, md: 3 }}>
          <StatsCard label="Chờ duyệt" value={overview.pendingRestaurants} color="rgba(245,158,11,0.22)" />
        </Grid>
        <Grid size={{ xs: 12, md: 3 }}>
          <StatsCard label="Đã duyệt" value={overview.activeRestaurants} color="rgba(32,180,134,0.18)" />
        </Grid>
        <Grid size={{ xs: 12, md: 3 }}>
          <StatsCard label="Chủ nhà hàng" value={overview.totalOwners} color="rgba(47,107,255,0.18)" />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, lg: 7 }}>
          <CustomCard>
            <Stack spacing={2}>
              <Typography variant="h4">Cần xử lý hôm nay</Typography>
              <Box sx={{ p: 2, borderRadius: 2, bgcolor: "rgba(245,158,11,0.12)" }}>
                <Typography fontWeight={700}>{overview.pendingRestaurants} chi nhánh đang chờ duyệt</Typography>
                <Typography color="text.secondary">
                  Tập trung kiểm tra thông tin hồ sơ và tình trạng dữ liệu nhà hàng trước khi mở quyền quản lý cho owner.
                </Typography>
              </Box>
            </Stack>
          </CustomCard>
        </Grid>

        <Grid size={{ xs: 12, lg: 5 }}>
          <CustomCard>
            <Stack spacing={1.2}>
              <Typography variant="h4">Chỉ số hệ thống</Typography>
              <Typography color="text.secondary">Tổng người dùng: {overview.totalUsers}</Typography>
              <Typography color="text.secondary">Khách hàng: {overview.totalCustomers}</Typography>
              <Typography color="text.secondary">Lượt đặt bàn: {overview.totalBookings}</Typography>
              <Typography color="text.secondary">Đánh giá trung bình: {overview.averageRating}</Typography>
            </Stack>
          </CustomCard>
        </Grid>
      </Grid>
    </Stack>
  );
}

export default AdminDashboardPage;
