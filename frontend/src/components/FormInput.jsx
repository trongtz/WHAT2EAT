import { TextField } from "@mui/material";

function FormInput({ sx, ...props }) {
  return (
    <TextField
      fullWidth
      size="medium"
      sx={{
        "& .MuiOutlinedInput-root": {
          borderRadius: 2,
          backgroundColor: "rgba(255,255,255,0.92)",
        },
        ...sx,
      }}
      {...props}
    />
  );
}

export default FormInput;
