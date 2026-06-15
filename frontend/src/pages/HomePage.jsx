import AutoAwesomeRoundedIcon from "@mui/icons-material/AutoAwesomeRounded";
import FmdGoodRoundedIcon from "@mui/icons-material/FmdGoodRounded";
import MenuBookRoundedIcon from "@mui/icons-material/MenuBookRounded";
import MyLocationRoundedIcon from "@mui/icons-material/MyLocationRounded";
import SearchRoundedIcon from "@mui/icons-material/SearchRounded";
import StarRoundedIcon from "@mui/icons-material/StarRounded";
import { Alert, Box, Button, Chip, Grid, Stack, Typography } from "@mui/material";
import L from "leaflet";
import { useEffect, useMemo, useState } from "react";
import { MapContainer, Marker, TileLayer, Tooltip, useMap, useMapEvents } from "react-leaflet";
import { Link as RouterLink } from "react-router-dom";
import CustomButton from "../components/CustomButton";
import CustomModal from "../components/CustomModal";
import LoadingScreen from "../components/LoadingScreen";
import RestaurantCard from "../components/RestaurantCard";
import SectionHeader from "../components/SectionHeader";
import { useAuth } from "../hooks/useAuth";
import { favoriteService } from "../services/favoriteService";
import { restaurantService } from "../services/restaurantService";
import { getGuestFavoriteIds, toggleGuestFavorite } from "../utils/guestSession";
import { formatCurrency, formatDate, formatOpenHours, getPriceRangeLabel, getTableAvailabilityLabel } from "../utils/helpers";

const DEFAULT_MAP_CENTER = [10.7769, 106.7009];
const DEFAULT_MAP_ZOOM = 14;
const NEARBY_MAP_ZOOM = 18;

const toRadians = (value) => (value * Math.PI) / 180;

const getDistanceInKm = ([lat1, lng1], [lat2, lng2]) => {
  const earthRadiusKm = 6371;
  const deltaLat = toRadians(lat2 - lat1);
  const deltaLng = toRadians(lng2 - lng1);

  const a =
    Math.sin(deltaLat / 2) ** 2 +
    Math.cos(toRadians(lat1)) * Math.cos(toRadians(lat2)) * Math.sin(deltaLng / 2) ** 2;

  return earthRadiusKm * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
};

const formatDistanceLabel = (distanceKm) => {
  if (!Number.isFinite(distanceKm)) return "Chưa xác định";
  if (distanceKm < 1) return `${Math.round(distanceKm * 1000)}m`;
  return `${distanceKm.toFixed(distanceKm < 10 ? 1 : 0)}km`;
};

const hasCoordinates = (restaurant) =>
  Number.isFinite(Number(restaurant.latitude)) && Number.isFinite(Number(restaurant.longitude));

const normalizeRestaurantSignature = (restaurant) =>
  [restaurant.name, restaurant.address, restaurant.category]
    .map((value) => String(value || "").trim().toLowerCase())
    .join("|");

const dedupeRestaurants = (restaurants) => {
  const seen = new Set();

  return restaurants.filter((restaurant) => {
    const signature = normalizeRestaurantSignature(restaurant);
    if (seen.has(signature)) return false;
    seen.add(signature);
    return true;
  });
};

const buildFallbackBackground = (index) => {
  const palettes = [
    "linear-gradient(135deg, rgba(47,133,90,0.92), rgba(104,211,145,0.72))",
    "linear-gradient(135deg, rgba(21,94,117,0.92), rgba(45,212,191,0.72))",
    "linear-gradient(135deg, rgba(29,78,216,0.92), rgba(96,165,250,0.72))",
    "linear-gradient(135deg, rgba(22,101,52,0.92), rgba(74,222,128,0.72))",
  ];

  return palettes[index % palettes.length];
};

const decorateRestaurant = (restaurant, index) => ({
  ...restaurant,
  lat: Number(restaurant.latitude),
  lng: Number(restaurant.longitude),
  position: [Number(restaurant.latitude), Number(restaurant.longitude)],
  imageBackground: restaurant.image
    ? `linear-gradient(180deg, rgba(18,22,44,0.08), rgba(18,22,44,0.24)), url(${restaurant.image})`
    : buildFallbackBackground(index),
});

const getNearestRestaurant = (origin, restaurants) => {
  if (!origin || !restaurants.length) return null;

  return restaurants.reduce((nearestRestaurant, currentRestaurant) => {
    if (!nearestRestaurant) return currentRestaurant;

    return getDistanceInKm(origin, currentRestaurant.position) <
      getDistanceInKm(origin, nearestRestaurant.position)
      ? currentRestaurant
      : nearestRestaurant;
  }, null);
};

