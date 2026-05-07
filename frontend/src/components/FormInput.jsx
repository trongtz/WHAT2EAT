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
        },
        ...sx,
      }}
      {...props}
    />
  );
}

export default FormInput;
