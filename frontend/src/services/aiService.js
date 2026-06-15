import apiClient from "./apiClient";
import { normalizeRestaurant } from "./restaurantService";

export const aiService = {
  recommend: async (payload) => {
    const query = payload?.query ?? payload?.prompt ?? "";
    const response = await apiClient.post("/ai/recommend", {
      query,
      latitude: payload?.latitude,
      longitude: payload?.longitude,
      session_id: payload?.session_id ?? payload?.sessionId,
    });
    const data = response.data || {};

    return {
      message: data.message ?? "",
      sessionId: data.session_id ?? payload?.session_id ?? payload?.sessionId,
      source: data.source ?? "AI",
      agent: data.agent ?? null,
      booking: data.booking ?? null,
      restaurants: Array.isArray(data.recommended_restaurants)
        ? data.recommended_restaurants.map(normalizeRestaurant)
        : [],
    };
  },
};
