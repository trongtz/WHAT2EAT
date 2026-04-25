import CheckCircleRoundedIcon from "@mui/icons-material/CheckCircleRounded";
import HighlightRoundedIcon from "@mui/icons-material/HighlightRounded";
import BlockRoundedIcon from "@mui/icons-material/BlockRounded";
import { Alert, Chip, Grid, Stack, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import CustomButton from "../../components/CustomButton";
import CustomCard from "../../components/CustomCard";
import LoadingScreen from "../../components/LoadingScreen";
import SectionHeader from "../../components/SectionHeader";
import { dashboardService } from "../../services/dashboardService";

function AdminRestaurantsPage() {
  const [items, setItems] = useState(null);
  const [message, setMessage] = useState("");

  const loadData = async () => {
    const data = await dashboardService.getAdminRestaurants();
    setItems(data);
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleApprove = async (restaurantId) => {
    await dashboardService.approveRestaurant(restaurantId);
    setMessage("Đã duyệt nhà hàng.");
    await loadData();
  };

  const handleReject = async (restaurantId) => {
    await dashboardService.rejectRestaurant(restaurantId);
    setMessage("Đã từ chối nhà hàng.");
    await loadData();
  };

  const handleToggleFeatured = async (restaurantId) => {
    await dashboardService.toggleRestaurantFeatured(restaurantId);
    setMessage("Đã cập nhật trạng thái nổi bật.");
    await loadData();
  };

  if (!items) return <LoadingScreen message="Đang tải danh sách nhà hàng..." />;

  return (
    <Stack spacing={3}>
      <SectionHeader
        title="Quản lý nhà hàng"
        description="Duyệt, từ chối và điều chỉnh trạng thái nổi bật cho toàn bộ nhà hàng trong hệ thống."
      />

      {message ? <Alert severity="success">{message}</Alert> : null}

      <Grid container spacing={3}>
        {items.map((item) => (
          <Grid key={item.id} size={{ xs: 12 }}>
            <CustomCard>
              <Stack direction={{ xs: "column", lg: "row" }} spacing={2.5} justifyContent="space-between">
                <Stack spacing={1.25}>
                  <Typography variant="h4">{item.name}</Typography>
                  <Typography color="text.secondary">{item.address}</Typography>
                  <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                    <Chip label={item.category} />
                    <Chip label={item.priceRange} variant="outlined" />
                    <Chip label={`Rating ${item.rating}`} color="primary" />
                    <Chip label={item.approved ? "Đã duyệt" : "Chờ duyệt"} color={item.approved ? "success" : "warning"} />
                    <Chip label={item.featured ? "Nổi bật" : "Thường"} color={item.featured ? "secondary" : "default"} />
                  </Stack>
                  <Typography color="text.secondary">{item.description}</Typography>
                </Stack>
                <Stack spacing={1.25} alignItems={{ xs: "stretch", lg: "flex-end" }}>
                  <CustomButton
                    startIcon={<CheckCircleRoundedIcon />}
                    onClick={() => handleApprove(item.id)}
                  >
                    Duyệt nhà hàng
                  </CustomButton>
                  <CustomButton
                    startIcon={<BlockRoundedIcon />}
                    onClick={() => handleReject(item.id)}
                    sx={{ background: "linear-gradient(135deg, #E85D75 0%, #FB7185 100%)" }}
                  >
                    Từ chối
                  </CustomButton>
                  <CustomButton
                    startIcon={<HighlightRoundedIcon />}
                    onClick={() => handleToggleFeatured(item.id)}
                    sx={{ background: "linear-gradient(135deg, #F59E0B 0%, #FBBF24 100%)" }}
                  >
                    {item.featured ? "Bỏ nổi bật" : "Đặt nổi bật"}
                  </CustomButton>
                </Stack>
              </Stack>
            </CustomCard>
          </Grid>
        ))}
      </Grid>
    </Stack>
  );
}

export default AdminRestaurantsPage;
