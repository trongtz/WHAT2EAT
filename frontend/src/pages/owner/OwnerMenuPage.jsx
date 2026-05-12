import AddRoundedIcon from "@mui/icons-material/AddRounded";
import DeleteRoundedIcon from "@mui/icons-material/DeleteRounded";
import EditRoundedIcon from "@mui/icons-material/EditRounded";
import { Alert, Box, Chip, Grid, MenuItem, Stack, Typography } from "@mui/material";
import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import CustomButton from "../../components/CustomButton";
import CustomCard from "../../components/CustomCard";
import CustomModal from "../../components/CustomModal";
import EmptyState from "../../components/EmptyState";
import FormInput from "../../components/FormInput";
import LoadingScreen from "../../components/LoadingScreen";
import SectionHeader from "../../components/SectionHeader";
import { useAuth } from "../../hooks/useAuth";
import { restaurantService } from "../../services/restaurantService";
import { formatCurrency, getRestaurantStatusLabel } from "../../utils/helpers";

const emptyForm = {
  restaurantId: "",
  menuItemId: "",
  name: "",
  description: "",
  price: "",
  category: "",
  image_url: "",
  is_available: true,
};

function OwnerMenuPage() {
  const { user } = useAuth();
  const [searchParams] = useSearchParams();
  const [restaurants, setRestaurants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState("create");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState(emptyForm);

  const selectedRestaurantId = searchParams.get("restaurantId") || "";
  const focusCreate = searchParams.get("focus") === "create";

  const loadData = async () => {
    setLoading(true);
    try {
      const ownerRestaurants = await restaurantService.getOwnerRestaurants(user.id);
      const approvedRestaurants = ownerRestaurants.filter((restaurant) => restaurant.status === "APPROVED");
      const withMenus = await Promise.all(
        approvedRestaurants.map(async (restaurant) => {
          const menu = await restaurantService.getRestaurantMenu(restaurant.id);
          return { ...restaurant, menu };
        })
      );
      setRestaurants(withMenus);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [user.id]);

  useEffect(() => {
    if (focusCreate && selectedRestaurantId && restaurants.length) {
      handleOpenCreate(selectedRestaurantId);
    }
  }, [focusCreate, restaurants, selectedRestaurantId]);

  const visibleRestaurants = useMemo(() => {
    if (!selectedRestaurantId) return restaurants;
    return restaurants.filter((restaurant) => restaurant.id === selectedRestaurantId);
  }, [restaurants, selectedRestaurantId]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleClose = () => {
    setOpen(false);
    setForm(emptyForm);
  };

  const handleOpenCreate = (restaurantId) => {
    setMode("create");
    setForm({ ...emptyForm, restaurantId });
    setOpen(true);
  };

  const handleOpenEdit = (restaurantId, item) => {
    setMode("edit");
    setForm({
      restaurantId,
      menuItemId: item.id,
      name: item.name,
      description: item.description || "",
      price: item.price,
      category: item.category || "",
      image_url: item.imageUrl || "",
      is_available: item.isAvailable,
    });
    setOpen(true);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      if (mode === "create") {
        await restaurantService.createMenuItem(form.restaurantId, form);
        setMessage("Đã thêm món mới vào chi nhánh.");
      } else {
        await restaurantService.updateMenuItem(form.menuItemId, form);
        setMessage("Đã cập nhật món ăn.");
      }
      handleClose();
      await loadData();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (itemId) => {
    await restaurantService.deleteMenuItem(itemId);
    setMessage("Đã xóa món ăn khỏi menu.");
    await loadData();
  };

  if (loading) return <LoadingScreen message="Đang tải danh sách menu..." />;

  return (
    <Stack spacing={3}>
      <SectionHeader title={selectedRestaurantId ? "Menu chi nhánh" : "Quản lý menu"} />
      {message ? <Alert severity="success">{message}</Alert> : null}
      {error ? <Alert severity="error">{error}</Alert> : null}

      {visibleRestaurants.length ? (
        <Grid container spacing={3}>
          {visibleRestaurants.map((restaurant) => (
            <Grid key={restaurant.id} size={{ xs: 12 }}>
              <CustomCard>
                <Stack spacing={2}>
                  <Stack direction="row" justifyContent="space-between" alignItems="center" flexWrap="wrap" useFlexGap>
                    <Stack spacing={0.35}>
                      <Typography variant="h3">{restaurant.name}</Typography>
                      <Typography color="text.secondary">{restaurant.address}</Typography>
                    </Stack>
                    <Stack direction="row" spacing={1} alignItems="center">
                      <Chip label={`${restaurant.menu.length} món`} color="primary" variant="outlined" />
                      <Chip label={getRestaurantStatusLabel(restaurant.status)} color="success" />
                      <CustomButton startIcon={<AddRoundedIcon />} onClick={() => handleOpenCreate(restaurant.id)}>
                        Thêm món
                      </CustomButton>
                    </Stack>
                  </Stack>

                  {restaurant.menu.length ? (
                    <Grid container spacing={1.5}>
                      {restaurant.menu.map((item) => (
                        <Grid key={item.id} size={{ xs: 12, xl: 6 }}>
                          <Box
                            sx={{
                              p: 1.5,
                              borderRadius: 2,
                              bgcolor: "rgba(248,250,255,0.92)",
                              border: "1px solid rgba(15,23,42,0.06)",
                            }}
                          >
                            <Stack direction={{ xs: "column", md: "row" }} spacing={1.25} alignItems={{ md: "center" }}>
                              <Box
                                sx={{
                                  width: 110,
                                  minWidth: 110,
                                  height: 110,
                                  borderRadius: 1.75,
                                  overflow: "hidden",
                                  background: item.imageUrl
                                    ? `linear-gradient(180deg, rgba(18,22,44,0.05), rgba(18,22,44,0.18)), url(${item.imageUrl})`
                                    : "linear-gradient(135deg, color-mix(in srgb, var(--app-primary) 16%, white), color-mix(in srgb, var(--app-secondary) 12%, white))",
                                  backgroundSize: "cover",
                                  backgroundPosition: "center",
                                }}
                              />

                              <Stack spacing={0.5} sx={{ minWidth: 0, flex: 1 }}>
                                <Typography fontWeight={800}>{item.name}</Typography>
                                <Typography color="text.secondary">
                                  {item.description || "Chưa có mô tả món ăn."}
                                </Typography>
                                <Stack direction="row" spacing={0.75} flexWrap="wrap" useFlexGap>
                                  {item.category ? <Chip size="small" label={item.category} /> : null}
                                  <Chip size="small" label={item.isAvailable ? "Đang phục vụ" : "Tạm hết"} color={item.isAvailable ? "success" : "default"} />
                                </Stack>
                                <Typography fontWeight={800}>{formatCurrency(item.price)}</Typography>
                              </Stack>

                              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                                <CustomButton startIcon={<EditRoundedIcon />} onClick={() => handleOpenEdit(restaurant.id, item)}>
                                  Sửa
                                </CustomButton>
                                <CustomButton
                                  startIcon={<DeleteRoundedIcon />}
                                  onClick={() => handleDelete(item.id)}
                                  sx={{ background: "linear-gradient(135deg, #E85D75 0%, #FB7185 100%)" }}
                                >
                                  Xóa
                                </CustomButton>
                              </Stack>
                            </Stack>
                          </Box>
                        </Grid>
                      ))}
                    </Grid>
                  ) : (
                    <Typography color="text.secondary">Chi nhánh này chưa có món ăn nào.</Typography>
                  )}
                </Stack>
              </CustomCard>
            </Grid>
          ))}
        </Grid>
      ) : (
        <EmptyState title="Chưa có chi nhánh đã duyệt" description="Menu sẽ mở khi chi nhánh được admin duyệt." />
      )}

      <CustomModal open={open} onClose={handleClose} title={mode === "create" ? "Thêm món mới" : "Cập nhật món ăn"}>
        <Stack component="form" spacing={2} onSubmit={handleSubmit}>
          <FormInput label="Tên món" name="name" value={form.name} onChange={handleChange} required />
          <FormInput label="Mô tả" name="description" value={form.description} onChange={handleChange} multiline rows={3} />
          <FormInput label="Giá" name="price" value={form.price} onChange={handleChange} type="number" required />
          <FormInput label="Danh mục" name="category" value={form.category} onChange={handleChange} />
          <FormInput label="Ảnh món ăn" name="image_url" value={form.image_url} onChange={handleChange} />
          <FormInput select label="Trạng thái" name="is_available" value={String(form.is_available)} onChange={(event) => setForm((prev) => ({ ...prev, is_available: event.target.value === "true" }))}>
            <MenuItem value="true">Đang phục vụ</MenuItem>
            <MenuItem value="false">Tạm hết</MenuItem>
          </FormInput>
          <Stack direction="row" spacing={1.5}>
            <CustomButton type="submit" disabled={saving}>
              {saving ? "Đang lưu..." : mode === "create" ? "Thêm món" : "Lưu thay đổi"}
            </CustomButton>
            <CustomButton type="button" onClick={handleClose} sx={{ background: "linear-gradient(135deg, #64748B 0%, #94A3B8 100%)" }}>
              Đóng
            </CustomButton>
          </Stack>
        </Stack>
      </CustomModal>
    </Stack>
  );
}

export default OwnerMenuPage;
