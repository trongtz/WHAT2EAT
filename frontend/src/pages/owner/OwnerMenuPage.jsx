import AddRoundedIcon from "@mui/icons-material/AddRounded";
import DeleteRoundedIcon from "@mui/icons-material/DeleteRounded";
import EditRoundedIcon from "@mui/icons-material/EditRounded";
import RestaurantMenuRoundedIcon from "@mui/icons-material/RestaurantMenuRounded";
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
import { formatCurrency } from "../../utils/helpers";

const emptyForm = {
  restaurantId: "",
  itemId: "",
  name: "",
  description: "",
  category: "",
  price: "",
  image_url: "",
  is_available: true,
};

function MenuImage({ imageUrl, size = 88 }) {
  return (
    <Box
      sx={{
        width: size,
        height: size,
        borderRadius: 2,
        flexShrink: 0,
        border: "1px solid rgba(15,23,42,0.08)",
        background: imageUrl
          ? `linear-gradient(180deg, rgba(18,22,44,0.05), rgba(18,22,44,0.16)), url(${imageUrl})`
          : "linear-gradient(135deg, rgba(255,159,28,0.18), rgba(47,107,255,0.14))",
        backgroundPosition: "center",
        backgroundSize: "cover",
        display: "grid",
        placeItems: "center",
        boxShadow: "inset 0 1px 0 rgba(255,255,255,0.72)",
      }}
    >
      {!imageUrl ? <RestaurantMenuRoundedIcon color="warning" /> : null}
    </Box>
  );
}