const createPlaceMarkerIcon = ({ color }) =>
  L.divIcon({
    className: "",
    html: `
      <div class="smartfood-map-pin-wrap">
        <div class="smartfood-map-pin" style="--pin-color:${color};"></div>
      </div>
    `,
    iconSize: [30, 50],
    iconAnchor: [15, 44],
  });

const createUserMarkerIcon = () =>
  L.divIcon({
    className: "",
    html: `
      <div class="smartfood-map-pin-wrap">
        <div class="smartfood-map-pin smartfood-map-pin--user" style="--pin-color:#E5484D;"></div>
      </div>
    `,
    iconSize: [34, 56],
    iconAnchor: [17, 50],
  });

const defaultPlaceIcon = createPlaceMarkerIcon({ color: "#2F855A" });
const userPlaceIcon = createUserMarkerIcon();

const getMarkerDensityConfig = (zoom) => {
  if (zoom >= 17) return { cellSize: 0.00045, limit: 700 };
  if (zoom >= 16) return { cellSize: 0.0008, limit: 420 };
  if (zoom >= 15) return { cellSize: 0.0012, limit: 280 };
  if (zoom >= 14) return { cellSize: 0.0022, limit: 180 };
  if (zoom >= 13) return { cellSize: 0.0035, limit: 120 };
  return { cellSize: 0.006, limit: 80 };
};

const compactRestaurantsForViewport = (restaurants, zoom, anchorPosition, selectedRestaurantId) => {
  if (!restaurants.length) return [];

  const { cellSize, limit } = getMarkerDensityConfig(zoom);
  const gridMap = new Map();
  const orderedRestaurants = anchorPosition
    ? [...restaurants].sort(
        (firstRestaurant, secondRestaurant) =>
          getDistanceInKm(anchorPosition, firstRestaurant.position) -
          getDistanceInKm(anchorPosition, secondRestaurant.position)
      )
    : restaurants;

  for (const restaurant of orderedRestaurants) {
    const key =
      restaurant.id === selectedRestaurantId
        ? `selected:${restaurant.id}`
        : `${Math.round(restaurant.lat / cellSize)}:${Math.round(restaurant.lng / cellSize)}`;

    if (!gridMap.has(key)) {
      gridMap.set(key, restaurant);
    }

    if (gridMap.size >= limit) {
      break;
    }
  }

  if (
    selectedRestaurantId &&
    !Array.from(gridMap.values()).some((restaurant) => restaurant.id === selectedRestaurantId)
  ) {
    const selectedRestaurant = restaurants.find((restaurant) => restaurant.id === selectedRestaurantId);
    if (selectedRestaurant) {
      const values = Array.from(gridMap.values());
      values[values.length - 1] = selectedRestaurant;
      return values;
    }
  }

  return Array.from(gridMap.values());
};

const getRatingLabel = (restaurant) => {
  const rating = Number(restaurant.averageRating || restaurant.rating || 0);
  return rating > 0 ? rating.toFixed(1) : "Mới";
};

const buildRestaurantPreviewDetail = (restaurant, distanceLabel = "Chưa xác định") => ({
  ...restaurant,
  distanceLabel,
  imageBackground: restaurant.imageBackground || buildFallbackBackground(0),
  menu: Array.isArray(restaurant.menu) ? restaurant.menu : [],
  reviewsList: Array.isArray(restaurant.reviewsList) ? restaurant.reviewsList : [],
  reviewCount: Number(restaurant.reviewCount || restaurant.reviews || 0),
  averageRating: Number(restaurant.averageRating || restaurant.rating || 0),
  openHours: restaurant.openHours || "",
  availableCapacity: Number(restaurant.availableCapacity || 0),
  maxCapacity: Number(restaurant.maxCapacity || 0),
  phone: restaurant.phone || "",
  address: restaurant.address || "",
  priceRange: restaurant.priceRange || "",
  description: restaurant.description || "",
});

function MapFocusController({ focusState }) {
  const map = useMap();

  useEffect(() => {
    if (!focusState) return;
    map.flyTo(focusState.center, focusState.zoom, { duration: 0.85 });
  }, [focusState, map]);

  return null;
}

function MapViewportController({ onChange }) {
  const map = useMapEvents({
    moveend() {
      onChange({
        bounds: map.getBounds(),
        zoom: map.getZoom(),
      });
    },
    zoomend() {
      onChange({
        bounds: map.getBounds(),
        zoom: map.getZoom(),
      });
    },
  });

  useEffect(() => {
    onChange({
      bounds: map.getBounds(),
      zoom: map.getZoom(),
    });
  }, [map, onChange]);

  return null;
}

