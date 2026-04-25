import DeleteRoundedIcon from "@mui/icons-material/DeleteRounded";
import EditRoundedIcon from "@mui/icons-material/EditRounded";
import LocalOfferRoundedIcon from "@mui/icons-material/LocalOfferRounded";
import RestaurantMenuRoundedIcon from "@mui/icons-material/RestaurantMenuRounded";
import AddRoundedIcon from "@mui/icons-material/AddRounded";
import {
  Alert,
  Chip,
  Grid,
  Stack,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";
import CustomButton from "../../components/CustomButton";
import CustomCard from "../../components/CustomCard";
import CustomModal from "../../components/CustomModal";
import FormInput from "../../components/FormInput";
import LoadingScreen from "../../components/LoadingScreen";
import SectionHeader from "../../components/SectionHeader";
import { useAuth } from "../../hooks/useAuth";
import { dashboardService } from "../../services/dashboardService";
import { formatCurrency } from "../../utils/helpers";

const emptyForm = { restaurantId: "", menuItemId: "", name: "", price: "" };

function OwnerMenuPage() {
  const { user } = useAuth();
  const [restaurants, setRestaurants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState("create");
  const [message, setMessage] = useState("");
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState(emptyForm);

  const loadData = async () => {
    const data = await dashboardService.getOwnerRestaurants(user.id);
    setRestaurants(data);
    setLoading(false);
  };

  useEffect(() => {
    loadData();
  }, [user.id]);

  const handleOpenCreate = (restaurantId) => {
    setMode("create");
    setForm({ ...emptyForm, restaurantId, price: "" });
    setOpen(true);
  };

  const handleOpenEdit = (restaurantId, item) => {
    setMode("edit");
    setForm({
      restaurantId,
      menuItemId: item.id,
      name: item.name,
      price: item.price,
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
      if (mode === "create") {
        await dashboardService.createMenuItem({ ownerId: user.id, ...form });
        setMessage("Đã thêm món mới vào menu.");
      } else {
        await dashboardService.updateMenuItem({ ownerId: user.id, ...form });
        setMessage("Đã cập nhật món ăn.");
      }
      await loadData();
      setOpen(false);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (restaurantId, menuItemId) => {
    await dashboardService.deleteMenuItem({ ownerId: user.id, restaurantId, menuItemId });
    setMessage("Đã xóa món khỏi menu.");
    await loadData();
  };

  if (loading) return <LoadingScreen message="Đang tải danh sách menu..." />;

  return (
    <Stack spacing={3}>
      <SectionHeader
        title="Quản lý menu"
        description="Thêm, sửa, xóa món ăn và quản lý giá hiển thị trên ứng dụng."
      />

      {message ? <Alert severity="success">{message}</Alert> : null}

      <Grid container spacing={3}>
        {restaurants.map((restaurant) => (
          <Grid key={restaurant.id} size={{ xs: 12, lg: 6 }}>
            <CustomCard>
              <Stack spacing={2}>
                <Stack direction="row" justifyContent="space-between" alignItems="center">
                  <BoxTitle name={restaurant.name} />
                  <Stack direction="row" spacing={1} alignItems="center">
                    <Chip label={`${restaurant.menu.length} món`} color="primary" variant="outlined" />
                    <CustomButton
                      startIcon={<AddRoundedIcon />}
                      onClick={() => handleOpenCreate(restaurant.id)}
                    >
                      Thêm món
                    </CustomButton>
                  </Stack>
                </Stack>

                <Stack spacing={1.25}>
                  {restaurant.menu.map((item) => (
                    <Stack
                      key={item.id}
                      direction={{ xs: "column", md: "row" }}
                      justifyContent="space-between"
                      alignItems={{ xs: "flex-start", md: "center" }}
                      sx={{
                        p: 1.5,
                        borderRadius: 2,
                        bgcolor: "rgba(248,250,255,0.92)",
                        border: "1px solid rgba(15,23,42,0.06)",
                      }}
                    >
                      <Stack direction="row" spacing={1.25} alignItems="center">
                        <RestaurantMenuRoundedIcon color="warning" />
                        <Stack spacing={0.25}>
                          <BoxTitle name={item.name} small />
                          <Chip
                            icon={<LocalOfferRoundedIcon />}
                            label={formatCurrency(item.price)}
                            sx={{ alignSelf: "flex-start" }}
                          />
                        </Stack>
                      </Stack>
                      <Stack direction="row" spacing={1}>
                        <CustomButton
                          startIcon={<EditRoundedIcon />}
                          onClick={() => handleOpenEdit(restaurant.id, item)}
                        >
                          Sửa
                        </CustomButton>
                        <CustomButton
                          startIcon={<DeleteRoundedIcon />}
                          onClick={() => handleDelete(restaurant.id, item.id)}
                          sx={{ background: "linear-gradient(135deg, #E85D75 0%, #FB7185 100%)" }}
                        >
                          Xóa
                        </CustomButton>
                      </Stack>
                    </Stack>
                  ))}
                </Stack>
              </Stack>
            </CustomCard>
          </Grid>
        ))}
      </Grid>

      <CustomModal
        open={open}
        onClose={() => setOpen(false)}
        title={mode === "create" ? "Thêm món mới" : "Cập nhật món ăn"}
      >
        <Stack component="form" spacing={2} onSubmit={handleSubmit}>
          <FormInput label="Tên món" name="name" value={form.name} onChange={handleChange} />
          <FormInput label="Giá" name="price" value={form.price} onChange={handleChange} />
          <Stack direction="row" spacing={1.5}>
            <CustomButton type="submit" disabled={saving}>
              {saving ? "Đang lưu..." : mode === "create" ? "Thêm món" : "Lưu thay đổi"}
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

function BoxTitle({ name, small }) {
  return (
    <Typography variant={small ? "body1" : "h4"} fontWeight={700}>
      {name}
    </Typography>
  );
}

export default OwnerMenuPage;
