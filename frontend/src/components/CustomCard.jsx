import { Card, CardContent } from "@mui/material";

function CustomCard({ children, sx, contentSx, ...props }) {
  return (
    <Card
      className="glass-panel"
      sx={{
        overflow: "visible",
        borderRadius: 2,
        background: "var(--app-surface-strong)",
        border: "1px solid color-mix(in srgb, var(--app-text-primary) 10%, white)",
        boxShadow:
          "0 24px 50px var(--app-glass-shadow), inset 0 1px 0 rgba(255,255,255,0.55)",
        ...sx,
      }}
      {...props}
    >
      <CardContent
        sx={{
          p: 3.5,
          "&:last-child": { pb: 3.5 },
          ...contentSx,
        }}
      >
        {children}
      </CardContent>
    </Card>
  );
}

export default CustomCard;
