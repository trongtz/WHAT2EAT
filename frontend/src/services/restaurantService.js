import apiClient from "./apiClient";

export const restaurantService = {
  getRestaurants: async (params) => {
    const response = await apiClient.get("/restaurants", { params });
    return response.data;
  },
  getRestaurantDetail: async (restaurantId) => {
    const response = await apiClient.get(`/restaurants/${restaurantId}`);
    return response.data;
  },
};
