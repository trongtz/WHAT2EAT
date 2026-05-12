import { TextField } from "@mui/material";

function FormInput({ sx, ...props }) {
  return (
    <TextField
      fullWidth
      size="small"
      sx={{
        "& .MuiOutlinedInput-root": {
          borderRadius: 2,
          backgroundColor: "var(--app-surface-strong)",
          minHeight: 44,
          transition: "box-shadow 0.2s ease, border-color 0.2s ease, background-color 0.2s ease",
          "& fieldset": {
            borderColor: "color-mix(in srgb, var(--app-text-primary) 16%, white)",
          },
          "&:hover fieldset": {
            borderColor: "color-mix(in srgb, var(--app-primary) 34%, white)",
          },
          "&.Mui-focused": {
            boxShadow: "0 0 0 4px color-mix(in srgb, var(--app-primary) 12%, transparent)",
          },
          "&.Mui-focused fieldset": {
            borderColor: "var(--app-primary)",
            borderWidth: "1px",
          },
        },
        "& .MuiInputLabel-root.Mui-focused": {
          color: "var(--app-primary)",
        },
        "& .MuiFormHelperText-root.Mui-error": {
          color: "var(--app-error)",
        },
        ...sx,
      }}
      {...props}
    />
  );
}

export default FormInput;