function OwnerMenuPage() {
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [restaurants, setRestaurants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState("create");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState(emptyForm);

  const restaurantIdParam = searchParams.get("restaurantId");
  const actionParam = searchParams.get("action");

  const loadData = async () => {
    const ownerRestaurants = await restaurantService.getOwnerRestaurants(user.id);
    const approvedRestaurants = ownerRestaurants.filter((item) => item.status === "APPROVED");
    const menus = await Promise.all(
      approvedRestaurants.map(async (restaurant) => ({
        ...restaurant,
        menu: await restaurantService.getRestaurantMenu(restaurant.id),
      }))
    );
    setRestaurants(menus);
    setLoading(false);
  };

  useEffect(() => {
    loadData();
  }, [user.id]);

  useEffect(() => {
    if (!restaurants.length || !restaurantIdParam || actionParam !== "create" || open) return;

    const targetRestaurant = restaurants.find((item) => String(item.id) === String(restaurantIdParam));
    if (!targetRestaurant) return;

    setMode("create");
    setError("");
    setForm({ ...emptyForm, restaurantId: targetRestaurant.id });
    setOpen(true);
  }, [actionParam, open, restaurantIdParam, restaurants]);

  const selectedRestaurant = useMemo(() => {
    if (!restaurantIdParam) return null;
    return restaurants.find((item) => String(item.id) === String(restaurantIdParam)) || null;
  }, [restaurantIdParam, restaurants]);

  const visibleRestaurants = selectedRestaurant ? [selectedRestaurant] : restaurants;

  const clearActionParams = () => {
    const nextParams = new URLSearchParams(searchParams);
    nextParams.delete("action");
    setSearchParams(nextParams, { replace: true });
  };

  const handleOpenCreate = (restaurantId) => {
    setMode("create");
    setError("");
    setForm({ ...emptyForm, restaurantId });
    setOpen(true);
    clearActionParams();
  };

  const handleOpenEdit = (restaurantId, item) => {
    setMode("edit");
    setError("");
    setForm({
      restaurantId,
      itemId: item.id,
      name: item.name,
      description: item.description ?? "",
      category: item.category ?? "",
      price: item.price,
      image_url: item.imageUrl ?? "",
      is_available: Boolean(item.isAvailable),
    });
    setOpen(true);
    clearActionParams();
  };

  const handleCloseModal = () => {
    setOpen(false);
    clearActionParams();
  };

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({
      ...prev,
      [name]: name === "is_available" ? value === "true" : value,
    }));
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
        await restaurantService.updateMenuItem(form.itemId, form);
        setMessage("Đã cập nhật món ăn.");
      }
      setOpen(false);
      clearActionParams();
      await loadData();
    } catch (submitError) {
      setError(submitError.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (itemId) => {
    await restaurantService.deleteMenuItem(itemId);
    setMessage("Đã xóa món ăn khỏi menu.");
    await loadData();
  };

  if (loading) return <LoadingScreen message="Đang tải menu các chi nhánh..." />;

  if (!restaurants.length) {
    return (
      <Stack spacing={3}>
        <SectionHeader
          title="Quản lý menu"
          description="Menu chỉ được mở khi ít nhất một chi nhánh đã được admin duyệt."
        />
        <EmptyState
          title="Chưa có chi nhánh nào được duyệt"
          description="Khi admin phê duyệt chi nhánh, bạn sẽ có quyền thêm món ăn và cập nhật tình trạng phục vụ."
        />
      </Stack>
    );
  }

  return (
    <Stack spacing={3}>
      <SectionHeader
        title={selectedRestaurant ? `Menu chi nhánh ${selectedRestaurant.name}` : "Quản lý menu theo chi nhánh"}
        description="Món ăn được thêm tại đây sẽ hiển thị trực tiếp cho chi nhánh tương ứng."
      />

      {message ? <Alert severity="success">{message}</Alert> : null}

      <Grid container spacing={3}>
        {visibleRestaurants.map((restaurant) => (
          <Grid key={restaurant.id} size={{ xs: 12, lg: selectedRestaurant ? 12 : 6 }}>
            <CustomCard>
              <Stack spacing={2}>
                <Stack
                  direction={{ xs: "column", md: "row" }}
                  justifyContent="space-between"
                  alignItems={{ xs: "flex-start", md: "center" }}
                  spacing={1.5}
                >
                  <Stack spacing={0.25}>
                    <Typography variant="h4">{restaurant.name}</Typography>
                    <Typography color="text.secondary">{restaurant.address}</Typography>
                  </Stack>
                  <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap" useFlexGap>
                    <Chip label={`${restaurant.menu.length} món`} color="primary" variant="outlined" />
                    <CustomButton startIcon={<AddRoundedIcon />} onClick={() => handleOpenCreate(restaurant.id)}>
                      Thêm món
                    </CustomButton>
                  </Stack>
                </Stack>

                {restaurant.menu.length ? (
                  <Grid container spacing={2}>
                    {restaurant.menu.map((item) => (
                      <Grid key={item.id} size={{ xs: 12, xl: selectedRestaurant ? 6 : 12 }}>
                        <Box
                          sx={{
                            p: 2,
                            borderRadius: 2,
                            bgcolor: "rgba(248,250,255,0.92)",
                            border: "1px solid rgba(15,23,42,0.06)",
                            height: "100%",
                          }}
                        >
                          <Stack spacing={1.5}>
                            <Stack direction="row" spacing={1.5} alignItems="flex-start">
                              <MenuImage imageUrl={item.imageUrl} />
                              <Stack spacing={0.75} flex={1} minWidth={0}>
                                <Typography fontWeight={800} sx={{ lineHeight: 1.35 }}>
                                  {item.name}
                                </Typography>
                                <Typography color="text.secondary" sx={{ lineHeight: 1.55 }}>
                                  {item.description || "Chưa có mô tả món ăn."}
                                </Typography>
                                <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                                  <Chip label={item.category || "Chưa phân loại"} />
                                  <Chip
                                    label={item.isAvailable ? "Đang phục vụ" : "Tạm ẩn"}
                                    color={item.isAvailable ? "success" : "default"}
                                  />
                                  <Chip label={formatCurrency(item.price)} variant="outlined" />
                                </Stack>
                              </Stack>
                            </Stack>

                            <Stack
                              direction={{ xs: "column", sm: "row" }}
                              spacing={1}
                              justifyContent="flex-end"
                              alignItems={{ xs: "stretch", sm: "center" }}
                            >
                              <CustomButton
                                startIcon={<EditRoundedIcon />}
                                onClick={() => handleOpenEdit(restaurant.id, item)}
                              >
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
                  <Alert severity="info">Chi nhánh này chưa có món ăn nào.</Alert>
                )}
              </Stack>
            </CustomCard>
          </Grid>
        ))}
      </Grid>

      <CustomModal
        open={open}
        onClose={handleCloseModal}
        title={mode === "create" ? "Thêm món mới" : "Cập nhật món ăn"}
        width={680}
      >
        <Stack component="form" spacing={2} onSubmit={handleSubmit}>
          {error ? <Alert severity="error">{error}</Alert> : null}
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, md: 6 }}>
              <FormInput label="Tên món" name="name" value={form.name} onChange={handleChange} required />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <FormInput label="Danh mục" name="category" value={form.category} onChange={handleChange} />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <FormInput label="Giá" name="price" value={form.price} onChange={handleChange} required />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <FormInput
                select
                label="Trạng thái phục vụ"
                name="is_available"
                value={String(form.is_available)}
                onChange={handleChange}
              >
                <MenuItem value="true">Đang phục vụ</MenuItem>
                <MenuItem value="false">Tạm ẩn</MenuItem>
              </FormInput>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormInput
                multiline
                rows={3}
                label="Mô tả món ăn"
                name="description"
                value={form.description}
                onChange={handleChange}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormInput label="URL hình ảnh" name="image_url" value={form.image_url} onChange={handleChange} />
            </Grid>
          </Grid>
          <Stack direction="row" spacing={1.5}>
            <CustomButton type="submit" disabled={saving}>
              {saving ? "Đang lưu..." : mode === "create" ? "Thêm món" : "Lưu cập nhật"}
            </CustomButton>
            <CustomButton
              type="button"
              onClick={handleCloseModal}
              sx={{ background: "linear-gradient(135deg, #64748B 0%, #94A3B8 100%)" }}
            >
              Đóng
            </CustomButton>
          </Stack>
        </Stack>
      </CustomModal>
    </Stack>
  );
}

export default OwnerMenuPage;
