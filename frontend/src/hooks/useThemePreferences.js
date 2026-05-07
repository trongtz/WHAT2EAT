import { useContext } from "react";
import { ThemePreferencesContext } from "../context/ThemePreferencesContext";

export const useThemePreferences = () => useContext(ThemePreferencesContext);
