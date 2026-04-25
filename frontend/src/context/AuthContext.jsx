import { createContext, useEffect, useMemo, useState } from "react";
import { authService } from "../services/authService";
import {
  clearStoredAuth,
  getStoredToken,
  getStoredUser,
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
      setStoredAuth(response);
      setUser(response.user);
      setToken(response.token);
      return response;
    } finally {
      setLoading(false);
    }
  };

  const register = async (payload) => {
    setLoading(true);
    try {
      const response = await authService.register(payload);
      setStoredAuth(response);
      setUser(response.user);
      setToken(response.token);
      return response;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    clearStoredAuth();
    setUser(null);
    setToken(null);
  };

  const updateUser = (nextUser) => {
    setUser(nextUser);
    localStorage.setItem(storageKeys.user, JSON.stringify(nextUser));
  };

  const value = useMemo(
    () => ({
      user,
      token,
      isAuthenticated: Boolean(token),
      loading,
      login,
      register,
      updateUser,
      logout,
    }),
    [user, token, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
