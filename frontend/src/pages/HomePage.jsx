import AccessTimeRoundedIcon from "@mui/icons-material/AccessTimeRounded";
import AutoAwesomeRoundedIcon from "@mui/icons-material/AutoAwesomeRounded";
import FmdGoodRoundedIcon from "@mui/icons-material/FmdGoodRounded";
import MyLocationRoundedIcon from "@mui/icons-material/MyLocationRounded";
import SearchRoundedIcon from "@mui/icons-material/SearchRounded";
import StarRoundedIcon from "@mui/icons-material/StarRounded";
import {
  alpha,
  Box,
  Button,
  Chip,
  Grid,
  Stack,
  Typography,
} from "@mui/material";
import L from "leaflet";
import { useEffect, useMemo, useState } from "react";
import {
  MapContainer,
  Marker,
  TileLayer,
  Tooltip,
  useMap,
  useMapEvents,
} from "react-leaflet";
import { Link as RouterLink } from "react-router-dom";
import restaurantsCsv from "../../data/restaurants.csv?raw";
import CustomModal from "../components/CustomModal";
import LoadingScreen from "../components/LoadingScreen";
import RestaurantCard from "../components/RestaurantCard";
import SectionHeader from "../components/SectionHeader";
import { restaurantService } from "../services/restaurantService";

const DEFAULT_MAP_CENTER = [10.7769, 106.7009];
const DEFAULT_MAP_ZOOM = 14;
const NEARBY_MAP_ZOOM = 18;

const insightItems = [
  { label: "Gợi ý theo vị trí", value: "12+", icon: FmdGoodRoundedIcon },
  { label: "Nhà hàng nổi bật", value: "Top rated", icon: StarRoundedIcon },
  { label: "Đặt bàn siêu nhanh", value: "< 30s", icon: AccessTimeRoundedIcon },
];

