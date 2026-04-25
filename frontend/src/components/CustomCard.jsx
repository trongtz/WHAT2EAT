import { Card, CardContent } from "@mui/material";

function CustomCard({ children, sx, contentSx, ...props }) {
  return (
    <Card
      className="glass-panel"
      sx={{
        overflow: "visible",
        borderRadius: 2,
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
