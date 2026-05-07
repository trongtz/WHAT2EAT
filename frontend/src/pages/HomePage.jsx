import AccessTimeRoundedIcon from "@mui/icons-material/AccessTimeRounded";
import AutoAwesomeRoundedIcon from "@mui/icons-material/AutoAwesomeRounded";
import FmdGoodRoundedIcon from "@mui/icons-material/FmdGoodRounded";
import MyLocationRoundedIcon from "@mui/icons-material/MyLocationRounded";
import SearchRoundedIcon from "@mui/icons-material/SearchRounded";
import StarRoundedIcon from "@mui/icons-material/StarRounded";
import TuneRoundedIcon from "@mui/icons-material/TuneRounded";
import {
  alpha,
  Box,
  Button,
  Chip,
  Grid,
  InputAdornment,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import L from "leaflet";
import { useEffect, useMemo, useState } from "react";
import { MapContainer, Marker, Popup, TileLayer, useMap } from "react-leaflet";
import { Link as RouterLink } from "react-router-dom";
import LoadingScreen from "../components/LoadingScreen";
import RestaurantCard from "../components/RestaurantCard";
import SectionHeader from "../components/SectionHeader";
import { restaurantService } from "../services/restaurantService";

const restaurantLocations = {
  1: [10.7769, 106.7009],
  2: [10.7991, 106.6918],
  3: [10.7624, 106.6981],
  4: [10.7933, 106.6884],
};

const statusColors = {
  "Còn chỗ": "#22B573",
  "Sắp đầy": "#F5A623",
  "Hết chỗ": "#E15B64",
};

const insightItems = [
  { label: "Gợi ý theo vị trí", value: "12+", icon: FmdGoodRoundedIcon },
  { label: "Nhà hàng nổi bật", value: "Top rated", icon: StarRoundedIcon },
  { label: "Đặt bàn siêu nhanh", value: "< 30s", icon: AccessTimeRoundedIcon },
];

const createMarkerIcon = (color) =>
  L.divIcon({
    className: "",
    html: `<div class="smartfood-marker" style="background:${color}; position:relative;"></div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 24],
    popupAnchor: [0, -22],
  });

function MapFocusController({ center }) {
  const map = useMap();

  useEffect(() => {
    if (center) {
      map.flyTo(center, 15, { duration: 0.8 });
    }
  }, [center, map]);

  return null;
}

function HomePage() {
  const [restaurants, setRestaurants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [keyword, setKeyword] = useState("");
  const [selectedId, setSelectedId] = useState(1);
  const [focusCenter, setFocusCenter] = useState([10.7769, 106.7009]);
  const [locationPending, setLocationPending] = useState(false);

  useEffect(() => {
    const fetchRestaurants = async () => {
      const data = await restaurantService.getRestaurants();
      setRestaurants(data);
      setLoading(false);
    };

    fetchRestaurants();
  }, []);

  const featuredRestaurants = useMemo(() => restaurants.filter((item) => item.featured), [restaurants]);

  const filteredRestaurants = useMemo(() => {
    const normalized = keyword.trim().toLowerCase();
    if (!normalized) return featuredRestaurants;

    return featuredRestaurants.filter(
      (item) =>
        item.name.toLowerCase().includes(normalized) ||
        item.address.toLowerCase().includes(normalized) ||
        item.category.toLowerCase().includes(normalized)
    );
  }, [featuredRestaurants, keyword]);

  useEffect(() => {
    if (filteredRestaurants.length && !filteredRestaurants.some((item) => item.id === selectedId)) {
      setSelectedId(filteredRestaurants[0].id);
    }
  }, [filteredRestaurants, selectedId]);

  const selectedRestaurant =
    filteredRestaurants.find((item) => item.id === selectedId) || filteredRestaurants[0];

  useEffect(() => {
    if (selectedRestaurant) {
      setFocusCenter(restaurantLocations[selectedRestaurant.id] || [10.7769, 106.7009]);
    }
  }, [selectedRestaurant]);

  const handleLocateMe = () => {
    if (!navigator.geolocation) return;

    setLocationPending(true);
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        setFocusCenter([coords.latitude, coords.longitude]);
        setLocationPending(false);
      },
      () => {
        setLocationPending(false);
      },
      { enableHighAccuracy: true, timeout: 6000 }
    );
  };

  const heroViewportHeight = {
    xs: "min(68svh, 560px)",
    md: "calc(100svh - 190px)",
    lg: "calc(100svh - 170px)",
  };

  return (
    <Stack spacing={4.5}>
      <Box className="glass-panel" sx={{ p: { xs: 1.5, md: 2 }, borderRadius: 2.5 }}>
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, lg: 8.6 }}>
            <Box
              sx={{
                position: "relative",
                overflow: "hidden",
                borderRadius: 2.5,
                height: heroViewportHeight,
                border: "1px solid rgba(74,144,226,0.12)",
                backgroundColor: "#EAF3FF",
              }}
            >
              <MapContainer
                center={[10.7769, 106.7009]}
                zoom={14}
                scrollWheelZoom
                attributionControl={false}
                style={{ height: "100%", width: "100%" }}
              >
                <TileLayer
                  attribution="Tiles © Esri — Source: Esri, Maxar, Earthstar Geographics, and the GIS User Community"
                  url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                />

                <MapFocusController center={focusCenter} />

                {filteredRestaurants.map((restaurant) => {
                  const position = restaurantLocations[restaurant.id];
                  if (!position) return null;

                  return (
                    <Marker
                      key={restaurant.id}
                      position={position}
                      icon={createMarkerIcon(statusColors[restaurant.status] || "#22B573")}
                      eventHandlers={{ click: () => setSelectedId(restaurant.id) }}
                    >
                      <Popup>
                        <strong>{restaurant.name}</strong>
                        <br />
                        {restaurant.address}
                      </Popup>
                    </Marker>
                  );
                })}
              </MapContainer>

              <Stack spacing={1} sx={{ position: "absolute", top: 14, left: 14, right: 14, zIndex: 500 }}>
                <TextField
                  placeholder="Tìm món, nhà hàng hoặc khu vực bạn muốn ăn..."
                  value={keyword}
                  onChange={(event) => setKeyword(event.target.value)}
                  sx={{
                    maxWidth: 340,
                    "& .MuiOutlinedInput-root": {
                      minHeight: 42,
                      fontSize: "0.88rem",
                      bgcolor: "rgba(255,255,255,0.98)",
                      boxShadow: "0 18px 34px rgba(15,23,42,0.12)",
                    },
                  }}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <SearchRoundedIcon sx={{ color: "#4A90E2", fontSize: 20 }} />
                      </InputAdornment>
                    ),
                    endAdornment: (
                      <InputAdornment position="end">
                        <TuneRoundedIcon sx={{ color: "#667085", fontSize: 20 }} />
                      </InputAdornment>
                    ),
                  }}
                />

                <Stack direction={{ xs: "column", sm: "row" }} spacing={0.8}>
                  <Button
                    onClick={handleLocateMe}
                    startIcon={<MyLocationRoundedIcon sx={{ fontSize: 20 }} />}
                    disabled={locationPending}
                    sx={{
                      alignSelf: "flex-start",
                      minHeight: 38,
                      px: 1.35,
                      py: 0.45,
                      fontSize: "0.88rem",
                      bgcolor: "rgba(255,255,255,0.96)",
                      color: "secondary.main",
                      boxShadow: "0 16px 30px rgba(15,23,42,0.10)",
                      "&:hover": {
                        bgcolor: "white",
                        transform: "translateY(-1px)",
                      },
                    }}
                  >
                    {locationPending ? "Đang lấy vị trí..." : "Vị trí của tôi"}
                  </Button>
                </Stack>
              </Stack>
            </Box>
          </Grid>

          <Grid size={{ xs: 12, lg: 3.4 }}>
            <Stack
              spacing={1.5}
              sx={{
                height: { xs: "auto", lg: "calc(100svh - 170px)" },
                maxHeight: { xs: "none", lg: "calc(100svh - 170px)" },
                overflowY: "auto",
                pr: 0.5,
              }}
            >
              {filteredRestaurants.map((restaurant) => {
                const isActive = selectedId === restaurant.id;

                return (
                  <Box
                    key={restaurant.id}
                    onClick={() => setSelectedId(restaurant.id)}
                    sx={{
                      p: 1.25,
                      borderRadius: 2.5,
                      cursor: "pointer",
                      bgcolor: "rgba(255,255,255,0.94)",
                      border: isActive ? "1px solid rgba(255,138,42,0.22)" : "1px solid rgba(15,23,42,0.06)",
                      boxShadow: isActive ? "0 24px 42px rgba(255, 140, 64, 0.14)" : "0 14px 26px rgba(15,23,42,0.06)",
                      transition: "all 0.24s ease",
                      "&:hover": {
                        transform: "translateY(-2px)",
                        boxShadow: "0 22px 36px rgba(15,23,42,0.10)",
                      },
                    }}
                  >
                    <Stack spacing={1.15}>
                      <Box
                        sx={{
                          width: "100%",
                          height: { xs: 160, xl: 176 },
                          borderRadius: 2,
                          overflow: "hidden",
                          backgroundImage: `linear-gradient(180deg, rgba(8,15,28,0.02), rgba(8,15,28,0.22)), url(${restaurant.image})`,
                          backgroundSize: "cover",
                          backgroundPosition: "center",
                        }}
                      />

                      <Stack spacing={0.65}>
                        <Stack direction="row" justifyContent="space-between" spacing={1} alignItems="flex-start">
                          <Typography variant="h4" sx={{ fontSize: "1.02rem" }}>
                            {restaurant.name}
                          </Typography>
                          <Chip
                            size="small"
                            icon={<StarRoundedIcon sx={{ color: "#F6B500 !important" }} />}
                            label={restaurant.rating}
                            sx={{ bgcolor: alpha("#22B573", 0.1), color: "#169A52" }}
                          />
                        </Stack>

                        <Typography color="text.secondary" sx={{ fontSize: "0.92rem" }}>
                          {restaurant.category} • {restaurant.address}
                        </Typography>

                        <Stack direction="row" spacing={1} alignItems="center" justifyContent="space-between">
                          <Stack direction="row" spacing={0.6} alignItems="center">
                            <FmdGoodRoundedIcon sx={{ fontSize: 17, color: "#4A90E2" }} />
                            <Typography fontWeight={700} sx={{ color: "#4A90E2", fontSize: "0.92rem" }}>
                              {restaurant.distance}
                            </Typography>
                          </Stack>
                          <Typography sx={{ color: "primary.main", fontWeight: 800 }}>
                            {restaurant.averagePrice
                              ? `${Math.round(restaurant.averagePrice / 1000)}k`
                              : restaurant.priceRange}
                          </Typography>
                        </Stack>
                      </Stack>
                    </Stack>
                  </Box>
                );
              })}
            </Stack>
          </Grid>
        </Grid>
      </Box>

      <SectionHeader
        eyebrow="Curated picks"
        title="Danh sách nổi bật hôm nay"
        description="Ưu tiên hình ảnh hấp dẫn, đánh giá tốt và khoảng cách tiện lợi để bạn chọn quán nhanh hơn."
      />

      {loading ? (
        <LoadingScreen />
      ) : (
        <Grid container spacing={3}>
          {featuredRestaurants.map((restaurant) => (
            <Grid key={restaurant.id} size={{ xs: 12, md: 6, xl: 4 }}>
              <RestaurantCard
                restaurant={restaurant}
                action={
                  <Chip
                    component={RouterLink}
                    to={`/nha-hang/${restaurant.id}`}
                    clickable
                    label="Xem chi tiết"
                    sx={{
                      px: 1.2,
                      bgcolor: "rgba(255, 138, 42, 0.12)",
                      color: "primary.main",
                    }}
                  />
                }
              />
            </Grid>
          ))}
        </Grid>
      )}

      <Box
        sx={{
          px: { xs: 2.2, md: 4.5 },
          py: { xs: 3, md: 4.25 },
          borderRadius: 2.5,
          position: "relative",
          overflow: "hidden",
          background:
            "linear-gradient(135deg, rgba(255,122,24,0.12) 0%, rgba(255,179,71,0.08) 34%, rgba(74,144,226,0.08) 100%)",
          border: "1px solid rgba(255,255,255,0.75)",
          boxShadow: "0 24px 64px rgba(15, 23, 42, 0.08)",
        }}
      >
        <Box
          sx={{
            position: "absolute",
            width: 280,
            height: 280,
            top: -120,
            right: -80,
            borderRadius: "50%",
            background: "radial-gradient(circle, rgba(255,179,71,0.42), transparent 68%)",
          }}
        />

        <Grid container spacing={3} alignItems="center">
          <Grid size={{ xs: 12, lg: 7 }}>
            <Stack spacing={2.1}>
              <Chip
                icon={<AutoAwesomeRoundedIcon />}
                label="Bản đồ ẩm thực cá nhân hóa"
                sx={{
                  alignSelf: "flex-start",
                  bgcolor: "rgba(255,255,255,0.8)",
                  color: "primary.main",
                }}
              />
              <Typography variant="h1" sx={{ maxWidth: 720 }}>
                WHAT2EAT giúp bạn tìm quán ngon gần mình theo cách tinh tế hơn.
              </Typography>
              <Typography color="text.secondary" sx={{ maxWidth: 620, fontSize: "1.05rem" }}>
                Khám phá nhà hàng bằng bản đồ trực quan, ảnh món ăn nổi bật và gợi ý thông minh để
                mỗi quyết định ăn gì đều nhanh, đẹp mắt và đáng tin.
              </Typography>

              <Stack direction={{ xs: "column", sm: "row" }} spacing={1.4} pt={0.5}>
                <Button
                  component={RouterLink}
                  to="/tim-kiem"
                  variant="contained"
                  startIcon={<SearchRoundedIcon />}
                  sx={{
                    px: 2.8,
                    backgroundColor: "var(--app-primary)",
                    backgroundImage:
                      "linear-gradient(135deg, var(--app-primary) 0%, var(--app-primary-light) 100%)",
                    boxShadow:
                      "0 18px 36px color-mix(in srgb, var(--app-primary) 24%, transparent)",
                  }}
                >
                  Khám phá ngay
                </Button>
                <Button
                  onClick={handleLocateMe}
                  variant="outlined"
                  startIcon={<MyLocationRoundedIcon />}
                  sx={{
                    px: 2.6,
                    borderColor: "rgba(74,144,226,0.24)",
                    color: "secondary.main",
                    bgcolor: "rgba(255,255,255,0.72)",
                  }}
                >
                  Vị trí của tôi
                </Button>
              </Stack>
            </Stack>
          </Grid>

          <Grid size={{ xs: 12, lg: 5 }}>
            <Stack direction={{ xs: "column", sm: "row", lg: "column" }} spacing={1.5}>
              {insightItems.map((item) => {
                const Icon = item.icon;

                return (
                  <Stack
                    key={item.label}
                    direction="row"
                    spacing={1.5}
                    alignItems="center"
                    sx={{
                      p: 2,
                      borderRadius: 2.5,
                      bgcolor: "rgba(255,255,255,0.78)",
                      border: "1px solid rgba(255,255,255,0.68)",
                    }}
                  >
                    <Box
                      sx={{
                        width: 48,
                        height: 48,
                        borderRadius: 1.75,
                        display: "grid",
                        placeItems: "center",
                        background: "linear-gradient(135deg, rgba(255,122,24,0.18), rgba(74,144,226,0.14))",
                      }}
                    >
                      <Icon sx={{ color: item.icon === StarRoundedIcon ? "#22B573" : "#4A90E2" }} />
                    </Box>
                    <Box>
                      <Typography sx={{ fontWeight: 800 }}>{item.value}</Typography>
                      <Typography sx={{ color: "text.secondary", fontSize: "0.92rem" }}>
                        {item.label}
                      </Typography>
                    </Box>
                  </Stack>
                );
              })}
            </Stack>
          </Grid>
        </Grid>
      </Box>
    </Stack>
  );
}

export default HomePage;
