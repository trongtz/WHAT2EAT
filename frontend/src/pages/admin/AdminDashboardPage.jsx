import ApartmentRoundedIcon from "@mui/icons-material/ApartmentRounded";
import CheckCircleRoundedIcon from "@mui/icons-material/CheckCircleRounded";
import PhotoLibraryRoundedIcon from "@mui/icons-material/PhotoLibraryRounded";
import ScheduleRoundedIcon from "@mui/icons-material/ScheduleRounded";
import { Box, Grid, Stack, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import CustomCard from "../../components/CustomCard";
import LoadingScreen from "../../components/LoadingScreen";
import SectionHeader from "../../components/SectionHeader";
import StatsCard from "../../components/StatsCard";
import { restaurantService } from "../../services/restaurantService";

function AdminDashboardPage() {
  const [restaurants, setRestaurants] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      const data = await restaurantService.getAdminRestaurants();
      setRestaurants(data);
    };
    loadData();
  }, []);

  if (!restaurants) return <LoadingScreen message="Đang tải tổng quan hệ thống..." />;

  const pendingRestaurants = restaurants.filter((item) => item.status === "PENDING").length;
  const approvedRestaurants = restaurants.filter((item) => item.status === "APPROVED").length;
  const rejectedRestaurants = restaurants.filter((item) => item.status === "REJECTED").length;
  const ownerCount = new Set(restaurants.map((item) => item.ownerId)).size;
  const averageRating =
    restaurants.length > 0
      ? (
          restaurants.reduce((sum, item) => sum + Number(item.averageRating || 0), 0) / restaurants.length
        ).toFixed(1)
      : "0.0";
  const withImages = restaurants.filter((item) => Array.isArray(item.images) && item.images.length > 0).length;

  return (
    <Stack spacing={3}>
      <SectionHeader title="Tổng quan" />

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 3 }}>
          <StatsCard label="Tổng chi nhánh" value={restaurants.length} color="rgba(47,107,255,0.18)" />
        </Grid>
        <Grid size={{ xs: 12, md: 3 }}>
          <StatsCard label="Chờ duyệt" value={pendingRestaurants} color="rgba(245,158,11,0.22)" />
        </Grid>
        <Grid size={{ xs: 12, md: 3 }}>
          <StatsCard label="Đã duyệt" value={approvedRestaurants} color="rgba(32,180,134,0.18)" />
        </Grid>
        <Grid size={{ xs: 12, md: 3 }}>
          <StatsCard label="Chủ nhà hàng" value={ownerCount} color="rgba(232,93,117,0.18)" />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {[
          {
            icon: <ApartmentRoundedIcon color="primary" />,
            title: "Chi nhánh bị từ chối",
            value: rejectedRestaurants,
            text: "Cần theo dõi chất lượng hồ sơ và hướng dẫn owner bổ sung thông tin.",
          },
          {
            icon: <CheckCircleRoundedIcon color="success" />,
            title: "Đánh giá trung bình",
            value: averageRating,
            text: "Chỉ số tổng hợp của các chi nhánh hiện có.",
          },
          {
            icon: <PhotoLibraryRoundedIcon color="warning" />,
            title: "Chi nhánh có hình ảnh",
            value: withImages,
            text: "Số hồ sơ đã có ảnh minh họa để hỗ trợ duyệt và hiển thị tốt hơn.",
          },
          {
            icon: <ScheduleRoundedIcon color="error" />,
            title: "Chi nhánh đang chờ xử lý",
            value: pendingRestaurants,
            text: "Khối lượng công việc mà admin cần phê duyệt tiếp theo.",
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
          <Typography variant="h4">Cần xử lý hôm nay</Typography>
          <Box sx={{ p: 2, borderRadius: 2, bgcolor: "rgba(245,158,11,0.12)" }}>
            <Typography fontWeight={700}>{pendingRestaurants} chi nhánh chờ duyệt</Typography>
            <Typography color="text.secondary">
              Chi nhánh owner mới tạo sẽ chỉ có quyền sửa thông tin và menu sau khi được admin chấp thuận.
            </Typography>
          </Box>
          <Box sx={{ p: 2, borderRadius: 2, bgcolor: "rgba(47,107,255,0.1)" }}>
            <Typography fontWeight={700}>{approvedRestaurants} chi nhánh đã sẵn sàng vận hành</Typography>
            <Typography color="text.secondary">
              Đây là nhóm chi nhánh đã mở khóa cập nhật menu, hình ảnh và thông tin kinh doanh.
            </Typography>
          </Box>
        </Stack>
      </CustomCard>
    </Stack>
  );
}

export default AdminDashboardPage;
