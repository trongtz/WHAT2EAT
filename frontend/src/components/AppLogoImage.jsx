import { Box } from "@mui/material";

function AppLogoImage({
  size = 48,
  sx,
  alt = "WHAT2EAT",
  framed = true,
  imageScale = 0.94,
}) {
  if (!framed) {
    return (
      <Box
        component="img"
        src="/logo.jpg"
        alt={alt}
        sx={{
          width: size,
          height: size,
          objectFit: "contain",
          display: "block",
          flexShrink: 0,
          ...sx,
        }}
      />
    );
  }

  return (
    <Box
      sx={{
        width: size,
        height: size,
        borderRadius: "50%",
        overflow: "hidden",
        display: "grid",
        placeItems: "center",
        flexShrink: 0,
        bgcolor: "#050505",
        border: "2px solid rgba(255,255,255,0.82)",
        boxShadow: "0 12px 28px rgba(15, 23, 42, 0.16), inset 0 0 0 1px rgba(255,255,255,0.08)",
        ...sx,
      }}
    >
      <Box
        component="img"
        src="/logo.jpg"
        alt={alt}
        sx={{
          width: `${imageScale * 100}%`,
          height: `${imageScale * 100}%`,
          objectFit: "contain",
          display: "block",
        }}
      />
    </Box>
  );
}

export default AppLogoImage;
