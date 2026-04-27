import { Button } from "@mui/material";

function CustomButton({ children, sx, ...props }) {
  return (
    <Button
      variant="contained"
      sx={{
        px: 3,
        py: 0.95,
        minHeight: 44,
        lineHeight: 1.2,
        whiteSpace: "nowrap",
        borderRadius: 2,
        boxShadow: "0 14px 28px rgba(47, 107, 255, 0.22)",
        background: "linear-gradient(135deg, #2F6BFF 0%, #5B8CFF 100%)",
        ...sx,
      }}
      {...props}
    >
      {children}
    </Button>
  );
}

export default CustomButton;
