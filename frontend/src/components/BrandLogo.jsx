import FmdGoodRoundedIcon from "@mui/icons-material/FmdGoodRounded";
import RestaurantRoundedIcon from "@mui/icons-material/RestaurantRounded";
import { Box, Stack, Typography } from "@mui/material";

function BrandLogo({ compact = false }) {
  return (
    <Stack direction="row" spacing={compact ? 1.25 : 1.4} alignItems="center">
      <Box
        sx={{
          width: compact ? 48 : 54,
          height: compact ? 48 : 54,
          borderRadius: compact ? 2.5 : 4,
          position: "relative",
          display: "grid",
          placeItems: "center",
          background: "linear-gradient(135deg, #FF7A18 0%, #FFB347 100%)",
          boxShadow: "0 20px 42px rgba(255, 140, 64, 0.28)",
          overflow: "hidden",
        }}
      >
        <Box
          sx={{
            position: "absolute",
            inset: 1.5,
            borderRadius: compact ? 2 : 2.5,
            background:
              "radial-gradient(circle at top, rgba(255,255,255,0.28), transparent 48%), rgba(255,255,255,0.08)",
          }}
        />
        <FmdGoodRoundedIcon sx={{ position: "absolute", fontSize: compact ? 31 : 36, color: "white" }} />
        <RestaurantRoundedIcon
          sx={{
            position: "absolute",
            fontSize: compact ? 16 : 18,
            color: "#FF8B2C",
            transform: "translateY(1px)",
            filter: "drop-shadow(0 2px 4px rgba(0,0,0,0.08))",
          }}
        />
      </Box>

      <Box>
        <Typography
          sx={{
            fontSize: compact ? "1.05rem" : "1.14rem",
            fontWeight: 800,
            letterSpacing: "0.06em",
            lineHeight: 1,
          }}
        >
          WHAT2EAT
        </Typography>
        {!compact ? (
          <Typography sx={{ mt: 0.35, fontSize: "0.74rem", color: "text.secondary", letterSpacing: "0.08em" }}>
            DISCOVER TASTE NEAR YOU
          </Typography>
        ) : null}
      </Box>
    </Stack>
  );
}

export default BrandLogo;
