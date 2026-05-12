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
import {
  formatDateTime,
  getPriceRangeLabel,
  getRestaurantStatusLabel,
  getStatusColor,
} from "../../utils/helpers";

function AdminRestaurantsPage() {
  const [items, setItems] = useState(null);
  const [message, setMessage] = useState("");
  const [filter, setFilter] = useState("ALL");

  const loadData = async () => {
    const data = await restaurantService.getAdminRestaurants();
    setItems(data);
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleStatus = async (restaurantId, status) => {
    await restaurantService.updateAdminRestaurantStatus(restaurantId, status);
    setMessage(status === "APPROVED" ? "Đã duyệt chi nhánh." : "Đã từ chối chi nhánh.");
    await loadData();
  };

  const filteredItems = useMemo(() => {
    if (!items) return [];
    if (filter === "ALL") return items;
    return items.filter((item) => item.status === filter);
  }, [filter, items]);

  if (!items) return <LoadingScreen message="Đang tải danh sách chi nhánh..." />;

  const pendingCount = items.filter((item) => item.status === "PENDING").length;
  const approvedCount = items.filter((item) => item.status === "APPROVED").length;
  const rejectedCount = items.filter((item) => item.status === "REJECTED").length;

  return (
    <Stack spacing={3}>
      <SectionHeader
        title="Duyệt chi nhánh nhà hàng"
        description="Tất cả chi nhánh owner đăng ký sẽ hiển thị tại đây để admin xác minh và phê duyệt."
      />

      {message ? <Alert severity="success">{message}</Alert> : null}

      <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
        <Chip label={`Tất cả (${items.length})`} color={filter === "ALL" ? "primary" : "default"} onClick={() => setFilter("ALL")} />
        <Chip label={`Chờ duyệt (${pendingCount})`} color={filter === "PENDING" ? "warning" : "default"} onClick={() => setFilter("PENDING")} />
        <Chip label={`Đã duyệt (${approvedCount})`} color={filter === "APPROVED" ? "success" : "default"} onClick={() => setFilter("APPROVED")} />
        <Chip label={`Từ chối (${rejectedCount})`} color={filter === "REJECTED" ? "error" : "default"} onClick={() => setFilter("REJECTED")} />
      </Stack>

      {filteredItems.length ? (
        <Grid container spacing={3}>
          {filteredItems.map((item) => (
            <Grid key={item.id} size={{ xs: 12 }}>
              <CustomCard>
                <Stack direction={{ xs: "column", lg: "row" }} spacing={2.5} justifyContent="space-between">
                  <Stack spacing={1.25}>
                    <Typography variant="h4">{item.name}</Typography>
                    <Typography color="text.secondary">{item.address}</Typography>
                    <Typography color="text.secondary">
                      Owner: {item.ownerName || "Chưa rõ"} {item.ownerEmail ? `• ${item.ownerEmail}` : ""}
                    </Typography>
                    <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                      <Chip label={item.cuisineType || "Chưa có loại ẩm thực"} />
                      <Chip label={getPriceRangeLabel(item.priceRange)} variant="outlined" />
                      <Chip label={getRestaurantStatusLabel(item.status)} color={getStatusColor(item.status)} />
                    </Stack>
                    <Typography color="text.secondary">{item.description || "Chi nhánh chưa có mô tả."}</Typography>
                    <Typography color="text.secondary">Số điện thoại: {item.phone || "Chưa cập nhật"}</Typography>
                    <Typography color="text.secondary">Ngày gửi hồ sơ: {formatDateTime(item.createdAt)}</Typography>
                  </Stack>
                  <Stack spacing={1.25} alignItems={{ xs: "stretch", lg: "flex-end" }}>
                    <CustomButton
                      startIcon={<CheckCircleRoundedIcon />}
                      onClick={() => handleStatus(item.id, "APPROVED")}
                      disabled={item.status === "APPROVED"}
                    >
                      Duyệt chi nhánh
                    </CustomButton>
                    <CustomButton
                      startIcon={<BlockRoundedIcon />}
                      onClick={() => handleStatus(item.id, "REJECTED")}
                      disabled={item.status === "REJECTED"}
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
        <EmptyState
          title="Không có chi nhánh nào trong bộ lọc này"
          description="Thử chuyển bộ lọc hoặc đợi owner gửi thêm hồ sơ chi nhánh mới."
        />
      )}
    </Stack>
  );
}

export default AdminRestaurantsPage;
