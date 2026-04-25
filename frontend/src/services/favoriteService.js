import apiClient from "./apiClient";

export const favoriteService = {
  getFavorites: async (userId) => {
    const response = await apiClient.get("/favorites", { params: { userId } });
    return response.data;
  },
  toggle: async (payload) => {
    const response = await apiClient.post("/favorites/toggle", payload);
    return response.data;
  },
};
