import { CssBaseline, ThemeProvider } from "@mui/material";
import { createContext, useEffect, useMemo, useState } from "react";
import { createAppTheme, defaultThemePreferences, themePresets } from "../utils/theme";

const THEME_STORAGE_KEY = "what2eat_theme_preferences";

export const ThemePreferencesContext = createContext(null);

const readStoredPreferences = () => {
  const rawValue = localStorage.getItem(THEME_STORAGE_KEY);
  if (!rawValue) return defaultThemePreferences;

  try {
    return { ...defaultThemePreferences, ...JSON.parse(rawValue) };
  } catch {
    return defaultThemePreferences;
  }
};

export function ThemePreferencesProvider({ children }) {
  const [preferences, setPreferences] = useState(readStoredPreferences);

  useEffect(() => {
    localStorage.setItem(THEME_STORAGE_KEY, JSON.stringify(preferences));
  }, [preferences]);

  const theme = useMemo(() => createAppTheme(preferences), [preferences]);

  const value = useMemo(
    () => ({
      preferences,
      themePresets,
      setPreset: (presetId) => setPreferences((prev) => ({ ...prev, presetId })),
      setRadius: (radius) => setPreferences((prev) => ({ ...prev, radius })),
      setDensity: (density) => setPreferences((prev) => ({ ...prev, density })),
      resetPreferences: () => setPreferences(defaultThemePreferences),
    }),
    [preferences]
  );

  return (
    <ThemePreferencesContext.Provider value={value}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </ThemeProvider>
    </ThemePreferencesContext.Provider>
  );
}
