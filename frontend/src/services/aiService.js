import apiClient from "./apiClient";

export const aiService = {
  recommend: async (payload) => {
    const response = await apiClient.post("/ai/recommend", payload);
    return response.data;
  },
};
