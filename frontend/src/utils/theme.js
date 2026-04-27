import { createTheme } from "@mui/material/styles";

export const appTheme = createTheme({
  palette: {
    primary: {
      main: "#FF8A2A",
      light: "#FFB347",
      dark: "#E66C0F",
    },
    secondary: {
      main: "#4A90E2",
    },
    success: {
      main: "#22B573",
    },
    error: {
      main: "#E15B64",
    },
    background: {
      default: "#F7F8FA",
      paper: "#FFFFFF",
    },
    text: {
      primary: "#18212F",
      secondary: "#667085",
    },
  },
  shape: {
    borderRadius: 12,
  },
  typography: {
    fontFamily: '"Inter", "SF Pro Display", "Segoe UI", sans-serif',
    h1: { fontSize: "clamp(2.7rem, 5vw, 4.6rem)", fontWeight: 800, letterSpacing: "-0.04em" },
    h2: { fontSize: "clamp(2rem, 3vw, 3rem)", fontWeight: 800, letterSpacing: "-0.03em" },
    h3: { fontSize: "clamp(1.5rem, 2.1vw, 2.15rem)", fontWeight: 750, letterSpacing: "-0.02em" },
    h4: { fontSize: "1.15rem", fontWeight: 700, letterSpacing: "-0.01em" },
    body1: { fontSize: "1rem", lineHeight: 1.7 },
    body2: { lineHeight: 1.6 },
    button: { fontWeight: 700, textTransform: "none" },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 14,
          boxShadow: "0 22px 50px rgba(15, 23, 42, 0.08)",
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          paddingInline: 18,
          minHeight: 44,
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 999,
          fontWeight: 700,
        },
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          borderRadius: 12,
        },
      },
    },
  },
});
