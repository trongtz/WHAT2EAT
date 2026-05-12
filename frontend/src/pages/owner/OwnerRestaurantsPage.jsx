import AddRoundedIcon from "@mui/icons-material/AddRounded";
import EditRoundedIcon from "@mui/icons-material/EditRounded";
import LocalPhoneRoundedIcon from "@mui/icons-material/LocalPhoneRounded";
import PlaceRoundedIcon from "@mui/icons-material/PlaceRounded";
import RestaurantMenuRoundedIcon from "@mui/icons-material/RestaurantMenuRounded";
import StarRoundedIcon from "@mui/icons-material/StarRounded";
import TableRestaurantRoundedIcon from "@mui/icons-material/TableRestaurantRounded";
import VisibilityRoundedIcon from "@mui/icons-material/VisibilityRounded";
import {
  Alert,
  Box,
  Checkbox,
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
import EmptyState from "../../components/EmptyState";
import FormInput from "../../components/FormInput";
import LoadingScreen from "../../components/LoadingScreen";
import SectionHeader from "../../components/SectionHeader";
import { useAuth } from "../../hooks/useAuth";
import { restaurantService } from "../../services/restaurantService";
import {
  formatDate,
  formatOpenHours,
  getPriceRangeLabel,
  getRestaurantStatusLabel,
  getStatusColor,
} from "../../utils/helpers";

const defaultOpenHoursTemplate = "08:00 - 22:00";
const OTHER_CUISINE_OPTION = "Khác";
const cuisineOptions = [
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
  OTHER_CUISINE_OPTION,
];

const defaultForm = {
  restaurantId: "",
  name: "",
  address: "",
  phone: "",
  description: "",
  latitude: "",
  longitude: "",
  cuisineSelections: [],
  cuisineOther: "",
  price_range: "mid",
  max_capacity: 10,
  imagesText: "",
  openHoursText: defaultOpenHoursTemplate,
};

const parseCuisineType = (value) => {
  const tokens = String(value || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);

  const selections = [];
  let otherText = "";

  tokens.forEach((token) => {
    if (cuisineOptions.includes(token) && token !== OTHER_CUISINE_OPTION) {
      selections.push(token);
      return;
    }

    if (token === OTHER_CUISINE_OPTION) {
      if (!selections.includes(OTHER_CUISINE_OPTION)) {
        selections.push(OTHER_CUISINE_OPTION);
      }
      return;
    }

    if (token.toLowerCase().startsWith("khác:")) {
      if (!selections.includes(OTHER_CUISINE_OPTION)) {
        selections.push(OTHER_CUISINE_OPTION);
      }
      otherText = token.slice(5).trim();
      return;
    }

    if (!selections.includes(OTHER_CUISINE_OPTION)) {
      selections.push(OTHER_CUISINE_OPTION);
    }
    otherText = token;
  });

  return {
    selections,
    otherText,
  };
};

const serializeCuisineType = (selections, otherText) => {
  const baseValues = selections.filter((item) => item !== OTHER_CUISINE_OPTION);

  if (!selections.includes(OTHER_CUISINE_OPTION)) {
    return baseValues.join(", ");
  }

  if (otherText.trim()) {
    return [...baseValues, `Khác: ${otherText.trim()}`].join(", ");
  }

  return [...baseValues, OTHER_CUISINE_OPTION].join(", ");
};

const getCuisineLabels = (value) => {
  const { selections, otherText } = parseCuisineType(value);

  if (!selections.length) {
    return [];
  }

  return selections.map((item) =>
    item === OTHER_CUISINE_OPTION && otherText ? `Khác: ${otherText}` : item
  );
};

const buildFormFromRestaurant = (restaurant) => {
  const cuisine = parseCuisineType(restaurant.cuisineType);

  return {
    restaurantId: restaurant.id,
    name: restaurant.name ?? "",
    address: restaurant.address ?? "",
    phone: restaurant.phone ?? "",
    description: restaurant.description ?? "",
    latitude: restaurant.latitude ?? "",
    longitude: restaurant.longitude ?? "",
    cuisineSelections: cuisine.selections,
    cuisineOther: cuisine.otherText,
    price_range: restaurant.priceRange ?? "mid",
    max_capacity: restaurant.maxCapacity || 10,
    imagesText: restaurant.images?.join("\n") ?? "",
    openHoursText: restaurant.openHours ?? defaultOpenHoursTemplate,
  };
};

const getRestaurantRatingLabel = (restaurant) =>
  Number(restaurant.reviewCount || 0) > 0
    ? `${Number(restaurant.averageRating || 0).toFixed(1)} sao`
    : "Không có đánh giá";

function RestaurantMetric({ label, value }) {
  return (
    <Box
      sx={{
        p: 1.4,
        borderRadius: 2,
        bgcolor: "rgba(248,250,255,0.92)",
        border: "1px solid rgba(15,23,42,0.06)",
      }}
    >
      <Typography color="text.secondary" sx={{ fontSize: "0.92rem" }}>
        {label}
      </Typography>
      <Box sx={{ mt: 0.35, fontWeight: 800, fontSize: "1.15rem", color: "text.primary" }}>{value}</Box>
    </Box>
  );
}

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
    const data = await restaurantService.getOwnerRestaurants(user.id);
    setRestaurants(data);
    setLoading(false);
  };

  useEffect(() => {
    loadData();
  }, [user.id]);

  const handleOpenCreate = () => {
    setMode("create");
    setForm(defaultForm);
    setError("");
    setOpen(true);
  };

  const handleOpenEdit = (restaurant) => {
    setMode("edit");
    setForm(buildFormFromRestaurant(restaurant));
    setError("");
    setOpen(true);
  };

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleCuisineChange = (event) => {
    const nextSelections = Array.isArray(event.target.value)
      ? event.target.value
      : String(event.target.value || "")
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean);

    setForm((prev) => ({
      ...prev,
      cuisineSelections: nextSelections,
      cuisineOther: nextSelections.includes(OTHER_CUISINE_OPTION) ? prev.cuisineOther : "",
    }));
  };

  const buildPayload = () => ({
    name: form.name,
    address: form.address,
    phone: form.phone,
    description: form.description,
    latitude: form.latitude,
    longitude: form.longitude,
    cuisine_type: serializeCuisineType(form.cuisineSelections, form.cuisineOther),
    price_range: form.price_range,
    max_capacity: Number(form.max_capacity),
    open_hours: form.openHoursText,
    images: form.imagesText
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean),
  });

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError("");

    if (
      form.cuisineSelections.includes(OTHER_CUISINE_OPTION) &&
      !form.cuisineOther.trim()
    ) {
      setSaving(false);
      setError("Bạn hãy nhập thêm nội dung cho mục Khác.");
      return;
    }

    try {
      const payload = buildPayload();
      if (mode === "create") {
        await restaurantService.createRestaurant(payload);
        setMessage("Đã gửi chi nhánh mới lên trang admin để duyệt.");
      } else {
        await restaurantService.updateRestaurant(form.restaurantId, payload);
        setMessage("Đã cập nhật thông tin chi nhánh.");
      }
      setOpen(false);
      await loadData();
    } catch (submitError) {
      setError(submitError.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <LoadingScreen message="Đang tải danh sách chi nhánh..." />;

  return (
    <Stack spacing={3}>
      <SectionHeader
        title="Quản lý chi nhánh nhà hàng"
        action={
          <CustomButton startIcon={<AddRoundedIcon />} onClick={handleOpenCreate}>
            Đăng ký chi nhánh
          </CustomButton>
        }
      />

      {message ? <Alert severity="success">{message}</Alert> : null}

      {!restaurants.length ? (
        <Stack spacing={2}>
          <EmptyState title="Trang chủ owner đang trống" />
          <CustomButton startIcon={<AddRoundedIcon />} onClick={handleOpenCreate} sx={{ alignSelf: "flex-start" }}>
            Tạo chi nhánh đầu tiên
          </CustomButton>
        </Stack>
      ) : (
        <Grid container spacing={3}>
          {restaurants.map((restaurant) => {
            const cuisineLabels = getCuisineLabels(restaurant.cuisineType);

            return (
              <Grid key={restaurant.id} size={{ xs: 12, xl: 6 }}>
                <CustomCard>
                  <Stack spacing={2}>
                    <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
                      <Box
                        sx={{
                          width: { xs: "100%", md: 184 },
                          height: 146,
                          borderRadius: 2,
                          flexShrink: 0,
                          background: restaurant.image
                            ? `linear-gradient(180deg, rgba(18,22,44,0.08), rgba(18,22,44,0.24)), url(${restaurant.image})`
                            : "linear-gradient(135deg, rgba(255,159,28,0.22), rgba(47,107,255,0.18))",
                          backgroundPosition: "center",
                          backgroundSize: "cover",
                          border: "1px solid rgba(15,23,42,0.06)",
                        }}
                      />

                      <Stack spacing={1.15} flex={1}>
                        <Typography variant="h4">{restaurant.name}</Typography>
                        <Typography color="text.secondary">{restaurant.address}</Typography>

                        <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                          {cuisineLabels.length ? (
                            cuisineLabels.map((label) => <Chip key={label} label={label} />)
                          ) : (
                            <Chip label="Chưa có loại ẩm thực" />
                          )}
                          <Chip label={getPriceRangeLabel(restaurant.priceRange)} variant="outlined" />
                          <Chip
                            label={getRestaurantStatusLabel(restaurant.status)}
                            color={getStatusColor(restaurant.status)}
                          />
                          <Chip
                            icon={<StarRoundedIcon sx={{ fontSize: 18 }} />}
                            label={getRestaurantRatingLabel(restaurant)}
                            variant="outlined"
                            color="warning"
                          />
                        </Stack>

                        <Stack direction="row" spacing={0.9} alignItems="center">
                          <LocalPhoneRoundedIcon sx={{ color: "text.secondary", fontSize: 18 }} />
                          <Typography color="text.secondary">{restaurant.phone || "Chưa cập nhật"}</Typography>
                        </Stack>
                      </Stack>
                    </Stack>

                    <Grid container spacing={1.5}>
                      <Grid size={{ xs: 12, sm: 6, lg: 3 }}>
                        <RestaurantMetric label="Ngày tạo" value={formatDate(restaurant.createdAt)} />
                      </Grid>
                      <Grid size={{ xs: 12, sm: 6, lg: 3 }}>
                        <RestaurantMetric label="Giờ mở cửa" value={formatOpenHours(restaurant.openHours)} />
                      </Grid>
                      <Grid size={{ xs: 12, sm: 6, lg: 3 }}>
                        <RestaurantMetric
                          label="Chỗ ngồi"
                          value={
                            <Stack direction="row" spacing={0.6} alignItems="center">
                              <TableRestaurantRoundedIcon sx={{ fontSize: 18 }} />
                              <span>{`${restaurant.availableCapacity || 0}/${restaurant.maxCapacity || 0}`}</span>
                            </Stack>
                          }
                        />
                      </Grid>
                    </Grid>

                    <Typography color="text.secondary">
                      {restaurant.description || "Chi nhánh này chưa có mô tả chi tiết."}
                    </Typography>

                    <Stack direction="row" spacing={1.25} flexWrap="wrap" useFlexGap>
                      <CustomButton
                        component={RouterLink}
                        to={`/chu-nha-hang/nha-hang/${restaurant.id}`}
                        startIcon={<VisibilityRoundedIcon />}
                      >
                        Xem chi tiết
                      </CustomButton>
                      <CustomButton
                        component={RouterLink}
                        to={`/chu-nha-hang/menu?restaurantId=${restaurant.id}&action=create`}
                        startIcon={<RestaurantMenuRoundedIcon />}
                        disabled={restaurant.status !== "APPROVED"}
                        sx={{ background: "linear-gradient(135deg, #2E8B57 0%, #57CC99 100%)" }}
                      >
                        Thêm món
                      </CustomButton>
                      <CustomButton
                        startIcon={<EditRoundedIcon />}
                        onClick={() => handleOpenEdit(restaurant)}
                        disabled={restaurant.status !== "APPROVED"}
                        sx={{ background: "linear-gradient(135deg, #64748B 0%, #94A3B8 100%)" }}
                      >
                        Sửa thông tin
                      </CustomButton>
                    </Stack>

                    {restaurant.status !== "APPROVED" ? (
                      <Alert severity={restaurant.status === "REJECTED" ? "error" : "info"} icon={<PlaceRoundedIcon />}>
                        {restaurant.status === "PENDING"
                          ? "Chi nhánh đang chờ admin duyệt. Sau khi duyệt bạn mới có thể sửa thông tin, quản lý menu và sức chứa đặt bàn."
                          : "Chi nhánh đã bị từ chối. Bạn có thể tạo chi nhánh mới hoặc cập nhật lại hồ sơ sau khi quy trình duyệt được mở rộng."}
                      </Alert>
                    ) : null}
                  </Stack>
                </CustomCard>
              </Grid>
            );
          })}
        </Grid>
      )}

      <CustomModal
        open={open}
        onClose={() => setOpen(false)}
        title={mode === "create" ? "Đăng ký chi nhánh mới" : "Cập nhật chi nhánh đã duyệt"}
        width={760}
      >
        <Stack component="form" spacing={2} onSubmit={handleSubmit}>
          {error ? <Alert severity="error">{error}</Alert> : null}

          <Grid container spacing={2}>
            <Grid size={{ xs: 12, md: 6 }}>
              <FormInput label="Tên chi nhánh" name="name" value={form.name} onChange={handleChange} required />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <FormInput
                select
                label="Loại ẩm thực"
                name="cuisineSelections"
                value={form.cuisineSelections}
                onChange={handleCuisineChange}
                SelectProps={{
                  multiple: true,
                  displayEmpty: true,
                  renderValue: (selected) => {
                    const labels = Array.isArray(selected)
                      ? selected.map((item) =>
                          item === OTHER_CUISINE_OPTION && form.cuisineOther.trim()
                            ? `Khác: ${form.cuisineOther.trim()}`
                            : item
                        )
                      : [];

                    return labels.length ? labels.join(", ") : "Chọn loại ẩm thực";
                  },
                }}
                helperText="Bạn có thể chọn nhiều loại ẩm thực."
              >
                {cuisineOptions.map((option) => (
                  <MenuItem key={option} value={option}>
                    <Checkbox checked={form.cuisineSelections.includes(option)} size="small" />
                    {option}
                  </MenuItem>
                ))}
              </FormInput>
            </Grid>
            {form.cuisineSelections.includes(OTHER_CUISINE_OPTION) ? (
              <Grid size={{ xs: 12 }}>
                <FormInput
                  label="Loại ẩm thực khác"
                  name="cuisineOther"
                  value={form.cuisineOther}
                  onChange={handleChange}
                  required
                />
              </Grid>
            ) : null}
            <Grid size={{ xs: 12, md: 6 }}>
              <FormInput label="Số điện thoại" name="phone" value={form.phone} onChange={handleChange} required />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <FormInput select label="Khoảng giá" name="price_range" value={form.price_range} onChange={handleChange}>
                <MenuItem value="cheap">Dưới 100k</MenuItem>
                <MenuItem value="mid">100k - 300k</MenuItem>
                <MenuItem value="expensive">Trên 300k</MenuItem>
              </FormInput>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormInput label="Địa chỉ" name="address" value={form.address} onChange={handleChange} required />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <FormInput
                type="number"
                label="Số bàn tối đa"
                name="max_capacity"
                value={form.max_capacity}
                onChange={handleChange}
                required
                inputProps={{ min: 1 }}
                helperText="Số bàn này sẽ dùng để tính bàn trống khi khách đặt bàn."
              />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <FormInput
                multiline
                rows={2}
                label="Giờ mở cửa"
                name="openHoursText"
                value={form.openHoursText}
                onChange={handleChange}
                helperText="Ví dụ: 08:00 - 22:00"
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormInput
                multiline
                rows={3}
                label="Mô tả"
                name="description"
                value={form.description}
                onChange={handleChange}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormInput
                multiline
                rows={3}
                label="Danh sách ảnh, mỗi dòng 1 URL"
                name="imagesText"
                value={form.imagesText}
                onChange={handleChange}
              />
            </Grid>
          </Grid>

          <Stack direction="row" spacing={1.5}>
            <CustomButton type="submit" disabled={saving}>
              {saving ? "Đang lưu..." : mode === "create" ? "Gửi admin duyệt" : "Lưu cập nhật"}
            </CustomButton>
            <CustomButton
              type="button"
              onClick={() => setOpen(false)}
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
