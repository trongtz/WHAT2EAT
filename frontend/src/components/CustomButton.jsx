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
        color: "white",
        boxShadow: "0 14px 28px color-mix(in srgb, var(--app-primary) 28%, transparent)",
        backgroundColor: "var(--app-primary)",
        backgroundImage:
          "linear-gradient(135deg, var(--app-primary) 0%, var(--app-primary-light) 100%)",
        "&:hover": {
          backgroundColor: "var(--app-primary)",
          backgroundImage:
            "linear-gradient(135deg, var(--app-primary) 0%, var(--app-primary-light) 100%)",
          filter: "brightness(1.02)",
        },
        ...sx,
      }}
      {...props}
    >
      {children}
    </Button>
  );
}

export default CustomButton;
