import AdminPanelSettingsRoundedIcon from "@mui/icons-material/AdminPanelSettingsRounded";
import ApartmentRoundedIcon from "@mui/icons-material/ApartmentRounded";
import PeopleRoundedIcon from "@mui/icons-material/PeopleRounded";
import ReceiptLongRoundedIcon from "@mui/icons-material/ReceiptLongRounded";
import { Box, Grid, Stack, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import CustomCard from "../../components/CustomCard";
import LoadingScreen from "../../components/LoadingScreen";
import SectionHeader from "../../components/SectionHeader";
import StatsCard from "../../components/StatsCard";
import { dashboardService } from "../../services/dashboardService";

function AdminDashboardPage() {
  const [overview, setOverview] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      const data = await dashboardService.getAdminOverview();
      setOverview(data);
    };
    loadData();
  }, []);

  if (!overview) return <LoadingScreen message="Dang tai tong quan he thong..." />;

  return (
    <Stack spacing={3}>
      <SectionHeader
        eyebrow="Admin workspace"
        title="Tong quan he thong"
        description="So lieu tong hop de admin nhan biet tang truong, rui ro va cac muc can kiem soat ngay."
      />

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 3 }}>
          <StatsCard label="Tong nguoi dung" value={overview.totalUsers} color="rgba(47,107,255,0.18)" />
        </Grid>
        <Grid size={{ xs: 12, md: 3 }}>
          <StatsCard label="Tong nha hang" value={overview.totalRestaurants} color="rgba(17,24,39,0.14)" />
        </Grid>
        <Grid size={{ xs: 12, md: 3 }}>
          <StatsCard label="Cho duyet" value={overview.pendingRestaurants} color="rgba(245,158,11,0.22)" />
        </Grid>
        <Grid size={{ xs: 12, md: 3 }}>
          <StatsCard label="Tong dat ban" value={overview.totalBookings} color="rgba(232,93,117,0.18)" />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {[
          {
            icon: <PeopleRoundedIcon color="primary" />,
            title: "Tai khoan dang hoat dong",
            value: overview.totalCustomers,
            text: "Nguoi dung khach hang dang su dung nen tang.",
          },
          {
            icon: <ApartmentRoundedIcon color="warning" />,
            title: "Chu nha hang",
            value: overview.totalOwners,
            text: "So tai khoan doi tac dang tham gia he thong.",
          },
          {
            icon: <AdminPanelSettingsRoundedIcon color="success" />,
            title: "Co so da duyet",
            value: overview.activeRestaurants,
            text: "Nha hang da dat dieu kien hien thi cong khai.",
          },
          {
            icon: <ReceiptLongRoundedIcon color="error" />,
            title: "Danh gia trung binh",
            value: overview.averageRating,
            text: "Chat luong dich vu tong hop tren toan he thong.",
          },
        ].map((item) => (
          <Grid key={item.title} size={{ xs: 12, md: 6, xl: 3 }}>
            <CustomCard>
              <Stack spacing={1.2}>
                {item.icon}
                <Typography color="text.secondary">{item.title}</Typography>
                <Typography variant="h3">{item.value}</Typography>
                <Typography color="text.secondary">{item.text}</Typography>
              </Stack>
            </CustomCard>
          </Grid>
        ))}
      </Grid>

      <CustomCard>
        <Stack spacing={2}>
          <Typography variant="h4">Can xu ly hom nay</Typography>
          <Box sx={{ p: 2, borderRadius: 2, bgcolor: "rgba(245,158,11,0.12)" }}>
            <Typography fontWeight={700}>{overview.pendingRestaurants} nha hang cho duyet</Typography>
            <Typography color="text.secondary">
              Uu tien doi chieu thong tin va menu de giam thoi gian cho doi tac.
            </Typography>
          </Box>
          <Box sx={{ p: 2, borderRadius: 2, bgcolor: "rgba(47,107,255,0.1)" }}>
            <Typography fontWeight={700}>Theo doi tang truong luot dat ban</Typography>
            <Typography color="text.secondary">
              Tong {overview.totalBookings} luot dat ban dang duoc ghi nhan trong moi truong mock.
            </Typography>
          </Box>
        </Stack>
      </CustomCard>
    </Stack>
  );
}

export default AdminDashboardPage;