function HomePage() {
  const { user } = useAuth();
  const [restaurants, setRestaurants] = useState([]);
  const [favoriteIds, setFavoriteIds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedRestaurantId, setSelectedRestaurantId] = useState(null);
  const [activeRestaurantPreview, setActiveRestaurantPreview] = useState(null);
  const [activeRestaurantDetail, setActiveRestaurantDetail] = useState(null);
  const [activeRestaurantLoading, setActiveRestaurantLoading] = useState(false);
  const [activeRestaurantError, setActiveRestaurantError] = useState("");
  const [userPosition, setUserPosition] = useState(null);
  const [focusState, setFocusState] = useState(null);
  const [locationPending, setLocationPending] = useState(false);
  const [viewport, setViewport] = useState({ bounds: null, zoom: DEFAULT_MAP_ZOOM });

  useEffect(() => {
    const fetchRestaurants = async () => {
      try {
        const data = dedupeRestaurants(await restaurantService.getRestaurants());
        setRestaurants(data);
        const firstLocatedRestaurant = data.find((restaurant) => hasCoordinates(restaurant));
        setSelectedRestaurantId(firstLocatedRestaurant?.id || data[0]?.id || null);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchRestaurants();
  }, []);

  useEffect(() => {
    const loadFavorites = async () => {
      if (!user) {
        setFavoriteIds([]);
        return;
      }

      if (user.isGuest) {
        setFavoriteIds(getGuestFavoriteIds().map(String));
        return;
      }

      if (user.role !== "customer") {
        setFavoriteIds([]);
        return;
      }

      const ids = await favoriteService.getFavoriteRestaurantIds();
      setFavoriteIds(ids.map(String));
    };

    loadFavorites();
  }, [user]);

  useEffect(() => {
    if (!navigator.geolocation) return;

    setLocationPending(true);
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        const currentPosition = [coords.latitude, coords.longitude];
        setUserPosition(currentPosition);
        setFocusState({ center: currentPosition, zoom: NEARBY_MAP_ZOOM });
        setLocationPending(false);
      },
      () => {
        setLocationPending(false);
      },
      { enableHighAccuracy: true, timeout: 7000 }
    );
  }, []);

  const mapRestaurants = useMemo(
    () =>
      dedupeRestaurants(restaurants)
        .filter((restaurant) => hasCoordinates(restaurant))
        .map(decorateRestaurant),
    [restaurants]
  );

  useEffect(() => {
    if (!mapRestaurants.length) return;

    if (userPosition) {
      const nearestRestaurant = getNearestRestaurant(userPosition, mapRestaurants);
      if (nearestRestaurant) {
        setSelectedRestaurantId((currentValue) => currentValue || nearestRestaurant.id);
      }
      return;
    }

    if (!selectedRestaurantId) {
      setSelectedRestaurantId(mapRestaurants[0].id);
    }
  }, [mapRestaurants, selectedRestaurantId, userPosition]);

  const selectedMapRestaurant =
    mapRestaurants.find((restaurant) => restaurant.id === selectedRestaurantId) || mapRestaurants[0] || null;

  const visibleMapRestaurants = useMemo(() => {
    if (!viewport.bounds) return mapRestaurants;
    const paddedBounds = viewport.bounds.pad(0.25);
    return mapRestaurants.filter((restaurant) => paddedBounds.contains(restaurant.position));
  }, [mapRestaurants, viewport.bounds]);

  const renderedMapRestaurants = useMemo(() => {
    const anchorPosition =
      userPosition ||
      selectedMapRestaurant?.position ||
      (viewport.bounds ? [viewport.bounds.getCenter().lat, viewport.bounds.getCenter().lng] : null);

    return compactRestaurantsForViewport(
      visibleMapRestaurants,
      viewport.zoom,
      anchorPosition,
      selectedMapRestaurant?.id
    );
  }, [
    selectedMapRestaurant?.id,
    selectedMapRestaurant?.position,
    userPosition,
    viewport.bounds,
    viewport.zoom,
    visibleMapRestaurants,
  ]);

  const nearbyAnchorPosition = useMemo(() => {
    if (userPosition) return userPosition;
    if (selectedMapRestaurant?.position) return selectedMapRestaurant.position;
    if (viewport.bounds) {
      const center = viewport.bounds.getCenter();
      return [center.lat, center.lng];
    }
    return DEFAULT_MAP_CENTER;
  }, [selectedMapRestaurant?.position, userPosition, viewport.bounds]);

  const nearbyRestaurants = useMemo(() => {
    return dedupeRestaurants(mapRestaurants)
      .map((restaurant) => {
        const distanceKm = getDistanceInKm(nearbyAnchorPosition, restaurant.position);
        return {
          ...restaurant,
          distanceKm,
          distanceLabel: formatDistanceLabel(distanceKm),
        };
      })
      .sort((a, b) => a.distanceKm - b.distanceKm)
      .slice(0, 20);
  }, [mapRestaurants, nearbyAnchorPosition]);

  const featuredRestaurants = useMemo(() => {
    return dedupeRestaurants(restaurants)
      .sort((a, b) => {
        if (Number(b.averageRating || 0) !== Number(a.averageRating || 0)) {
          return Number(b.averageRating || 0) - Number(a.averageRating || 0);
        }

        if (Number(b.reviewCount || 0) !== Number(a.reviewCount || 0)) {
          return Number(b.reviewCount || 0) - Number(a.reviewCount || 0);
        }

        return new Date(b.createdAt || 0).getTime() - new Date(a.createdAt || 0).getTime();
      })
      .slice(0, 6)
      .map((restaurant) => {
        const distanceKm = hasCoordinates(restaurant)
          ? getDistanceInKm(nearbyAnchorPosition, [restaurant.latitude, restaurant.longitude])
          : null;

        return {
          ...restaurant,
          distance: formatDistanceLabel(distanceKm),
        };
      });
  }, [nearbyAnchorPosition, restaurants]);

  const insightItems = useMemo(
    () => [
      {
        label: "Gợi ý theo vị trí",
        value: `${mapRestaurants.length}+`,
        icon: FmdGoodRoundedIcon,
      },
      {
        label: "Nhà hàng nổi bật",
        value: featuredRestaurants.length ? getRatingLabel(featuredRestaurants[0]) : "--",
        icon: StarRoundedIcon,
      },
      {
        label: "Lượt đánh giá",
        value: `${restaurants.reduce((sum, restaurant) => sum + Number(restaurant.reviewCount || 0), 0)}+`,
        icon: MenuBookRoundedIcon,
      },
    ],
    [featuredRestaurants, mapRestaurants.length, restaurants]
  );

  const handleLocateMe = () => {
    if (userPosition) {
      setFocusState({ center: userPosition, zoom: NEARBY_MAP_ZOOM });
      return;
    }

    if (!navigator.geolocation) return;

    setLocationPending(true);
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        const currentPosition = [coords.latitude, coords.longitude];
        setUserPosition(currentPosition);
        setFocusState({ center: currentPosition, zoom: NEARBY_MAP_ZOOM });
        setLocationPending(false);
      },
      () => {
        setLocationPending(false);
      },
      { enableHighAccuracy: true, timeout: 7000 }
    );
  };

  const handleOpenRestaurantDetail = async (restaurant) => {
    setSelectedRestaurantId(restaurant.id);
    if (restaurant.position) {
      setFocusState({
        center: restaurant.position,
        zoom: Math.max(viewport.zoom, DEFAULT_MAP_ZOOM),
      });
    }

    const previewDistanceLabel =
      restaurant.distanceLabel ||
      (restaurant.position
        ? formatDistanceLabel(getDistanceInKm(nearbyAnchorPosition, restaurant.position))
        : "Chưa xác định");

    setActiveRestaurantPreview(restaurant);
    setActiveRestaurantError("");
    setActiveRestaurantDetail(buildRestaurantPreviewDetail(restaurant, previewDistanceLabel));
    setActiveRestaurantLoading(true);

    try {
      const detail = await restaurantService.getRestaurantDetail(restaurant.id);
      const detailPosition =
        hasCoordinates(detail) ? [detail.latitude, detail.longitude] : restaurant.position || null;
      const distanceKm = detailPosition ? getDistanceInKm(nearbyAnchorPosition, detailPosition) : null;

      setActiveRestaurantDetail({
        ...detail,
        distanceLabel: formatDistanceLabel(distanceKm),
        imageBackground: detail.image
          ? `linear-gradient(180deg, rgba(18,22,44,0.08), rgba(18,22,44,0.32)), url(${detail.image})`
          : restaurant.imageBackground || buildFallbackBackground(0),
      });
    } catch {
      setActiveRestaurantError("Không tải được đầy đủ chi tiết nhà hàng. Đang hiển thị thông tin cơ bản.");
    } finally {
      setActiveRestaurantLoading(false);
    }
  };

  const handleCloseDetail = () => {
    setActiveRestaurantPreview(null);
    setActiveRestaurantDetail(null);
    setActiveRestaurantLoading(false);
    setActiveRestaurantError("");
  };

  const handleToggleFavorite = async (restaurant) => {
    try {
      if (!user) {
        setError("Vui lòng đăng nhập để lưu yêu thích.");
        return;
      }

      if (user.isGuest) {
        setFavoriteIds(toggleGuestFavorite(restaurant.id).map(String));
        return;
      }

      if (user.role !== "customer") {
        return;
      }

      const result = await favoriteService.toggle(restaurant.id);
      setFavoriteIds((currentValue) => {
        const currentIds = currentValue.map(String);
        if (result.isFavorite) {
          return currentIds.includes(String(restaurant.id)) ? currentIds : [...currentIds, String(restaurant.id)];
        }
        return currentIds.filter((item) => item !== String(restaurant.id));
      });
    } catch (err) {
      setError(err.message);
    }
  };

  const heroViewportHeight = {
    xs: "min(68svh, 560px)",
    md: "calc(100svh - 190px)",
    lg: "calc(100svh - 170px)",
  };

  if (loading) return <LoadingScreen message="Đang tải bản đồ và danh sách nhà hàng..." />;

  return (
    <Stack spacing={4.5}>
      {error ? <Alert severity="error">{error}</Alert> : null}

      <Box className="glass-panel" sx={{ p: { xs: 1.5, md: 2 }, borderRadius: 2.5 }}>
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, lg: 8.2 }}>
            <Box
              sx={{
                position: "relative",
                overflow: "hidden",
                borderRadius: 2.5,
                height: heroViewportHeight,
                border: "1px solid rgba(255,255,255,0.72)",
                boxShadow: "0 26px 56px rgba(15, 23, 42, 0.08)",
              }}
            >
              <Box sx={{ position: "absolute", inset: 0 }}>
                <MapContainer
                  center={selectedMapRestaurant?.position || userPosition || DEFAULT_MAP_CENTER}
                  zoom={DEFAULT_MAP_ZOOM}
                  style={{ height: "100%", width: "100%" }}
                >
                  <TileLayer
                    attribution="Tiles © Esri — Source: Esri, Maxar, Earthstar Geographics, and the GIS User Community"
                    url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                  />

                  <MapViewportController onChange={setViewport} />
                  <MapFocusController focusState={focusState} />

                  {renderedMapRestaurants.map((restaurant) => (
                    <Marker
                      key={restaurant.id}
                      position={restaurant.position}
                      icon={defaultPlaceIcon}
                      eventHandlers={{ click: () => handleOpenRestaurantDetail(restaurant) }}
                    >
                      <Tooltip direction="top" offset={[0, -40]} opacity={0.98}>
                        {restaurant.name}
                      </Tooltip>
                    </Marker>
                  ))}

                  {userPosition ? <Marker position={userPosition} icon={userPlaceIcon} /> : null}
                </MapContainer>
              </Box>

              {!mapRestaurants.length ? (
                <Box
                  sx={{
                    position: "absolute",
                    inset: 0,
                    zIndex: 450,
                    display: "grid",
                    placeItems: "center",
                    pointerEvents: "none",
                    px: 2,
                    textAlign: "center",
                    bgcolor: "rgba(248,250,252,0.55)",
                    backdropFilter: "blur(4px)",
                  }}
                >
                  <Typography sx={{ fontWeight: 700 }}>
                    Chưa có chi nhánh nào có tọa độ để hiển thị trên bản đồ.
                  </Typography>
                </Box>
              ) : null}
            </Box>
          </Grid>

          <Grid size={{ xs: 12, lg: 3.8 }}>
            <Stack
              spacing={1.5}
              sx={{
                height: { xs: "auto", lg: "calc(100svh - 170px)" },
                maxHeight: { xs: "none", lg: "calc(100svh - 170px)" },
                overflowY: "auto",
                pr: 0.5,
              }}
            >
              {nearbyRestaurants.map((restaurant) => {
                const isActive =
                  activeRestaurantPreview?.id === restaurant.id || selectedMapRestaurant?.id === restaurant.id;

                return (
                  <Box
                    key={restaurant.id}
                    onClick={() => handleOpenRestaurantDetail(restaurant)}
                    sx={{
                      p: 1.25,
                      borderRadius: 2.5,
                      cursor: "pointer",
                      bgcolor: "rgba(255,255,255,0.94)",
                      border: isActive
                        ? "1px solid color-mix(in srgb, var(--app-primary) 22%, white)"
                        : "1px solid rgba(15,23,42,0.06)",
                      boxShadow: isActive
                        ? "0 24px 42px color-mix(in srgb, var(--app-primary) 14%, transparent)"
                        : "0 14px 26px rgba(15,23,42,0.06)",
                      transition: "all 0.24s ease",
                      "&:hover": {
                        transform: "translateY(-2px)",
                        boxShadow: "0 22px 36px rgba(15,23,42,0.10)",
                      },
                    }}
                  >
                    <Stack direction="row" spacing={1.15} alignItems="stretch">
                      <Box
                        sx={{
                          width: 92,
                          minWidth: 92,
                          height: 92,
                          borderRadius: 2,
                          overflow: "hidden",
                          backgroundImage: restaurant.imageBackground,
                          backgroundSize: "cover",
                          backgroundPosition: "center",
                        }}
                      />

                      <Stack
                        spacing={0.75}
                        sx={{
                          minWidth: 0,
                          flex: 1,
                          justifyContent: "space-between",
                        }}
                      >
                        <Stack sx={{ minWidth: 0 }}>
                          <Typography
                            variant="h4"
                            sx={{
                              fontSize: "0.98rem",
                              lineHeight: 1.25,
                              whiteSpace: "normal",
                              wordBreak: "break-word",
                            }}
                          >
                            {restaurant.name}
                          </Typography>
                          <Typography color="text.secondary" sx={{ fontSize: "0.9rem", mt: 0.15 }}>
                            {restaurant.address}
                          </Typography>
                          <Typography color="text.secondary" sx={{ fontSize: "0.86rem", mt: 0.25 }}>
                            Bàn trống: {getTableAvailabilityLabel(restaurant.availableCapacity, restaurant.maxCapacity)}
                          </Typography>
                        </Stack>

                        <Stack direction="row" spacing={1} alignItems="center" justifyContent="space-between">
                          <Stack direction="row" spacing={0.55} alignItems="center">
                            <FmdGoodRoundedIcon sx={{ fontSize: 15, color: "var(--app-secondary)" }} />
                            <Typography fontWeight={700} sx={{ color: "var(--app-secondary)", fontSize: "0.84rem" }}>
                              {restaurant.distanceLabel}
                            </Typography>
                          </Stack>

                          <Chip
                            size="small"
                            icon={<StarRoundedIcon sx={{ color: "#F6B500 !important", fontSize: 15 }} />}
                            label={getRatingLabel(restaurant)}
                            sx={{
                              height: 28,
                              bgcolor: "color-mix(in srgb, var(--app-primary) 10%, white)",
                              color: "var(--app-primary)",
                              "& .MuiChip-label": {
                                px: 1,
                                fontSize: "0.78rem",
                              },
                            }}
                          />
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
        eyebrow="Nổi bật hôm nay"
        title="Danh sách nổi bật hôm nay"
        description="Ưu tiên các nhà hàng có ảnh đẹp, đánh giá tốt và dữ liệu chi tiết đầy đủ để bạn chọn nhanh hơn."
      />

      <Grid container spacing={3}>
        {featuredRestaurants.map((restaurant) => (
          <Grid key={restaurant.id} size={{ xs: 12, md: 6, xl: 4 }}>
            <RestaurantCard
              restaurant={restaurant}
              isFavorite={favoriteIds.includes(String(restaurant.id))}
              onToggleFavorite={handleToggleFavorite}
              action={
                <Chip
                  component={RouterLink}
                  to={`/nha-hang/${restaurant.id}`}
                  clickable
                  label="Xem chi tiết"
                  sx={{
                    px: 1.2,
                    bgcolor: "color-mix(in srgb, var(--app-primary) 12%, white)",
                    color: "var(--app-primary)",
                  }}
                />
              }
            />
          </Grid>
        ))}
      </Grid>

      <Box
        sx={{
          px: { xs: 2.2, md: 4.5 },
          py: { xs: 3, md: 4.25 },
          borderRadius: 2.5,
          position: "relative",
          overflow: "hidden",
          background:
            "linear-gradient(135deg, color-mix(in srgb, var(--app-primary) 12%, white) 0%, color-mix(in srgb, var(--app-primary-light) 10%, white) 34%, color-mix(in srgb, var(--app-secondary) 10%, white) 100%)",
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
            background:
              "radial-gradient(circle, color-mix(in srgb, var(--app-primary-light) 42%, transparent), transparent 68%)",
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
                  color: "var(--app-primary)",
                }}
              />
              <Typography variant="h1" sx={{ maxWidth: 720 }}>
                WHAT2EAT giúp bạn tìm quán ngon gần mình bằng dữ liệu thật từ hệ thống.
              </Typography>
              <Typography color="text.secondary" sx={{ maxWidth: 620, fontSize: "1.05rem" }}>
                Bản đồ, danh sách quán gần bạn, menu và đánh giá đều được đọc trực tiếp từ dữ liệu nhà
                hàng hiện có, giúp việc chọn quán nhanh hơn và sát thực tế hơn.
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
                    backgroundImage: "linear-gradient(135deg, var(--app-primary) 0%, var(--app-primary-light) 100%)",
                    boxShadow: "0 18px 36px color-mix(in srgb, var(--app-primary) 24%, transparent)",
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
                    borderColor: "color-mix(in srgb, var(--app-secondary) 24%, white)",
                    color: "var(--app-secondary)",
                    bgcolor: "rgba(255,255,255,0.72)",
                  }}
                >
                  {locationPending ? "Đang lấy vị trí..." : "Vị trí của tôi"}
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
                        background:
                          "linear-gradient(135deg, color-mix(in srgb, var(--app-primary) 18%, white), color-mix(in srgb, var(--app-secondary) 14%, white))",
                      }}
                    >
                      <Icon
                        sx={{
                          color: item.icon === StarRoundedIcon ? "var(--app-primary)" : "var(--app-secondary)",
                        }}
                      />
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

      <CustomModal
        open={Boolean(activeRestaurantPreview)}
        onClose={handleCloseDetail}
        title={activeRestaurantDetail?.name || activeRestaurantPreview?.name || "Chi tiết quán"}
        width={760}
      >
        {activeRestaurantDetail ? (
          <Stack spacing={2}>
            {activeRestaurantError ? <Alert severity="warning">{activeRestaurantError}</Alert> : null}

            <Box
              sx={{
                minHeight: 240,
                borderRadius: 2.5,
                p: 2,
                display: "flex",
                alignItems: "flex-end",
                backgroundImage: activeRestaurantDetail.imageBackground,
                backgroundSize: "cover",
                backgroundPosition: "center",
              }}
            >
              <Stack direction={{ xs: "column", sm: "row" }} spacing={1} useFlexGap flexWrap="wrap">
                <Chip
                  icon={<StarRoundedIcon sx={{ color: "#F6B500 !important" }} />}
                  label={
                    Number(activeRestaurantDetail.averageRating || 0) > 0
                      ? `${Number(activeRestaurantDetail.averageRating || 0).toFixed(1)} sao`
                      : "Chưa có đánh giá"
                  }
                  sx={{
                    bgcolor: "color-mix(in srgb, var(--app-primary) 10%, white)",
                    color: "var(--app-primary)",
                  }}
                />
                <Chip
                  icon={<FmdGoodRoundedIcon />}
                  label={`Cách bạn ${activeRestaurantDetail.distanceLabel}`}
                  sx={{
                    bgcolor: "color-mix(in srgb, var(--app-secondary) 10%, white)",
                    color: "var(--app-secondary)",
                  }}
                />
                <Chip
                  label={`${activeRestaurantDetail.reviewCount || 0} đánh giá`}
                  sx={{ bgcolor: "rgba(255,255,255,0.86)", color: "text.primary" }}
                />
              </Stack>
            </Box>

            {activeRestaurantLoading ? <LoadingScreen message="Đang tải thêm chi tiết nhà hàng..." /> : null}

            <Grid container spacing={1.5}>
              <Grid size={{ xs: 12, md: 6 }}>
                <Box
                  sx={{
                    p: 1.6,
                    height: "100%",
                    borderRadius: 2,
                    bgcolor: "rgba(255,255,255,0.72)",
                    border: "1px solid rgba(15,23,42,0.06)",
                  }}
                >
                  <Typography variant="h4" sx={{ fontSize: "1rem", mb: 0.8 }}>
                    Thông tin nhanh
                  </Typography>
                  <Stack spacing={0.6}>
                    <Typography color="text.secondary">
                      Địa chỉ: {activeRestaurantDetail.address || "Chưa cập nhật"}
                    </Typography>
                    <Typography color="text.secondary">
                      Điện thoại: {activeRestaurantDetail.phone || "Chưa cập nhật"}
                    </Typography>
                    <Typography color="text.secondary">
                      Giờ mở cửa: {formatOpenHours(activeRestaurantDetail.openHours)}
                    </Typography>
                    <Typography color="text.secondary">
                      Bàn trống: {getTableAvailabilityLabel(activeRestaurantDetail.availableCapacity, activeRestaurantDetail.maxCapacity)}
                    </Typography>
                    <Typography color="text.secondary">
                      Khoảng giá: {getPriceRangeLabel(activeRestaurantDetail.priceRange)}
                    </Typography>
                  </Stack>
                </Box>
              </Grid>

              <Grid size={{ xs: 12, md: 6 }}>
                <Box
                  sx={{
                    p: 1.6,
                    height: "100%",
                    borderRadius: 2,
                    bgcolor: "rgba(255,255,255,0.72)",
                    border: "1px solid rgba(15,23,42,0.06)",
                  }}
                >
                  <Typography variant="h4" sx={{ fontSize: "1rem", mb: 0.8 }}>
                    Menu nổi bật
                  </Typography>
                  <Stack spacing={1}>
                    {activeRestaurantDetail.menu.length ? (
                      activeRestaurantDetail.menu.slice(0, 4).map((item) => (
                        <Stack
                          key={item.id}
                          direction="row"
                          spacing={1.1}
                          sx={{
                            p: 1,
                            borderRadius: 1.75,
                            bgcolor: "rgba(255,255,255,0.84)",
                            border: "1px solid rgba(15,23,42,0.06)",
                            alignItems: "center",
                          }}
                        >
                          <Box
                            sx={{
                              width: 66,
                              minWidth: 66,
                              height: 66,
                              borderRadius: 1.5,
                              overflow: "hidden",
                              background: item.imageUrl
                                ? `linear-gradient(180deg, rgba(18,22,44,0.04), rgba(18,22,44,0.18)), url(${item.imageUrl})`
                                : "linear-gradient(135deg, color-mix(in srgb, var(--app-primary) 16%, white), color-mix(in srgb, var(--app-secondary) 12%, white))",
                              backgroundSize: "cover",
                              backgroundPosition: "center",
                            }}
                          />
                          <Stack spacing={0.35} sx={{ minWidth: 0, flex: 1 }}>
                            <Typography sx={{ fontWeight: 800, lineHeight: 1.25 }}>{item.name}</Typography>
                            <Typography
                              color="text.secondary"
                              sx={{
                                fontSize: "0.84rem",
                                display: "-webkit-box",
                                WebkitLineClamp: 2,
                                WebkitBoxOrient: "vertical",
                                overflow: "hidden",
                              }}
                            >
                              {item.description || "Chưa có mô tả món ăn."}
                            </Typography>
                            <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={1}>
                              <Typography fontWeight={800}>{formatCurrency(item.price)}</Typography>
                              <Chip
                                size="small"
                                label={item.isAvailable ? "Đang phục vụ" : "Tạm hết"}
                                sx={{
                                  bgcolor: item.isAvailable
                                    ? "color-mix(in srgb, var(--app-primary) 12%, white)"
                                    : "rgba(15,23,42,0.08)",
                                  color: item.isAvailable ? "var(--app-primary)" : "text.secondary",
                                }}
                              />
                            </Stack>
                          </Stack>
                        </Stack>
                      ))
                    ) : (
                      <Typography color="text.secondary">Nhà hàng này chưa có món ăn được khai báo.</Typography>
                    )}
                  </Stack>
                </Box>
              </Grid>

              <Grid size={{ xs: 12 }}>
                <Box
                  sx={{
                    p: 1.6,
                    borderRadius: 2,
                    bgcolor: "rgba(255,255,255,0.72)",
                    border: "1px solid rgba(15,23,42,0.06)",
                  }}
                >
                  <Typography variant="h4" sx={{ fontSize: "1rem", mb: 0.8 }}>
                    Mô tả chi tiết
                  </Typography>
                  <Typography color="text.secondary">
                    {activeRestaurantDetail.description || "Nhà hàng này chưa có mô tả chi tiết."}
                  </Typography>
                </Box>
              </Grid>

              <Grid size={{ xs: 12 }}>
                <Box
                  sx={{
                    p: 1.6,
                    borderRadius: 2,
                    bgcolor: "rgba(255,255,255,0.72)",
                    border: "1px solid rgba(15,23,42,0.06)",
                  }}
                >
                  <Typography variant="h4" sx={{ fontSize: "1rem", mb: 0.8 }}>
                    Đánh giá gần đây
                  </Typography>
                  <Stack spacing={1.1}>
                    {activeRestaurantDetail.reviewsList.length ? (
                      activeRestaurantDetail.reviewsList.slice(0, 3).map((review) => (
                        <Box key={review.id}>
                          <Typography fontWeight={700}>{review.userName || "Khách hàng"}</Typography>
                          <Typography color="text.secondary">
                            {review.comment || "Không có nội dung đánh giá."}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {formatDate(review.createdAt)}
                          </Typography>
                        </Box>
                      ))
                    ) : (
                      <Typography color="text.secondary">Nhà hàng này chưa có đánh giá nào.</Typography>
                    )}
                  </Stack>
                </Box>
              </Grid>
            </Grid>

            <Stack direction={{ xs: "column", sm: "row" }} spacing={1.25}>
              <CustomButton component={RouterLink} to={`/nha-hang/${activeRestaurantDetail.id}`} onClick={handleCloseDetail}>
                Xem trang chi tiết
              </CustomButton>
              <CustomButton
                component={RouterLink}
                to={`/dat-ban?nhaHang=${activeRestaurantDetail.id}`}
                onClick={handleCloseDetail}
                sx={{ background: "linear-gradient(135deg, #0F8F82 0%, #5EEAD4 100%)" }}
              >
                Đặt bàn ngay
              </CustomButton>
            </Stack>
          </Stack>
        ) : null}
      </CustomModal>
    </Stack>
  );
}

export default HomePage;
