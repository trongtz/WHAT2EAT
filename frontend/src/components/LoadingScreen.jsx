import { Box, CircularProgress, Typography } from "@mui/material";

function LoadingScreen({ message = "Đang tải dữ liệu..." }) {
  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        minHeight: 240,
        gap: 2,
      }}
    >
      <CircularProgress />
      <Typography color="text.secondary">{message}</Typography>
    </Box>
  );
}

export default LoadingScreen;
