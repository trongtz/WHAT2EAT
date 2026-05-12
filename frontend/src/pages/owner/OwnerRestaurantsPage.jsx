import AddRoundedIcon from "@mui/icons-material/AddRounded";
import EditRoundedIcon from "@mui/icons-material/EditRounded";
import LocalPhoneRoundedIcon from "@mui/icons-material/LocalPhoneRounded";
import StarRoundedIcon from "@mui/icons-material/StarRounded";
import VisibilityRoundedIcon from "@mui/icons-material/VisibilityRounded";
import {
  Alert,
  Box,
  Chip,
  Grid,
  MenuItem,
  Stack,
  Typography,
} from "@mui/material";
import { useEffect, useMemo, useState } from "react";
import { Link as RouterLink } from "react-router-dom";
import CustomButton from "../../components/CustomButton";
import CustomCard from "../../components/CustomCard";
import CustomModal from "../../components/CustomModal";
import EmptyState from "../../components/EmptyState";
import FormInput from "../../components/FormInput";
import LoadingScreen from "../../components/LoadingScreen";
import SectionHeader from "../../components/SectionHeader";
import { useAuth } from "../../hooks/useAuth";
import { restaurantService } from "../../services/restaurantService";
import { formatOpenHours, getPriceRangeLabel, getRestaurantStatusLabel } from "../../utils/helpers";

const CUISINE_OPTIONS = [
  "Món ăn Thái Lan",
  "Món ăn miền Tây",
  "Món lẩu",
  "Món nướng",
  "Món ăn Nhật Bản",
  "Món ăn Hàn Quốc",
  "Món Cajun",
  "Quán ăn nhỏ",
  "Món ăn nhanh",
  "Món ăn Việt Nam",
  "Quán bia",
  "Bít tết",
  "Khác",
];

const defaultForm = {
  restaurantId: "",
  name: "",
  address: "",
  phone: "",
  description: "",
  price_range: "",
  open_hours: "",
  max_capacity: "",
  imagesText: "",
  selectedCuisines: [],
  customCuisine: "",
};

const normalizeCuisineSelection = (value) =>
  String(value || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);

const toCuisineText = (selectedCuisines, customCuisine) =>
  selectedCuisines
    .flatMap((item) => {
      if (item === "Khác") {
        return customCuisine.trim() ? [customCuisine.trim()] : [];
      }
      return [item];
    })
    .join(", ");

