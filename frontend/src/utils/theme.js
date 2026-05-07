import { alpha, createTheme } from "@mui/material/styles";

export const themePresets = [
  {
    id: "citrus",
    name: "Cam nắng",
    description: "Ấm, ngon mắt và hợp với cảm giác khám phá món ăn.",
    colors: {
      primary: "#FF8A2A",
      primaryLight: "#FFB347",
      primaryDark: "#E66C0F",
      secondary: "#4A90E2",
      secondaryLight: "#7AB5FF",
      secondaryDark: "#2C6CC7",
      success: "#22B573",
      error: "#E15B64",
      background: "#F7F8FA",
      backgroundElevated: "#FFF6EE",
      paper: "#FFFFFF",
      textPrimary: "#18212F",
      textSecondary: "#667085",
      surfaceGlowA: "rgba(255, 167, 81, 0.18)",
      surfaceGlowB: "rgba(74, 144, 226, 0.16)",
      bodyGlowA: "rgba(255, 167, 81, 0.12)",
      bodyGlowB: "rgba(74, 144, 226, 0.10)",
      glassBg: "rgba(255, 250, 245, 0.84)",
      glassBorder: "rgba(255, 255, 255, 0.72)",
      glassShadow: "rgba(15, 23, 42, 0.08)",
      surfaceSoft: "rgba(255,255,255,0.72)",
      surfaceMuted: "rgba(255,248,241,0.86)",
      surfaceStrong: "rgba(255,255,255,0.92)",
    },
  },
  {
    id: "coastal",
    name: "Biển dịu",
    description: "Mát, sạch và sáng theo tinh thần bản đồ ven biển hiện đại.",
    colors: {
      primary: "#1C7ED6",
      primaryLight: "#5DA9F6",
      primaryDark: "#155E9E",
      secondary: "#14B8A6",
      secondaryLight: "#5EEAD4",
      secondaryDark: "#0F8F82",
      success: "#2FBF71",
      error: "#E76F51",
      background: "#F3F8FC",
      backgroundElevated: "#EAF4FB",
      paper: "#FFFFFF",
      textPrimary: "#14324A",
      textSecondary: "#5F7A8F",
      surfaceGlowA: "rgba(28, 126, 214, 0.16)",
      surfaceGlowB: "rgba(20, 184, 166, 0.14)",
      bodyGlowA: "rgba(28, 126, 214, 0.12)",
      bodyGlowB: "rgba(20, 184, 166, 0.10)",
      glassBg: "rgba(248, 252, 255, 0.88)",
      glassBorder: "rgba(255, 255, 255, 0.78)",
      glassShadow: "rgba(20, 50, 74, 0.09)",
      surfaceSoft: "rgba(255,255,255,0.74)",
      surfaceMuted: "rgba(239,248,253,0.88)",
      surfaceStrong: "rgba(255,255,255,0.94)",
    },
  },
  {
    id: "matcha",
    name: "Matcha thanh",
    description: "Xanh dịu, tinh hơn và bớt cảm giác app đại trà.",
    colors: {
      primary: "#2F855A",
      primaryLight: "#68D391",
      primaryDark: "#276749",
      secondary: "#C08457",
      secondaryLight: "#E6B98C",
      secondaryDark: "#9A6238",
      success: "#38A169",
      error: "#D64550",
      background: "#F5F7F2",
      backgroundElevated: "#EEF5EA",
      paper: "#FFFEFB",
      textPrimary: "#1F2D24",
      textSecondary: "#66776C",
      surfaceGlowA: "rgba(104, 211, 145, 0.18)",
      surfaceGlowB: "rgba(192, 132, 87, 0.14)",
      bodyGlowA: "rgba(104, 211, 145, 0.11)",
      bodyGlowB: "rgba(192, 132, 87, 0.10)",
      glassBg: "rgba(255, 254, 251, 0.86)",
      glassBorder: "rgba(255, 255, 255, 0.74)",
      glassShadow: "rgba(31, 45, 36, 0.08)",
      surfaceSoft: "rgba(255,252,247,0.76)",
      surfaceMuted: "rgba(244,249,240,0.90)",
      surfaceStrong: "rgba(255,255,252,0.95)",
    },
  },
];

