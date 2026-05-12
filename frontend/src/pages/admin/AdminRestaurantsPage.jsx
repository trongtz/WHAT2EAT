import BlockRoundedIcon from "@mui/icons-material/BlockRounded";
import CheckCircleRoundedIcon from "@mui/icons-material/CheckCircleRounded";
import { Alert, Chip, Grid, Stack, Typography } from "@mui/material";
import { useEffect, useMemo, useState } from "react";
import CustomButton from "../../components/CustomButton";
import CustomCard from "../../components/CustomCard";
import EmptyState from "../../components/EmptyState";
import LoadingScreen from "../../components/LoadingScreen";
import SectionHeader from "../../components/SectionHeader";
import { restaurantService } from "../../services/restaurantService";
import { getPriceRangeLabel } from "../../utils/helpers";

function AdminRestaurantsPage() {
  const [items, setItems] = useState(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const loadData = async () => {
    try {
      const data = await restaurantService.getAdminRestaurants();
      setItems(data);
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const pendingItems = useMemo(() => (items || []).filter((item) => item.status === "PENDING"), [items]);

  const handleStatus = async (restaurantId, status) => {
    await restaurantService.updateAdminRestaurantStatus(restaurantId, status);
    setMessage(status === "APPROVED" ? "Đã duyệt chi nhánh." : "Đã từ chối chi nhánh.");
    await loadData();
  };

  if (!items) return <LoadingScreen message="Đang tải danh sách chi nhánh..." />;

  return (
    <Stack spacing={3}>
      <SectionHeader title="Duyệt nhà hàng" />
      {message ? <Alert severity="success">{message}</Alert> : null}
      {error ? <Alert severity="error">{error}</Alert> : null}

      {pendingItems.length ? (
        <Grid container spacing={3}>
          {pendingItems.map((item) => (
            <Grid key={item.id} size={{ xs: 12 }}>
              <CustomCard>
                <Stack direction={{ xs: "column", lg: "row" }} spacing={2.5} justifyContent="space-between">
                  <Stack spacing={1.25}>
                    <Typography variant="h4">{item.name}</Typography>
                    <Typography color="text.secondary">{item.address}</Typography>
                    <Typography color="text.secondary">Owner: {item.ownerName || item.ownerEmail || "Chưa rõ"}</Typography>
                    <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                      {item.cuisineType
                        ?.split(",")
                        .map((part) => part.trim())
                        .filter(Boolean)
                        .slice(0, 3)
                        .map((part) => <Chip key={part} label={part} />)}
                      <Chip label={getPriceRangeLabel(item.priceRange)} variant="outlined" />
                      <Chip label="Chờ duyệt" color="warning" />
                    </Stack>
                    <Typography color="text.secondary">{item.description || "Không có mô tả."}</Typography>
                  </Stack>
                  <Stack spacing={1.25} alignItems={{ xs: "stretch", lg: "flex-end" }}>
                    <CustomButton startIcon={<CheckCircleRoundedIcon />} onClick={() => handleStatus(item.id, "APPROVED")}>
                      Duyệt chi nhánh
                    </CustomButton>
                    <CustomButton
                      startIcon={<BlockRoundedIcon />}
                      onClick={() => handleStatus(item.id, "REJECTED")}
                      sx={{ background: "linear-gradient(135deg, #E85D75 0%, #FB7185 100%)" }}
                    >
                      Từ chối
                    </CustomButton>
                  </Stack>
                </Stack>
              </CustomCard>
            </Grid>
          ))}
        </Grid>
      ) : (
        <EmptyState title="Không có hồ sơ chờ duyệt" description="" />
      )}
    </Stack>
  );
}

export default AdminRestaurantsPage;
