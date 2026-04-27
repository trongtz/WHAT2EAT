import { Box, Skeleton, Stack, Typography } from "@mui/material";

function LoadingScreen({ message = "Đang tải dữ liệu..." }) {
  return (
    <Box sx={{ minHeight: 240 }}>
      <Stack spacing={2.2}>
        <Typography color="text.secondary">{message}</Typography>
        <Skeleton variant="rounded" height={240} sx={{ borderRadius: 6 }} />
        <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
          {[1, 2, 3].map((item) => (
            <Stack
              key={item}
              spacing={1.2}
              sx={{
                flex: 1,
                p: 2,
                borderRadius: 6,
                bgcolor: "rgba(255,255,255,0.75)",
              }}
            >
              <Skeleton variant="rounded" height={160} sx={{ borderRadius: 5 }} />
              <Skeleton variant="text" width="68%" height={34} />
              <Skeleton variant="text" width="42%" />
              <Skeleton variant="text" width="86%" />
            </Stack>
          ))}
        </Stack>
      </Stack>
    </Box>
  );
}

export default LoadingScreen;
