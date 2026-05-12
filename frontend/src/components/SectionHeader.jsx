import { Box, Stack, Typography } from "@mui/material";

function SectionHeader({ eyebrow, title, description, action }) {
  return (
    <Stack
      direction={{ xs: "column", md: "row" }}
      alignItems={{ xs: "flex-start", md: "flex-end" }}
      justifyContent="space-between"
      spacing={2}
      mb={3}
    >
      <Box>
        {eyebrow ? (
          <Typography
            sx={{
              display: "inline-flex",
              alignItems: "center",
              px: 1.5,
              py: 0.75,
              mb: 1.25,
              borderRadius: 999,
              bgcolor: "color-mix(in srgb, var(--app-primary) 12%, white)",
              color: "var(--app-primary)",
              fontWeight: 800,
              letterSpacing: "0.04em",
            }}
          >
            {eyebrow}
          </Typography>
        ) : null}
        <Typography variant="h3" mb={0.6}>
          {title}
        </Typography>
        {description ? (
          <Typography color="text.secondary" sx={{ maxWidth: 620 }}>
            {description}
          </Typography>
        ) : null}
      </Box>
      {action}
    </Stack>
  );
}

export default SectionHeader;