function OwnerRestaurantsPage() {
  const { user } = useAuth();
  const [restaurants, setRestaurants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState("create");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [form, setForm] = useState(defaultForm);

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await restaurantService.getOwnerRestaurants(user.id);
      setRestaurants(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [user.id]);

  const approvedRestaurants = useMemo(
    () => restaurants.filter((restaurant) => restaurant.status === "APPROVED"),
    [restaurants]
  );

  const handleClose = () => {
    setOpen(false);
    setForm(defaultForm);
  };

  const handleOpenCreate = () => {
    setMode("create");
    setForm(defaultForm);
    setOpen(true);
  };

  const handleOpenEdit = (restaurant) => {
    const cuisineValues = normalizeCuisineSelection(restaurant.cuisineType);
    const selectedKnown = cuisineValues.filter((item) => CUISINE_OPTIONS.includes(item));
    const customValues = cuisineValues.filter((item) => !CUISINE_OPTIONS.includes(item));
    setMode("edit");
    setForm({
      restaurantId: restaurant.id,
      name: restaurant.name,
      address: restaurant.address,
      phone: restaurant.phone,
      description: restaurant.description || "",
      price_range: restaurant.priceRange || "",
      open_hours: restaurant.openHours || "",
      max_capacity: restaurant.maxCapacity || "",
      imagesText: (restaurant.images || []).join("\n"),
      selectedCuisines: customValues.length ? [...selectedKnown, "Khác"] : selectedKnown,
      customCuisine: customValues.join(", "),
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
    setError("");

    const payload = {
      name: form.name,
      address: form.address,
      phone: form.phone,
      description: form.description,
      price_range: form.price_range,
      open_hours: form.open_hours,
      max_capacity: Number(form.max_capacity),
      images: form.imagesText
        .split(/\r?\n/)
        .map((item) => item.trim())
        .filter(Boolean),
      cuisine_type: toCuisineText(form.selectedCuisines, form.customCuisine),
    };

    try {
      if (mode === "create") {
        await restaurantService.createRestaurant(payload);
        setMessage("Đã gửi hồ sơ chi nhánh lên admin để duyệt.");
      } else {
        await restaurantService.updateRestaurant(form.restaurantId, payload);
        setMessage("Đã cập nhật thông tin chi nhánh.");
      }
      handleClose();
      await loadData();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <LoadingScreen message="Đang tải danh sách chi nhánh..." />;

  return (
    <Stack spacing={3}>
      <SectionHeader
        title="Nhà hàng"
        action={
          <CustomButton startIcon={<AddRoundedIcon />} onClick={handleOpenCreate}>
            Đăng ký chi nhánh
          </CustomButton>
        }
      />

      {message ? <Alert severity="success">{message}</Alert> : null}
      {error ? <Alert severity="error">{error}</Alert> : null}

      {restaurants.length ? (
        <Grid container spacing={3}>
          {restaurants.map((restaurant) => (
            <Grid key={restaurant.id} size={{ xs: 12 }}>
              <CustomCard>
                <Stack spacing={2}>
                  <Stack direction={{ xs: "column", lg: "row" }} spacing={2.5}>
                    <Box
                      sx={{
                        width: { xs: "100%", lg: 280 },
                        minWidth: { lg: 280 },
                        height: 180,
                        borderRadius: 2,
                        overflow: "hidden",
                        background: restaurant.image
                          ? `linear-gradient(180deg, rgba(18,22,44,0.05), rgba(18,22,44,0.18)), url(${restaurant.image})`
                          : "linear-gradient(135deg, color-mix(in srgb, var(--app-primary) 20%, white), color-mix(in srgb, var(--app-secondary) 18%, white))",
                        backgroundSize: "cover",
                        backgroundPosition: "center",
                      }}
                    />

                    <Stack spacing={1.2} flex={1}>
                      <Typography variant="h3">{restaurant.name}</Typography>
                      <Typography color="text.secondary">{restaurant.address}</Typography>

                      <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                        {normalizeCuisineSelection(restaurant.cuisineType).map((item) => (
                          <Chip key={item} label={item} />
                        ))}
                        <Chip label={getPriceRangeLabel(restaurant.priceRange)} variant="outlined" />
                        <Chip
                          label={getRestaurantStatusLabel(restaurant.status)}
                          color={restaurant.status === "APPROVED" ? "success" : restaurant.status === "REJECTED" ? "error" : "warning"}
                        />
                        <Chip
                          icon={<StarRoundedIcon sx={{ color: "#F6B500 !important" }} />}
                          label={
                            restaurant.averageRating > 0
                              ? `${restaurant.averageRating.toFixed(1)}`
                              : "Không có đánh giá"
                          }
                          sx={{
                            bgcolor: "color-mix(in srgb, var(--app-primary) 10%, white)",
                            color: "var(--app-primary)",
                          }}
                        />
                      </Stack>

                      <Stack direction="row" spacing={1} alignItems="center">
                        <LocalPhoneRoundedIcon sx={{ color: "var(--app-secondary)" }} />
                        <Typography color="text.secondary">{restaurant.phone}</Typography>
                      </Stack>

                      <Grid container spacing={2}>
                        <Grid size={{ xs: 6, md: 3 }}>
                          <Typography color="text.secondary">Ngày tạo</Typography>
                          <Typography fontWeight={800}>{new Date(restaurant.createdAt).toLocaleDateString("vi-VN")}</Typography>
                        </Grid>
                        <Grid size={{ xs: 6, md: 3 }}>
                          <Typography color="text.secondary">Giờ mở cửa</Typography>
                          <Typography fontWeight={800}>{formatOpenHours(restaurant.openHours)}</Typography>
                        </Grid>
                        <Grid size={{ xs: 6, md: 3 }}>
                          <Typography color="text.secondary">Chỗ ngồi</Typography>
                          <Typography fontWeight={800}>
                            {restaurant.availableCapacity}/{restaurant.maxCapacity}
                          </Typography>
                        </Grid>
                        <Grid size={{ xs: 6, md: 3 }}>
                          <Typography color="text.secondary">Số món ăn</Typography>
                          <Typography fontWeight={800}>{restaurant.menu.length}</Typography>
                        </Grid>
                      </Grid>

                      <Typography color="text.secondary">
                        {restaurant.description || "Chưa có mô tả chi tiết cho chi nhánh này."}
                      </Typography>
                    </Stack>
                  </Stack>

                  <Stack direction="row" spacing={1.25} flexWrap="wrap" useFlexGap>
                    <CustomButton
                      component={RouterLink}
                      to={`/chu-nha-hang/nha-hang/${restaurant.id}`}
                      startIcon={<VisibilityRoundedIcon />}
                    >
                      Xem chi tiết
                    </CustomButton>
                    {restaurant.status === "APPROVED" ? (
                      <>
                        <CustomButton
                          startIcon={<EditRoundedIcon />}
                          onClick={() => handleOpenEdit(restaurant)}
                          sx={{ background: "linear-gradient(135deg, #64748B 0%, #94A3B8 100%)" }}
                        >
                          Sửa thông tin
                        </CustomButton>
                        <CustomButton
                          component={RouterLink}
                          to={`/chu-nha-hang/menu?restaurantId=${restaurant.id}&focus=create`}
                        >
                          Thêm món
                        </CustomButton>
                      </>
                    ) : null}
                  </Stack>
                </Stack>
              </CustomCard>
            </Grid>
          ))}
        </Grid>
      ) : (
        <EmptyState title="Chưa có chi nhánh nào" description="" />
      )}

      <CustomModal
        open={open}
        onClose={handleClose}
        title={mode === "create" ? "Đăng ký chi nhánh mới" : "Cập nhật chi nhánh đã duyệt"}
        width={1040}
      >
        <Stack component="form" spacing={2} onSubmit={handleSubmit}>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, md: 6 }}>
              <FormInput label="Tên chi nhánh" name="name" value={form.name} onChange={handleChange} required />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <FormInput
                select
                label="Loại ẩm thực"
                name="selectedCuisines"
                value={form.selectedCuisines}
                onChange={handleChange}
                SelectProps={{ multiple: true }}
              >
                {CUISINE_OPTIONS.map((option) => (
                  <MenuItem key={option} value={option}>
                    {option}
                  </MenuItem>
                ))}
              </FormInput>
            </Grid>
            {form.selectedCuisines.includes("Khác") ? (
              <Grid size={{ xs: 12 }}>
                <FormInput
                  label="Ẩm thực khác"
                  name="customCuisine"
                  value={form.customCuisine}
                  onChange={handleChange}
                />
              </Grid>
            ) : null}
            <Grid size={{ xs: 12, md: 6 }}>
              <FormInput label="Số điện thoại" name="phone" value={form.phone} onChange={handleChange} required />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <FormInput select label="Khoảng giá" name="price_range" value={form.price_range} onChange={handleChange}>
                <MenuItem value="">Chọn khoảng giá</MenuItem>
                <MenuItem value="cheap">Dưới 100k</MenuItem>
                <MenuItem value="mid">100k - 300k</MenuItem>
                <MenuItem value="expensive">Trên 300k</MenuItem>
              </FormInput>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormInput label="Địa chỉ" name="address" value={form.address} onChange={handleChange} required />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormInput multiline rows={4} label="Mô tả" name="description" value={form.description} onChange={handleChange} />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormInput
                multiline
                rows={4}
                label="Danh sách ảnh, mỗi dòng 1 URL"
                name="imagesText"
                value={form.imagesText}
                onChange={handleChange}
              />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <FormInput label="Giờ mở cửa" name="open_hours" value={form.open_hours} onChange={handleChange} helperText="Ví dụ: 08:00 - 22:00" />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <FormInput
                type="number"
                label="Số bàn tối đa"
                name="max_capacity"
                value={form.max_capacity}
                onChange={handleChange}
                required
              />
            </Grid>
          </Grid>

          <Stack direction="row" spacing={1.5}>
            <CustomButton type="submit" disabled={saving}>
              {saving ? "Đang lưu..." : mode === "create" ? "Gửi admin duyệt" : "Lưu cập nhật"}
            </CustomButton>
            <CustomButton
              type="button"
              onClick={handleClose}
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

export default OwnerRestaurantsPage;
