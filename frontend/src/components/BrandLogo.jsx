import FmdGoodRoundedIcon from "@mui/icons-material/FmdGoodRounded";
import RestaurantRoundedIcon from "@mui/icons-material/RestaurantRounded";
import { Box, Stack, Typography } from "@mui/material";

function BrandLogo({ compact = false }) {
  return (
    <Stack direction="row" spacing={compact ? 1.1 : 1.25} alignItems="center">
      <Box
        sx={{
          width: compact ? 46 : 52,
          height: compact ? 46 : 52,
          borderRadius: "50%",
          position: "relative",
          display: "grid",
          placeItems: "center",
          background: "var(--app-primary-gradient)",
          boxShadow: "0 14px 28px color-mix(in srgb, var(--app-primary) 24%, transparent)",
          overflow: "hidden",
          flexShrink: 0,
        }}
      >
        <Box
          sx={{
            position: "absolute",
            inset: compact ? 10 : 11,
            borderRadius: "50%",
            background: "var(--app-surface-strong)",
          }}
        />
        <Box
          sx={{
            position: "absolute",
            inset: 2,
            borderRadius: "50%",
            background:
              "radial-gradient(circle at top, rgba(255,255,255,0.26), transparent 52%), rgba(255,255,255,0.04)",
          }}
        />
        <FmdGoodRoundedIcon sx={{ position: "absolute", fontSize: compact ? 28 : 32, color: "white" }} />
        <RestaurantRoundedIcon
          sx={{
            position: "absolute",
            fontSize: compact ? 13 : 15,
            color: "var(--app-primary)",
            transform: "translateY(1px)",
          }}
        />
      </Box>

      <Box sx={{ minWidth: 0 }}>
        <Typography
          sx={{
            fontSize: compact ? "1.02rem" : "1.12rem",
            fontWeight: 800,
            letterSpacing: "0.05em",
            lineHeight: 1.05,
          }}
        >
          WHAT2EAT
        </Typography>
        {!compact ? (
          <Typography
            sx={{ mt: 0.28, fontSize: "0.72rem", color: "text.secondary", letterSpacing: "0.07em" }}
          >
            DISCOVER TASTE NEAR YOU
          </Typography>
        ) : null}
      </Box>
    </Stack>
  );
}

export default BrandLogo;
