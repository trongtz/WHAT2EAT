import { Box, Typography } from "@mui/material";

function EmptyState({ title, description }) {
  return (
    <Box
      sx={{
        py: 8,
        px: 3,
        borderRadius: 2,
        textAlign: "center",
        border: "1px dashed rgba(47, 107, 255, 0.25)",
        background: "rgba(255,255,255,0.72)",
      }}
    >
      <Typography variant="h4" mb={1}>
        {title}
      </Typography>
      <Typography color="text.secondary">{description}</Typography>
    </Box>
  );
}

export default EmptyState;
