import { createContext, useEffect, useMemo, useState } from "react";
import { authService } from "../services/authService";
import { clearAllCachedResources } from "../services/requestCache";
import { clearGuestSessionData, createGuestUser } from "../utils/guestSession";
import {
  GUEST_AUTH_TOKEN,
  clearStoredAuth,
  getStoredToken,
  getStoredUser,
  normalizeStoredUser,
  setStoredAuth,
  storageKeys,
} from "../utils/storage";

export const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(getStoredUser());
  const [token, setToken] = useState(getStoredToken());
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!token) setUser(null);
  }, [token]);

  const login = async (payload) => {
    setLoading(true);
    try {
      const response = await authService.login(payload);
      const normalizedResponse = {
        ...response,
        user: normalizeStoredUser(response.user),
      };
      clearAllCachedResources();
      clearGuestSessionData();
      setStoredAuth(normalizedResponse);
      setUser(normalizedResponse.user);
      setToken(normalizedResponse.token);
      return normalizedResponse;
    } finally {
      setLoading(false);
    }
  };

  const register = async (payload) => {
    setLoading(true);
    try {
      const response = await authService.register(payload);
      return response;
    } finally {
      setLoading(false);
    }
  };

  const loginAsGuest = async () => {
    setLoading(true);
    try {
      const guestUser = createGuestUser();
      clearAllCachedResources();
      clearStoredAuth();
      clearGuestSessionData();
      setStoredAuth({ token: GUEST_AUTH_TOKEN, user: guestUser });
      setUser(guestUser);
      setToken(GUEST_AUTH_TOKEN);
      return { token: GUEST_AUTH_TOKEN, user: guestUser };
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    clearAllCachedResources();
    clearStoredAuth();
    clearGuestSessionData();
    setUser(null);
    setToken(null);
  };

  const updateUser = (nextUser) => {
    const normalizedUser = normalizeStoredUser(nextUser);
    setUser(normalizedUser);
    sessionStorage.setItem(storageKeys.user, JSON.stringify(normalizedUser));
  };

  const value = useMemo(
    () => ({
      user,
      token,
      isAuthenticated: Boolean(token),
      loading,
      login,
      loginAsGuest,
      register,
      updateUser,
      logout,
    }),
    [user, token, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
