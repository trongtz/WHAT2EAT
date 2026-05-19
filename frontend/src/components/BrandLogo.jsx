import { Stack } from "@mui/material";
import AppLogoImage from "./AppLogoImage";

function BrandLogo({ compact = false }) {
  return (
    <Stack direction="row" alignItems="center">
      <AppLogoImage size={compact ? 60 : 76} imageScale={0.9} />
    </Stack>
  );
}

export default BrandLogo;
