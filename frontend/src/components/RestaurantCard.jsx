import ArrowOutwardRoundedIcon from "@mui/icons-material/ArrowOutwardRounded";
import FavoriteBorderRoundedIcon from "@mui/icons-material/FavoriteBorderRounded";
import LocationOnRoundedIcon from "@mui/icons-material/LocationOnRounded";
import StarRoundedIcon from "@mui/icons-material/StarRounded";
import { Box, Chip, IconButton, Stack, Typography } from "@mui/material";
import { Link as RouterLink } from "react-router-dom";
import { formatCurrency, getStatusColor } from "../utils/helpers";
import CustomCard from "./CustomCard";

function RestaurantCard({ restaurant, action, compact = false }) {
  return (
    <CustomCard
      sx={{
        height: "100%",
        overflow: "hidden",
        background: "rgba(255,255,255,0.94)",
        boxShadow: "0 20px 46px rgba(15, 23, 42, 0.08)",
        transition: "transform 0.28s ease, box-shadow 0.28s ease",
        "&:hover": {
          transform: "translateY(-6px)",
          boxShadow: "0 30px 56px rgba(15, 23, 42, 0.12)",
        },
        "&:hover .restaurant-card-media": {
          transform: "scale(1.05)",
        },
      }}
      contentSx={{ p: compact ? 2.5 : 3, "&:last-child": { pb: compact ? 2.5 : 3 } }}
    >
      <Stack spacing={2.25} sx={{ height: "100%" }}>
        <Box
          sx={{
            minHeight: compact ? 190 : 250,
            borderRadius: 3,
            overflow: "hidden",
            position: "relative",
          }}
        >
          <Box
            className="restaurant-card-media"
            sx={{
              position: "absolute",
              inset: 0,
              backgroundImage: `linear-gradient(180deg, rgba(8,15,28,0.04), rgba(8,15,28,0.28)), url(${restaurant.image})`,
              backgroundSize: "cover",
              backgroundPosition: "center",
              transition: "transform 0.35s ease",
            }}
          />
          <Chip
            label={restaurant.status}
            color={getStatusColor(restaurant.status)}
            sx={{ position: "absolute", top: 16, left: 16, fontWeight: 700, zIndex: 1 }}
          />
          <Chip
            icon={<StarRoundedIcon sx={{ color: "#F6B500 !important" }} />}
            label={`${restaurant.rating} (${restaurant.reviews})`}
            sx={{
              position: "absolute",
              right: 16,
              bottom: 16,
              zIndex: 1,
              bgcolor: "rgba(255,255,255,0.92)",
              color: "#18212F",
            }}
          />
          <IconButton
            sx={{
              position: "absolute",
              top: 14,
              right: 14,
              zIndex: 1,
              bgcolor: "rgba(255,255,255,0.9)",
              "&:hover": { bgcolor: "white" },
            }}
          >
            <FavoriteBorderRoundedIcon />
          </IconButton>
        </Box>

        <Stack direction="row" justifyContent="space-between" alignItems="flex-start" spacing={2}>
          <Box sx={{ minWidth: 0 }}>
            <Typography
              variant="h4"
              component={RouterLink}
              to={`/nha-hang/${restaurant.id}`}
              sx={{ display: "inline-block", mb: 0.6 }}
            >
              {restaurant.name}
            </Typography>
            <Typography color="text.secondary">{restaurant.category}</Typography>
          </Box>
          <Chip
            label={restaurant.distance}
            sx={{
              bgcolor: "color-mix(in srgb, var(--app-secondary) 12%, white)",
              color: "var(--app-secondary)",
              flexShrink: 0,
            }}
          />
        </Stack>

        <Stack direction="row" spacing={1} alignItems="center">
          <LocationOnRoundedIcon sx={{ fontSize: 18, color: "var(--app-secondary)" }} />
          <Typography color="text.secondary" sx={{ fontSize: "0.95rem" }}>
            {restaurant.address}
          </Typography>
        </Stack>

        <Typography color="text.secondary">{restaurant.description}</Typography>

        <Stack
          direction="row"
          justifyContent="space-between"
          alignItems="center"
          spacing={2}
          sx={{ mt: "auto", pt: 0.5 }}
        >
          <Box>
            <Typography sx={{ fontSize: "0.82rem", color: "text.secondary" }}>
              Mức giá tham khảo
            </Typography>
            <Typography fontWeight={800} color="primary.main">
              {restaurant.averagePrice ? `Từ ${formatCurrency(restaurant.averagePrice)}` : restaurant.priceRange}
            </Typography>
          </Box>

          {action || (
            <Chip
              component={RouterLink}
              to={`/nha-hang/${restaurant.id}`}
              clickable
              icon={<ArrowOutwardRoundedIcon />}
              label="Xem chi tiết"
              sx={{
                px: 1,
                bgcolor: "color-mix(in srgb, var(--app-primary) 12%, white)",
                color: "var(--app-primary)",
              }}
            />
          )}
        </Stack>
      </Stack>
    </CustomCard>
  );
}

export default RestaurantCard;
