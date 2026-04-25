import CalendarMonthRoundedIcon from "@mui/icons-material/CalendarMonthRounded";
import InsightsRoundedIcon from "@mui/icons-material/InsightsRounded";
import RateReviewRoundedIcon from "@mui/icons-material/RateReviewRounded";
import StorefrontRoundedIcon from "@mui/icons-material/StorefrontRounded";
import { Box, Chip, Grid, Stack, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import CustomCard from "../../components/CustomCard";
import LoadingScreen from "../../components/LoadingScreen";
import SectionHeader from "../../components/SectionHeader";
import StatsCard from "../../components/StatsCard";
import { useAuth } from "../../hooks/useAuth";
import { dashboardService } from "../../services/dashboardService";

function OwnerDashboardPage() {
  const { user } = useAuth();
  const [data, setData] = useState({
    restaurants: [],
    bookings: [],
    reviews: [],
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      const [restaurants, bookings, reviews] = await Promise.all([
        dashboardService.getOwnerRestaurants(user.id),
        dashboardService.getOwnerBookings(user.id),
        dashboardService.getOwnerReviews(user.id),
      ]);
      setData({ restaurants, bookings, reviews });
      setLoading(false);
    };
    loadData();
  }, [user.id]);

  if (loading) return <LoadingScreen message="Dang tai tong quan van hanh..." />;

  const confirmedBookings = data.bookings.filter((item) => item.status === "Đã xác nhận").length;
  const averageRating =
    data.reviews.length > 0
      ? (data.reviews.reduce((sum, item) => sum + Number(item.rating || 0), 0) / data.reviews.length).toFixed(1)
      : "0.0";

  return (
    <Stack spacing={3}>
      <SectionHeader
        eyebrow="Owner workspace"
        title="Tong quan kinh doanh"
        description="Theo doi doanh thu tiem nang, chat luong phuc vu va tinh trang van hanh cac co so."
      />

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 3 }}>
          <StatsCard label="Co so dang quan ly" value={data.restaurants.length} color="rgba(255,159,28,0.22)" />
        </Grid>
        <Grid size={{ xs: 12, md: 3 }}>
          <StatsCard label="Luot dat ban" value={data.bookings.length} color="rgba(47,107,255,0.18)" />
        </Grid>
        <Grid size={{ xs: 12, md: 3 }}>
          <StatsCard label="Da xac nhan" value={confirmedBookings} color="rgba(32,180,134,0.18)" />
        </Grid>
        <Grid size={{ xs: 12, md: 3 }}>
          <StatsCard label="Diem danh gia TB" value={averageRating} color="rgba(232,93,117,0.18)" />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, lg: 8 }}>
          <CustomCard>
            <Stack spacing={2.5}>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Typography variant="h4">Suc khoe hoat dong hom nay</Typography>
                <Chip label="Cap nhat luc 10:30" color="primary" variant="outlined" />
              </Stack>

              <Grid container spacing={2}>
                {[
                  {
                    icon: <StorefrontRoundedIcon color="warning" />,
                    title: "Ty le duyet nha hang",
                    value: `${data.restaurants.filter((item) => item.approved).length}/${data.restaurants.length}`,
                    text: "Co so da duyet san sang nhan dat ban.",
                  },
                  {
                    icon: <CalendarMonthRoundedIcon color="primary" />,
                    title: "Lich hen can xu ly",
                    value: data.bookings.filter((item) => item.status === "Chờ duyệt").length,
                    text: "Dat ban moi can xac nhan trong ca hien tai.",
                  },
                  {
                    icon: <RateReviewRoundedIcon color="error" />,
                    title: "Danh gia moi",
                    value: data.reviews.length,
                    text: "Can theo doi phan hoi de cai thien trai nghiem.",
                  },
                  {
                    icon: <InsightsRoundedIcon color="success" />,
                    title: "Menu dang hien thi",
                    value: data.restaurants.reduce((sum, item) => sum + item.menu.length, 0),
                    text: "Tong so mon dang hien thi tren ung dung.",
                  },
                ].map((item) => (
                  <Grid key={item.title} size={{ xs: 12, md: 6 }}>
                    <Box
                      sx={{
                        p: 2,
                        borderRadius: 2,
                        border: "1px solid rgba(15,23,42,0.06)",
                        bgcolor: "rgba(248,250,255,0.92)",
                      }}
                    >
                      <Stack spacing={1.25}>
                        {item.icon}
                        <Typography color="text.secondary">{item.title}</Typography>
                        <Typography variant="h3">{item.value}</Typography>
                        <Typography color="text.secondary">{item.text}</Typography>
                      </Stack>
                    </Box>
                  </Grid>
                ))}
              </Grid>
            </Stack>
          </CustomCard>
        </Grid>

        <Grid size={{ xs: 12, lg: 4 }}>
          <CustomCard>
            <Stack spacing={2}>
              <Typography variant="h4">Can uu tien</Typography>
              <Box sx={{ p: 2, borderRadius: 2, bgcolor: "rgba(255,159,28,0.12)" }}>
                <Typography fontWeight={700}>1 nha hang dang cho duyet</Typography>
                <Typography color="text.secondary">
                  Hoan thien ho so va menu de duoc admin duyet nhanh hon.
                </Typography>
              </Box>
              <Box sx={{ p: 2, borderRadius: 2, bgcolor: "rgba(47,107,255,0.1)" }}>
                <Typography fontWeight={700}>
                  {data.bookings.filter((item) => item.status === "Chờ duyệt").length} dat ban can xac nhan
                </Typography>
                <Typography color="text.secondary">
                  Xac nhan som de khong bo lo khach hang co nhu cau cao.
                </Typography>
              </Box>
              <Box sx={{ p: 2, borderRadius: 2, bgcolor: "rgba(232,93,117,0.1)" }}>
                <Typography fontWeight={700}>Theo doi phan hoi moi nhat</Typography>
                <Typography color="text.secondary">
                  Danh gia khach hang anh huong truc tiep den kha nang duoc de xuat.
                </Typography>
              </Box>
            </Stack>
          </CustomCard>
        </Grid>
      </Grid>
    </Stack>
  );
}

export default OwnerDashboardPage;
