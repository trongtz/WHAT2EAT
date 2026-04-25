import FmdGoodRoundedIcon from "@mui/icons-material/FmdGoodRounded";
import MyLocationRoundedIcon from "@mui/icons-material/MyLocationRounded";
import SearchRoundedIcon from "@mui/icons-material/SearchRounded";
import StarRoundedIcon from "@mui/icons-material/StarRounded";
import TuneRoundedIcon from "@mui/icons-material/TuneRounded";
import {
  Box,
  Chip,
  Grid,
  IconButton,
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
  "Còn chỗ": "#15C39A",
  "Sắp đầy": "#F59E0B",
  "Hết chỗ": "#EF4444",
};

const legendItems = [
  { label: "Còn chỗ", color: "#15C39A" },
  { label: "Sắp đầy", color: "#F59E0B" },
  { label: "Đặt trước", color: "#EF4444" },
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

  useEffect(() => {
    const fetchRestaurants = async () => {
      const data = await restaurantService.getRestaurants();
      setRestaurants(data);
      setLoading(false);
    };
    fetchRestaurants();
  }, []);

  const featuredRestaurants = useMemo(
    () => restaurants.filter((item) => item.featured),
    [restaurants]
  );

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

  const selectedCenter = selectedRestaurant
    ? restaurantLocations[selectedRestaurant.id] || [10.7769, 106.7009]
    : [10.7769, 106.7009];

  return (
    <Stack spacing={4}>
      <Box
        className="glass-panel"
        sx={{
          borderRadius: 2,
          p: { xs: 1.5, md: 2 },
          background:
            "linear-gradient(180deg, rgba(255,255,255,0.96) 0%, rgba(247,250,255,0.93) 100%)",
        }}
      >
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, lg: 9 }}>
            <Box
              sx={{
                position: "relative",
                overflow: "hidden",
                borderRadius: 2,
                height: { xs: 520, md: 640 },
                border: "1px solid rgba(47,107,255,0.08)",
                backgroundColor: "#EAF3FF",
              }}
            >
              <MapContainer
                center={[10.7769, 106.7009]}
                zoom={14}
                scrollWheelZoom
                style={{ height: "100%", width: "100%" }}
              >
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/">CARTO</a>'
                  url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
                />

                <MapFocusController center={selectedCenter} />

                {filteredRestaurants.map((restaurant) => {
                  const position = restaurantLocations[restaurant.id];
                  if (!position) return null;
                  const markerColor = statusColors[restaurant.status] || "#15C39A";

                  return (
                    <Marker
                      key={restaurant.id}
                      position={position}
                      icon={createMarkerIcon(markerColor)}
                      eventHandlers={{
                        click: () => setSelectedId(restaurant.id),
                      }}
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

              <Box sx={{ position: "absolute", top: 18, left: 18, zIndex: 500 }}>
                <TextField
                  placeholder="Tìm món, nhà hàng..."
                  value={keyword}
                  onChange={(event) => setKeyword(event.target.value)}
                  sx={{
                    width: { xs: 280, md: 340 },
                      "& .MuiOutlinedInput-root": {
                        borderRadius: 2,
                      bgcolor: "rgba(255,255,255,0.98)",
                      boxShadow: "0 16px 30px rgba(28,36,64,0.12)",
                    },
                  }}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <SearchRoundedIcon />
                      </InputAdornment>
                    ),
                    endAdornment: (
                      <InputAdornment position="end">
                        <TuneRoundedIcon />
                      </InputAdornment>
                    ),
                  }}
                />
              </Box>

              <Stack
                direction="row"
                spacing={1}
                sx={{
                  position: "absolute",
                  left: 18,
                  bottom: 18,
                  zIndex: 500,
                  px: 2,
                  py: 1.25,
                  borderRadius: 2,
                  bgcolor: "rgba(255,255,255,0.96)",
                  boxShadow: "0 16px 30px rgba(28,36,64,0.12)",
                }}
              >
                {legendItems.map((item) => (
                  <Stack key={item.label} direction="row" spacing={1} alignItems="center">
                    <Box sx={{ width: 10, height: 10, borderRadius: "50%", bgcolor: item.color }} />
                    <Typography fontSize="0.9rem">{item.label}</Typography>
                  </Stack>
                ))}
              </Stack>

              <Stack
                direction="row"
                spacing={1}
                sx={{
                  position: "absolute",
                  left: 18,
                  top: 86,
                  zIndex: 500,
                  px: 1.75,
                  py: 1,
                  borderRadius: 2,
                  bgcolor: "rgba(255,255,255,0.96)",
                  boxShadow: "0 16px 30px rgba(28,36,64,0.12)",
                }}
              >
                <MyLocationRoundedIcon color="primary" />
                <Typography fontWeight={600}>Vị trí của tôi</Typography>
              </Stack>

              <Box
                sx={{
                  position: "absolute",
                  top: 118,
                  right: 24,
                  zIndex: 500,
                  px: 2,
                  py: 1.1,
                  borderRadius: 2,
                  bgcolor: "rgba(255,255,255,0.97)",
                  boxShadow: "0 16px 30px rgba(28,36,64,0.12)",
                }}
              >
                <Typography fontWeight={700} color="text.secondary">
                  Đang tìm kiếm nhà hàng phù hợp...
                </Typography>
              </Box>
            </Box>
          </Grid>

          <Grid size={{ xs: 12, lg: 3 }}>
            <Stack
              spacing={1.5}
              sx={{
                height: { xs: "auto", lg: 640 },
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
                      p: 1.5,
                      borderRadius: 2,
                      cursor: "pointer",
                      bgcolor: "rgba(255,255,255,0.96)",
                      border: isActive
                        ? "1px solid rgba(47,107,255,0.3)"
                        : "1px solid rgba(47,107,255,0.08)",
                      boxShadow: isActive
                        ? "0 18px 36px rgba(47,107,255,0.16)"
                        : "0 12px 24px rgba(28,36,64,0.06)",
                      transition: "all 0.2s ease",
                    }}
                  >
                    <Stack direction="row" spacing={1.25}>
                      <Box
                        sx={{
                          width: 104,
                          height: 104,
                          borderRadius: 2,
                          flexShrink: 0,
                          backgroundImage: `url(${restaurant.image})`,
                          backgroundSize: "cover",
                          backgroundPosition: "center",
                        }}
                      />

                      <Stack spacing={0.6} minWidth={0}>
                        <Typography variant="h4" sx={{ fontSize: "1.05rem" }}>
                          {restaurant.name}
                        </Typography>
                        <Typography color="text.secondary" sx={{ fontSize: "0.92rem" }} noWrap>
                          {restaurant.address}
                        </Typography>
                        <Stack direction="row" spacing={0.6} alignItems="center">
                          <StarRoundedIcon sx={{ fontSize: 18, color: "#F59E0B" }} />
                          <Typography fontWeight={700}>{restaurant.rating}</Typography>
                          <Typography color="text.secondary" sx={{ fontSize: "0.92rem" }}>
                            {restaurant.reviews}
                          </Typography>
                        </Stack>
                        <Stack direction="row" spacing={0.6} alignItems="center">
                          <FmdGoodRoundedIcon sx={{ fontSize: 17, color: "#2F6BFF" }} />
                          <Typography fontWeight={700} color="primary.main">
                            {restaurant.distance}
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
        eyebrow="Gợi ý nổi bật"
        title="Danh sách nổi bật"
        description="Các nhà hàng đang được quan tâm nhiều hôm nay."
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
                    color="primary"
                    sx={{ fontWeight: 700, px: 1 }}
                  />
                }
              />
            </Grid>
          ))}
        </Grid>
      )}
    </Stack>
  );
}

export default HomePage;