const parseCsvLine = (line) => {
  const values = [];
  let currentValue = "";
  let inQuotes = false;

  for (let index = 0; index < line.length; index += 1) {
    const character = line[index];

    if (character === '"') {
      if (inQuotes && line[index + 1] === '"') {
        currentValue += '"';
        index += 1;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }

    if (character === "," && !inQuotes) {
      values.push(currentValue.trim());
      currentValue = "";
      continue;
    }

    currentValue += character;
  }

  values.push(currentValue.trim());
  return values;
};

const csvRestaurants = restaurantsCsv
  .split(/\r?\n/)
  .map((line) => line.trim())
  .filter(Boolean)
  .slice(1)
  .map(parseCsvLine)
  .map(([id, name, lat, lng]) => {
    const latitude = Number(lat);
    const longitude = Number(lng);

    return {
      id,
      name,
      lat: latitude,
      lng: longitude,
      position: [latitude, longitude],
    };
  })
  .filter(
    (place) =>
      place.id &&
      place.name &&
      Number.isFinite(place.lat) &&
      Number.isFinite(place.lng)
  );

const toRadians = (value) => (value * Math.PI) / 180;

const getDistanceInKm = ([lat1, lng1], [lat2, lng2]) => {
  const earthRadiusKm = 6371;
  const deltaLat = toRadians(lat2 - lat1);
  const deltaLng = toRadians(lng2 - lng1);

  const a =
    Math.sin(deltaLat / 2) ** 2 +
    Math.cos(toRadians(lat1)) *
      Math.cos(toRadians(lat2)) *
      Math.sin(deltaLng / 2) ** 2;

  return earthRadiusKm * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
};

const formatDistanceLabel = (distanceKm) => {
  if (!Number.isFinite(distanceKm)) return "";
  if (distanceKm < 1) return `${Math.round(distanceKm * 1000)}m`;
  return `${distanceKm.toFixed(distanceKm < 10 ? 1 : 0)}km`;
};

const getPlaceholderRating = (placeId) => {
  const numericPart = Number(String(placeId).replace(/\D/g, "").slice(-2) || 0);
  return (4.2 + (numericPart % 7) * 0.1).toFixed(1);
};

const getPlaceholderReviewCount = (placeId) => {
  const numericPart = Number(String(placeId).replace(/\D/g, "").slice(-3) || 0);
  return 40 + (numericPart % 180);
};

const getPlaceholderImageBackground = (placeId) => {
  const palettes = [
    "linear-gradient(135deg, rgba(27,94,32,0.92), rgba(67,160,71,0.72))",
    "linear-gradient(135deg, rgba(183,28,28,0.92), rgba(239,108,0,0.72))",
    "linear-gradient(135deg, rgba(13,71,161,0.92), rgba(66,165,245,0.72))",
    "linear-gradient(135deg, rgba(74,20,140,0.92), rgba(171,71,188,0.72))",
    "linear-gradient(135deg, rgba(0,96,100,0.92), rgba(38,166,154,0.72))",
  ];
  const numericPart = Number(String(placeId).replace(/\D/g, "").slice(-2) || 0);
  return palettes[numericPart % palettes.length];
};

const buildPlaceDetail = (place, anchorPosition) => {
  const distanceKm = getDistanceInKm(anchorPosition, place.position);

  return {
    ...place,
    distanceKm,
    distanceLabel: formatDistanceLabel(distanceKm),
    rating: getPlaceholderRating(place.id),
    reviewCount: getPlaceholderReviewCount(place.id),
    imageBackground: getPlaceholderImageBackground(place.id),
  };
};

const getNearestPlace = (origin, places) => {
  if (!origin || !places.length) return null;

  return places.reduce((nearest, currentPlace) => {
    if (!nearest) return currentPlace;

    return getDistanceInKm(origin, currentPlace.position) <
      getDistanceInKm(origin, nearest.position)
      ? currentPlace
      : nearest;
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

const defaultPlaceIcon = createPlaceMarkerIcon({ color: "#5EA2F7" });
const userPlaceIcon = createUserMarkerIcon();

const getMarkerDensityConfig = (zoom) => {
  if (zoom >= 17) return { cellSize: 0.00045, limit: 700 };
  if (zoom >= 16) return { cellSize: 0.0008, limit: 420 };
  if (zoom >= 15) return { cellSize: 0.0012, limit: 280 };
  if (zoom >= 14) return { cellSize: 0.0022, limit: 180 };
  if (zoom >= 13) return { cellSize: 0.0035, limit: 120 };
  return { cellSize: 0.006, limit: 80 };
};

const compactPlacesForViewport = (places, zoom, anchorPosition, selectedPlaceId) => {
  if (!places.length) return [];

  const { cellSize, limit } = getMarkerDensityConfig(zoom);

  if (!cellSize && places.length <= limit) {
    return places;
  }

  const gridMap = new Map();
  const orderedPlaces = anchorPosition
    ? [...places].sort(
        (firstPlace, secondPlace) =>
          getDistanceInKm(anchorPosition, firstPlace.position) -
          getDistanceInKm(anchorPosition, secondPlace.position)
      )
    : places;

  for (const place of orderedPlaces) {
    const key =
      place.id === selectedPlaceId
        ? `selected:${place.id}`
        : `${Math.round(place.lat / cellSize)}:${Math.round(place.lng / cellSize)}`;

    if (!gridMap.has(key)) {
      gridMap.set(key, place);
    }

    if (gridMap.size >= limit) {
      break;
    }
  }

  if (
    selectedPlaceId &&
    !Array.from(gridMap.values()).some((place) => place.id === selectedPlaceId)
  ) {
    const selectedPlace = places.find((place) => place.id === selectedPlaceId);
    if (selectedPlace) {
      const values = Array.from(gridMap.values());
      values[values.length - 1] = selectedPlace;
      return values;
    }
  }

  return Array.from(gridMap.values());
};

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
  const [restaurants, setRestaurants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState(1);
  const [selectedPlaceId, setSelectedPlaceId] = useState(csvRestaurants[0]?.id || null);
  const [activePlaceDetail, setActivePlaceDetail] = useState(null);
  const [userPosition, setUserPosition] = useState(null);
  const [focusState, setFocusState] = useState(null);
  const [locationPending, setLocationPending] = useState(false);
  const [viewport, setViewport] = useState({ bounds: null, zoom: DEFAULT_MAP_ZOOM });

  useEffect(() => {
    const fetchRestaurants = async () => {
      const data = await restaurantService.getRestaurants();
      setRestaurants(data);
      setLoading(false);
    };

    fetchRestaurants();
  }, []);

  useEffect(() => {
    if (!navigator.geolocation) return;

    setLocationPending(true);
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        const currentPosition = [coords.latitude, coords.longitude];
        setUserPosition(currentPosition);
        setFocusState({ center: currentPosition, zoom: NEARBY_MAP_ZOOM });

        const nearestPlace = getNearestPlace(currentPosition, csvRestaurants);
        if (nearestPlace) {
          setSelectedPlaceId(nearestPlace.id);
        }

        setLocationPending(false);
      },
      () => {
        setLocationPending(false);
      },
      { enableHighAccuracy: true, timeout: 7000 }
    );
  }, []);

  const featuredRestaurants = useMemo(
    () => restaurants.filter((item) => item.featured),
    [restaurants]
  );

  const filteredRestaurants = featuredRestaurants;

  useEffect(() => {
    if (
      filteredRestaurants.length &&
      !filteredRestaurants.some((item) => item.id === selectedId)
    ) {
      setSelectedId(filteredRestaurants[0].id);
    }
  }, [filteredRestaurants, selectedId]);

  const selectedMapPlace =
    csvRestaurants.find((place) => place.id === selectedPlaceId) || csvRestaurants[0] || null;

  const visibleMapPlaces = useMemo(() => {
    if (!viewport.bounds) return [];

    const paddedBounds = viewport.bounds.pad(0.25);
    return csvRestaurants.filter((place) => paddedBounds.contains(place.position));
  }, [viewport.bounds]);

  const renderedMapPlaces = useMemo(() => {
    const anchorPosition =
      userPosition || selectedMapPlace?.position || viewport.bounds?.getCenter?.() || null;

    return compactPlacesForViewport(
      visibleMapPlaces,
      viewport.zoom,
      anchorPosition ? [anchorPosition.lat ?? anchorPosition[0], anchorPosition.lng ?? anchorPosition[1]] : null,
      selectedMapPlace?.id
    );
  }, [selectedMapPlace?.id, selectedMapPlace?.position, userPosition, viewport.bounds, viewport.zoom, visibleMapPlaces]);

  const nearbyAnchorPosition = useMemo(() => {
    if (userPosition) return userPosition;
    if (selectedMapPlace?.position) return selectedMapPlace.position;
    if (viewport.bounds) {
      const center = viewport.bounds.getCenter();
      return [center.lat, center.lng];
    }
    return DEFAULT_MAP_CENTER;
  }, [selectedMapPlace?.position, userPosition, viewport.bounds]);

  const nearbyPlaces = useMemo(() => {
    return [...csvRestaurants]
      .map((place) => buildPlaceDetail(place, nearbyAnchorPosition))
      .sort((firstPlace, secondPlace) => firstPlace.distanceKm - secondPlace.distanceKm)
      .slice(0, 20);
  }, [nearbyAnchorPosition]);

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

        const nearestPlace = getNearestPlace(currentPosition, csvRestaurants);
        if (nearestPlace) {
          setSelectedPlaceId(nearestPlace.id);
        }

        setLocationPending(false);
      },
      () => {
        setLocationPending(false);
      },
      { enableHighAccuracy: true, timeout: 7000 }
    );
  };

  const handleSelectMapPlace = (place) => {
    setSelectedPlaceId(place.id);
    setFocusState({
      center: place.position,
      zoom: Math.max(viewport.zoom, DEFAULT_MAP_ZOOM),
    });
  };

  const handleOpenPlaceDetail = (place) => {
    const placeDetail = buildPlaceDetail(place, nearbyAnchorPosition);
    setSelectedPlaceId(place.id);
    setFocusState({
      center: place.position,
      zoom: Math.max(viewport.zoom, DEFAULT_MAP_ZOOM),
    });
    setActivePlaceDetail(placeDetail);
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
          <Grid size={{ xs: 12, lg: 8.2 }}>
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
                center={DEFAULT_MAP_CENTER}
                zoom={DEFAULT_MAP_ZOOM}
                scrollWheelZoom
                attributionControl={false}
                style={{ height: "100%", width: "100%" }}
              >
                <TileLayer
                  attribution="Tiles © Esri — Source: Esri, Maxar, Earthstar Geographics, and the GIS User Community"
                  url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                />

                <MapViewportController onChange={setViewport} />
                <MapFocusController focusState={focusState} />

                {renderedMapPlaces.map((place) => (
                  <Marker
                    key={place.id}
                    position={place.position}
                    icon={defaultPlaceIcon}
                    eventHandlers={{ click: () => handleOpenPlaceDetail(place) }}
                  >
                    <Tooltip direction="top" offset={[0, -40]} opacity={0.98}>
                      {`${place.name}${
                        userPosition
                          ? ` (${formatDistanceLabel(
                              getDistanceInKm(userPosition, place.position)
                            )})`
                          : ""
                      }`}
                    </Tooltip>
                  </Marker>
                ))}

                {userPosition ? (
                  <Marker position={userPosition} icon={userPlaceIcon} />
                ) : null}
              </MapContainer>

              <Stack
                spacing={1}
                sx={{
                  position: "absolute",
                  top: 14,
                  left: 14,
                  right: 14,
                  zIndex: 500,
                  pointerEvents: "none",
                }}
              >
                <Stack direction={{ xs: "column", sm: "row" }} spacing={0.8}>
                  <Button
                    onClick={handleLocateMe}
                    startIcon={<MyLocationRoundedIcon sx={{ fontSize: 20 }} />}
                    disabled={locationPending}
                    sx={{
                      pointerEvents: "auto",
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
              {nearbyPlaces.map((place) => {
                const isActive = activePlaceDetail?.id === place.id || selectedMapPlace?.id === place.id;

                return (
                  <Box
                    key={place.id}
                    onClick={() => handleOpenPlaceDetail(place)}
                    sx={{
                      p: 1.25,
                      borderRadius: 2.5,
                      cursor: "pointer",
                      bgcolor: "rgba(255,255,255,0.94)",
                      border: isActive
                        ? "1px solid rgba(255,138,42,0.22)"
                        : "1px solid rgba(15,23,42,0.06)",
                      boxShadow: isActive
                        ? "0 24px 42px rgba(255, 140, 64, 0.14)"
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
                          display: "flex",
                          alignItems: "flex-end",
                          justifyContent: "center",
                          p: 0.9,
                          backgroundImage: place.imageBackground,
                          backgroundSize: "cover",
                          backgroundPosition: "center",
                        }}
                      >
                        <Typography
                          sx={{
                            fontSize: "0.72rem",
                            fontWeight: 700,
                            color: "rgba(255,255,255,0.92)",
                            textAlign: "center",
                            px: 0.9,
                            py: 0.35,
                            borderRadius: 999,
                            bgcolor: "rgba(15,23,42,0.22)",
                            backdropFilter: "blur(6px)",
                          }}
                        >
                          Ảnh
                        </Typography>
                      </Box>

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
                              {place.name}
                            </Typography>
                          </Stack>

                        <Stack
                          direction="row"
                          spacing={1}
                          alignItems="center"
                          justifyContent="space-between"
                        >
                          <Stack direction="row" spacing={0.55} alignItems="center">
                            <FmdGoodRoundedIcon sx={{ fontSize: 15, color: "#4A90E2" }} />
                            <Typography
                              fontWeight={700}
                              sx={{ color: "#4A90E2", fontSize: "0.84rem" }}
                            >
                              {place.distanceLabel}
                            </Typography>
                          </Stack>

                          <Chip
                            size="small"
                            icon={<StarRoundedIcon sx={{ color: "#F6B500 !important", fontSize: 15 }} />}
                            label={place.rating}
                            sx={{
                              height: 28,
                              bgcolor: alpha("#22B573", 0.1),
                              color: "#169A52",
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
                        background:
                          "linear-gradient(135deg, rgba(255,122,24,0.18), rgba(74,144,226,0.14))",
                      }}
                    >
                      <Icon
                        sx={{ color: item.icon === StarRoundedIcon ? "#22B573" : "#4A90E2" }}
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
        open={Boolean(activePlaceDetail)}
        onClose={() => setActivePlaceDetail(null)}
        title={activePlaceDetail?.name || "Chi tiết quán"}
        width={640}
      >
        {activePlaceDetail ? (
          <Stack spacing={2}>
            <Box
              sx={{
                minHeight: 220,
                borderRadius: 2.5,
                p: 2,
                display: "flex",
                alignItems: "flex-end",
                backgroundImage: activePlaceDetail.imageBackground,
              }}
            >
              <Chip
                label="Ảnh bìa của quán sẽ cập nhật sau"
                sx={{
                  bgcolor: "rgba(255,255,255,0.2)",
                  color: "white",
                  backdropFilter: "blur(10px)",
                }}
              />
            </Box>

            <Stack direction={{ xs: "column", sm: "row" }} spacing={1} useFlexGap flexWrap="wrap">
              <Chip
                icon={<StarRoundedIcon sx={{ color: "#F6B500 !important" }} />}
                label={`${activePlaceDetail.rating} sao`}
                sx={{ bgcolor: alpha("#22B573", 0.1), color: "#169A52" }}
              />
              <Chip
                icon={<FmdGoodRoundedIcon />}
                label={`Cách bạn ${activePlaceDetail.distanceLabel}`}
                sx={{ bgcolor: "rgba(74,144,226,0.1)", color: "secondary.main" }}
              />
              <Chip
                label={`${activePlaceDetail.reviewCount} đánh giá`}
                sx={{ bgcolor: "rgba(15,23,42,0.06)", color: "text.secondary" }}
              />
            </Stack>

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
                    <Typography color="text.secondary">Tên quán: {activePlaceDetail.name}</Typography>
                    <Typography color="text.secondary">
                      Tọa độ: {activePlaceDetail.lat.toFixed(6)}, {activePlaceDetail.lng.toFixed(6)}
                    </Typography>
                    <Typography color="text.secondary">Địa chỉ chi tiết: sẽ cập nhật sau</Typography>
                    <Typography color="text.secondary">Giờ mở cửa: sẽ cập nhật sau</Typography>
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
                  <Stack spacing={0.6}>
                    <Typography color="text.secondary">Món 1: sẽ cập nhật sau</Typography>
                    <Typography color="text.secondary">Món 2: sẽ cập nhật sau</Typography>
                    <Typography color="text.secondary">Món 3: sẽ cập nhật sau</Typography>
                    <Typography color="text.secondary">Khoảng giá: sẽ cập nhật sau</Typography>
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
                    Khu vực này đang để trống để sau này bạn thêm mô tả quán, không gian, món signature, lưu ý đặt bàn hoặc thông tin khuyến mãi.
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </Stack>
        ) : null}
      </CustomModal>
    </Stack>
  );
}

export default HomePage;
