import apiClient from "./apiClient";

export const authService = {
  login: async (payload) => {
    const response = await apiClient.post("/auth/login", payload);
    return response.data;
  },
  register: async (payload) => {
    const response = await apiClient.post("/auth/register", payload);
    return response.data;
  },
  updateProfile: async (payload) => {
    const response = await apiClient.post("/profile/update", payload);
    return response.data;
  },
};
