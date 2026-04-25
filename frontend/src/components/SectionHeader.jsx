import { Stack, Typography } from "@mui/material";

function SectionHeader({ eyebrow, title, description, action }) {
  return (
    <Stack
      direction={{ xs: "column", md: "row" }}
      alignItems={{ xs: "flex-start", md: "center" }}
      justifyContent="space-between"
      spacing={2}
      mb={3}
    >
      <div>
        {eyebrow ? (
          <Typography color="secondary.main" fontWeight={800} mb={0.5}>
            {eyebrow}
          </Typography>
        ) : null}
        <Typography variant="h3" mb={0.5}>
          {title}
        </Typography>
        {description ? <Typography color="text.secondary">{description}</Typography> : null}
      </div>
      {action}
    </Stack>
  );
}

export default SectionHeader;
