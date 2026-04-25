import apiClient from "./apiClient";

export const reviewService = {
  create: async (payload) => {
    const response = await apiClient.post("/reviews", payload);
    return response.data;
  },
};
