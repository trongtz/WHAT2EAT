import apiClient from "./apiClient";

export const bookingService = {
  getHistory: async (userId) => {
    const response = await apiClient.get("/bookings", { params: { userId } });
    return response.data;
  },
  create: async (payload) => {
    const response = await apiClient.post("/bookings", payload);
    return response.data;
  },
};
