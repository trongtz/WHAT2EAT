import { Stack, Typography } from "@mui/material";
import CustomCard from "./CustomCard";

function StatsCard({ label, value, color = "#2F6BFF" }) {
  return (
    <CustomCard
      sx={{
        background: `linear-gradient(135deg, ${color} 0%, rgba(255,255,255,0.95) 100%)`,
      }}
      contentSx={{ p: 3 }}
    >
      <Stack spacing={0.5}>
        <Typography color="text.secondary">{label}</Typography>
        <Typography variant="h3">{value}</Typography>
      </Stack>
    </CustomCard>
  );
}

export default StatsCard;