export const defaultThemePreferences = {
  presetId: "citrus",
  radius: 12,
  density: "cozy",
};

export const getThemePreset = (presetId) =>
  themePresets.find((preset) => preset.id === presetId) || themePresets[0];

export const createAppTheme = (preferences = defaultThemePreferences) => {
  const preset = getThemePreset(preferences.presetId);
  const radius = preferences.radius ?? defaultThemePreferences.radius;
  const density = preferences.density ?? defaultThemePreferences.density;
  const spacingScale = density === "compact" ? 0.92 : density === "airy" ? 1.08 : 1;

  return createTheme({
    palette: {
      primary: {
        main: preset.colors.primary,
        light: preset.colors.primaryLight,
        dark: preset.colors.primaryDark,
      },
      secondary: {
        main: preset.colors.secondary,
        light: preset.colors.secondaryLight,
        dark: preset.colors.secondaryDark,
      },
      success: {
        main: preset.colors.success,
      },
      error: {
        main: preset.colors.error,
      },
      background: {
        default: preset.colors.background,
        paper: preset.colors.paper,
      },
      text: {
        primary: preset.colors.textPrimary,
        secondary: preset.colors.textSecondary,
      },
    },
    shape: {
      borderRadius: radius,
    },
    spacing: 8 * spacingScale,
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
      MuiCssBaseline: {
        styleOverrides: {
          ":root": {
            "--app-surface-glow-a": preset.colors.surfaceGlowA,
            "--app-surface-glow-b": preset.colors.surfaceGlowB,
            "--app-body-glow-a": preset.colors.bodyGlowA,
            "--app-body-glow-b": preset.colors.bodyGlowB,
            "--app-glass-bg": preset.colors.glassBg,
            "--app-glass-border": preset.colors.glassBorder,
            "--app-glass-shadow": preset.colors.glassShadow,
            "--app-avatar-a": preset.colors.primary,
            "--app-avatar-b": preset.colors.primaryLight,
            "--app-primary": preset.colors.primary,
            "--app-primary-light": preset.colors.primaryLight,
            "--app-primary-dark": preset.colors.primaryDark,
            "--app-secondary": preset.colors.secondary,
            "--app-secondary-light": preset.colors.secondaryLight,
            "--app-secondary-dark": preset.colors.secondaryDark,
            "--app-text-primary": preset.colors.textPrimary,
            "--app-text-secondary": preset.colors.textSecondary,
            "--app-background": preset.colors.background,
            "--app-background-elevated": preset.colors.backgroundElevated,
            "--app-paper": preset.colors.paper,
            "--app-surface-soft": preset.colors.surfaceSoft,
            "--app-surface-muted": preset.colors.surfaceMuted,
            "--app-surface-strong": preset.colors.surfaceStrong,
            "--app-success": preset.colors.success,
            "--app-error": preset.colors.error,
            "--app-primary-gradient": `linear-gradient(135deg, ${preset.colors.primary} 0%, ${preset.colors.primaryLight} 100%)`,
            "--app-secondary-gradient": `linear-gradient(135deg, ${preset.colors.secondary} 0%, ${preset.colors.secondaryLight} 100%)`,
            "--app-shell-gradient": `linear-gradient(180deg, ${preset.colors.backgroundElevated} 0%, ${preset.colors.background} 100%)`,
          },
          body: {
            color: preset.colors.textPrimary,
            background: `
              radial-gradient(circle at top left, ${preset.colors.bodyGlowA}, transparent 22%),
              radial-gradient(circle at 85% 10%, ${preset.colors.bodyGlowB}, transparent 18%),
              ${preset.colors.background}
            `,
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: radius + 2,
            boxShadow: `0 22px 50px ${alpha(preset.colors.textPrimary, 0.08)}`,
          },
        },
      },
      MuiButton: {
        styleOverrides: {
          root: {
            borderRadius: radius,
            paddingInline: density === "compact" ? 16 : 18,
            minHeight: density === "compact" ? 42 : density === "airy" ? 46 : 44,
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
            borderRadius: radius,
          },
        },
      },
    },
  });
};
