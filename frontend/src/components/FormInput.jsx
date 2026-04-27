import { TextField } from "@mui/material";

function FormInput({ sx, ...props }) {
  return (
    <TextField
      fullWidth
      size="small"
      sx={{
        "& .MuiOutlinedInput-root": {
          borderRadius: 2,
          backgroundColor: "rgba(255,255,255,0.92)",
          minHeight: 44,
        },
        ...sx,
      }}
      {...props}
    />
  );
}

export default FormInput;
