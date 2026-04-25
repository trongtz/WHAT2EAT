import EditRoundedIcon from "@mui/icons-material/EditRounded";
import VisibilityRoundedIcon from "@mui/icons-material/VisibilityRounded";
import {
  Alert,
  Chip,
  Grid,
  MenuItem,
  Stack,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";
import { Link as RouterLink } from "react-router-dom";
import CustomButton from "../../components/CustomButton";
import CustomCard from "../../components/CustomCard";
import CustomModal from "../../components/CustomModal";
import FormInput from "../../components/FormInput";
import LoadingScreen from "../../components/LoadingScreen";
import SectionHeader from "../../components/SectionHeader";
import { useAuth } from "../../hooks/useAuth";
import { dashboardService } from "../../services/dashboardService";

const defaultForm = {
  restaurantId: "",
  name: "",
  category: "",
  address: "",
  description: "",
  priceRange: "",
  status: "",
};

function OwnerRestaurantsPage() {
  const { user } = useAuth();
  const [restaurants, setRestaurants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [form, setForm] = useState(defaultForm);

  const loadData = async () => {
    const data = await dashboardService.getOwnerRestaurants(user.id);
    setRestaurants(data);
    setLoading(false);
  };

  useEffect(() => {
    loadData();
  }, [user.id]);

  const handleOpen = (restaurant) => {
    setForm({
      restaurantId: restaurant.id,
      name: restaurant.name,
      category: restaurant.category,
      address: restaurant.address,
      description: restaurant.description,
      priceRange: restaurant.priceRange,
      status: restaurant.status,
    });
    setOpen(true);
  };

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSaving(true);
    try {
      await dashboardService.updateOwnerRestaurant({ ownerId: user.id, ...form });
      await loadData();
      setMessage("Đã cập nhật thông tin nhà hàng.");
      setOpen(false);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <LoadingScreen message="Đang tải danh sách nhà hàng..." />;

  return (
    <Stack spacing={3}>
      <SectionHeader
        title="Quản lý nhà hàng"
        description="Cập nhật hồ sơ hoạt động, trạng thái bàn và thông tin hiển thị công khai."
      />

      {message ? <Alert severity="success">{message}</Alert> : null}

      <Grid container spacing={3}>
        {restaurants.map((restaurant) => (
          <Grid key={restaurant.id} size={{ xs: 12, xl: 6 }}>
            <CustomCard>
              <Stack spacing={2}>
                <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
                  <Stack
                    sx={{
                      width: { xs: "100%", md: 180 },
                      height: 140,
                      borderRadius: 2,
                      flexShrink: 0,
                      backgroundImage: `url(${restaurant.image})`,
                      backgroundPosition: "center",
                      backgroundSize: "cover",
                    }}
                  />
                  <Stack spacing={1} flex={1}>
                    <Typography variant="h4">{restaurant.name}</Typography>
                    <Typography color="text.secondary">{restaurant.address}</Typography>
                    <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                      <Chip label={restaurant.category} />
                      <Chip
                        label={restaurant.approved ? "Đã duyệt" : "Chờ duyệt"}
                        color={restaurant.approved ? "success" : "warning"}
                      />
                      <Chip label={`Rating ${restaurant.rating}`} color="primary" variant="outlined" />
                    </Stack>
                    <Typography color="text.secondary">
                      {restaurant.reviews} đánh giá • {restaurant.priceRange}
                    </Typography>
                  </Stack>
                </Stack>

                <Grid container spacing={2}>
                  <Grid size={{ xs: 6, md: 3 }}>
                    <Typography color="text.secondary">Trạng thái bàn</Typography>
                    <Typography fontWeight={800}>{restaurant.status}</Typography>
                  </Grid>
                  <Grid size={{ xs: 6, md: 3 }}>
                    <Typography color="text.secondary">Món đang hiển thị</Typography>
                    <Typography fontWeight={800}>{restaurant.menu.length}</Typography>
                  </Grid>
                  <Grid size={{ xs: 6, md: 3 }}>
                    <Typography color="text.secondary">Khoảng cách</Typography>
                    <Typography fontWeight={800}>{restaurant.distance}</Typography>
                  </Grid>
                  <Grid size={{ xs: 6, md: 3 }}>
                    <Typography color="text.secondary">Giá trung bình</Typography>
                    <Typography fontWeight={800}>
                      {restaurant.averagePrice.toLocaleString("vi-VN")}đ
                    </Typography>
                  </Grid>
                </Grid>

                <Stack direction="row" spacing={1.25} flexWrap="wrap" useFlexGap>
                  <CustomButton
                    startIcon={<EditRoundedIcon />}
                    onClick={() => handleOpen(restaurant)}
                  >
                    Cập nhật thông tin
                  </CustomButton>
                  <CustomButton
                    component={RouterLink}
                    to={`/nha-hang/${restaurant.id}`}
                    startIcon={<VisibilityRoundedIcon />}
                    sx={{ background: "linear-gradient(135deg, #64748B 0%, #94A3B8 100%)" }}
                  >
                    Xem trang công khai
                  </CustomButton>
                </Stack>
              </Stack>
            </CustomCard>
          </Grid>
        ))}
      </Grid>

      <CustomModal open={open} onClose={() => setOpen(false)} title="Cập nhật nhà hàng">
        <Stack component="form" spacing={2} onSubmit={handleSubmit}>
          <FormInput label="Tên nhà hàng" name="name" value={form.name} onChange={handleChange} />
          <FormInput label="Danh mục" name="category" value={form.category} onChange={handleChange} />
          <FormInput label="Địa chỉ" name="address" value={form.address} onChange={handleChange} />
          <FormInput
            label="Khoảng giá"
            name="priceRange"
            value={form.priceRange}
            onChange={handleChange}
          />
          <FormInput
            select
            label="Trạng thái bàn"
            name="status"
            value={form.status}
            onChange={handleChange}
          >
            <MenuItem value="Còn chỗ">Còn chỗ</MenuItem>
            <MenuItem value="Sắp đầy">Sắp đầy</MenuItem>
            <MenuItem value="Hết chỗ">Hết chỗ</MenuItem>
          </FormInput>
          <FormInput
            multiline
            rows={4}
            label="Mô tả"
            name="description"
            value={form.description}
            onChange={handleChange}
          />
          <Stack direction="row" spacing={1.5}>
            <CustomButton type="submit" disabled={saving}>
              {saving ? "Đang lưu..." : "Lưu cập nhật"}
            </CustomButton>
            <CustomButton
              type="button"
              onClick={() => setOpen(false)}
              sx={{ background: "linear-gradient(135deg, #64748B 0%, #94A3B8 100%)" }}
            >
              Hủy
            </CustomButton>
          </Stack>
        </Stack>
      </CustomModal>
    </Stack>
  );
}

export default OwnerRestaurantsPage;
