import FavoriteBorderRoundedIcon from "@mui/icons-material/FavoriteBorderRounded";
import LocationOnRoundedIcon from "@mui/icons-material/LocationOnRounded";
import StarRoundedIcon from "@mui/icons-material/StarRounded";
import { Box, Chip, IconButton, Stack, Typography } from "@mui/material";
import { Link as RouterLink } from "react-router-dom";
import CustomCard from "./CustomCard";
import { formatCurrency, getStatusColor } from "../utils/helpers";

function RestaurantCard({ restaurant, action, compact = false }) {
  return (
    <CustomCard
      sx={{
        height: "100%",
        background: "linear-gradient(180deg, rgba(255,255,255,0.95) 0%, rgba(247,250,255,0.9) 100%)",
      }}
      contentSx={{ p: compact ? 2.75 : 3.5, "&:last-child": { pb: compact ? 2.75 : 3.5 } }}
    >
      <Stack spacing={2.25} sx={{ height: "100%" }}>
        <Box
          sx={{
            minHeight: compact ? 160 : 220,
            borderRadius: 2,
            overflow: "hidden",
            backgroundImage: `linear-gradient(180deg, rgba(20,24,43,0.02), rgba(20,24,43,0.32)), url(${restaurant.image})`,
            backgroundSize: "cover",
            backgroundPosition: "center",
            position: "relative",
          }}
        >
          <Chip
            label={restaurant.status}
            color={getStatusColor(restaurant.status)}
            sx={{ position: "absolute", top: 14, left: 14, fontWeight: 700 }}
          />
          <IconButton
            sx={{
              position: "absolute",
              top: 12,
              right: 12,
              bgcolor: "rgba(255,255,255,0.92)",
            }}
          >
            <FavoriteBorderRoundedIcon />
          </IconButton>
        </Box>

        <Stack direction="row" justifyContent="space-between" alignItems="flex-start" spacing={2}>
          <Box>
            <Typography
              variant="h4"
              component={RouterLink}
              to={`/nha-hang/${restaurant.id}`}
              sx={{ display: "inline-block", mb: 0.5 }}
            >
              {restaurant.name}
            </Typography>
            <Typography color="text.secondary">{restaurant.category}</Typography>
          </Box>
          <Chip label={restaurant.distance} color="primary" variant="outlined" />
        </Stack>

        <Stack direction="row" spacing={2} flexWrap="wrap" useFlexGap>
          <Stack direction="row" spacing={0.5} alignItems="center">
            <LocationOnRoundedIcon color="secondary" fontSize="small" />
            <Typography color="text.secondary">{restaurant.address}</Typography>
          </Stack>
          <Stack direction="row" spacing={0.5} alignItems="center">
            <StarRoundedIcon sx={{ color: "#FFB300" }} fontSize="small" />
            <Typography color="text.secondary">
              {restaurant.rating} • {restaurant.reviews} đánh giá
            </Typography>
          </Stack>
        </Stack>

        <Typography color="text.secondary">{restaurant.description}</Typography>

        <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={2} sx={{ mt: "auto", pt: 1 }}>
          <Typography fontWeight={800} color="primary.main">
            {restaurant.averagePrice ? `Từ ${formatCurrency(restaurant.averagePrice)}` : restaurant.priceRange}
          </Typography>
          {action}
        </Stack>
      </Stack>
    </CustomCard>
  );
}

export default RestaurantCard;
