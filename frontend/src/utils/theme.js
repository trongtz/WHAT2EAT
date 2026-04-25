import { createTheme } from "@mui/material/styles";

export const appTheme = createTheme({
  palette: {
    primary: {
      main: "#2F6BFF",
      light: "#6F97FF",
      dark: "#214AB5",
    },
    secondary: {
      main: "#FF9F1C",
    },
    success: {
      main: "#20B486",
    },
    error: {
      main: "#E85D75",
    },
    background: {
      default: "#F7F9FF",
      paper: "#FFFFFF",
    },
    text: {
      primary: "#1C2440",
      secondary: "#5E6786",
    },
  },
  shape: {
    borderRadius: 6,
  },
  typography: {
    fontFamily: '"Be Vietnam Pro", "Segoe UI", sans-serif',
    h1: { fontSize: "2.6rem", fontWeight: 800 },
    h2: { fontSize: "2rem", fontWeight: 800 },
    h3: { fontSize: "1.5rem", fontWeight: 700 },
    h4: { fontSize: "1.25rem", fontWeight: 700 },
    button: { fontWeight: 700, textTransform: "none" },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 6,
          boxShadow: "0 22px 44px rgba(28, 36, 64, 0.08)",
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 6,
          paddingInline: 18,
          minHeight: 44,
        },
      },
    },
  },
});
