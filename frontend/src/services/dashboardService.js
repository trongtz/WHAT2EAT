import apiClient from "./apiClient";

const normalizeOwnerReview = (review) => ({
  ...review,
  id: review.id ?? review.review_id,
  reviewId: review.review_id ?? review.id,
  restaurantId: review.restaurant_id ?? review.restaurantId,
  customerId: review.customer_id ?? review.customerId,
  createdAt: review.created_at ?? review.createdAt,
  updatedAt: review.updated_at ?? review.updatedAt,
  userName: review.userName ?? "Khách hàng",
});

export const dashboardService = {
  getOwnerRestaurants: async (ownerId) => {
    const response = await apiClient.get("/owner/restaurants", { params: { ownerId } });
    return response.data;
  },
  getOwnerBookings: async (ownerId) => {
    const response = await apiClient.get("/owner/bookings", { params: { ownerId } });
    return response.data;
  },
  getOwnerReviews: async (ownerId) => {
    const response = await apiClient.get("/owner/reviews", { params: { ownerId } });
    return Array.isArray(response.data) ? response.data.map(normalizeOwnerReview) : [];
  },
  updateOwnerRestaurant: async (payload) => {
    const response = await apiClient.post("/owner/restaurants/update", payload);
    return response.data;
  },
  createMenuItem: async (payload) => {
    const response = await apiClient.post("/owner/menu/create", payload);
    return response.data;
  },
  updateMenuItem: async (payload) => {
    const response = await apiClient.post("/owner/menu/update", payload);
    return response.data;
  },
  deleteMenuItem: async (payload) => {
    const response = await apiClient.post("/owner/menu/delete", payload);
    return response.data;
  },
  updateBookingStatus: async (payload) => {
    const response = await apiClient.post("/owner/bookings/update-status", payload);
    return response.data;
  },
  replyReview: async (payload) => {
    const response = await apiClient.post("/owner/reviews/reply", payload);
    return response.data;
  },
  getAdminUsers: async () => {
    const response = await apiClient.get("/admin/users");
    return response.data;
  },
  getAdminOverview: async () => {
    const response = await apiClient.get("/admin/overview");
    return response.data;
  },
  getAdminRestaurants: async () => {
    const response = await apiClient.get("/admin/restaurants");
    return response.data;
  },
  getPendingRestaurants: async () => {
    const response = await apiClient.get("/admin/restaurants/pending");
    return response.data;
  },
  approveRestaurant: async (restaurantId) => {
    const response = await apiClient.post("/admin/restaurants/approve", { restaurantId });
    return response.data;
  },
  rejectRestaurant: async (restaurantId) => {
    const response = await apiClient.post("/admin/restaurants/reject", { restaurantId });
    return response.data;
  },
  toggleRestaurantFeatured: async (restaurantId) => {
    const response = await apiClient.post("/admin/restaurants/toggle-featured", { restaurantId });
    return response.data;
  },
  toggleUserStatus: async (userId) => {
    const response = await apiClient.post("/admin/users/toggle-status", { userId });
    return response.data;
  },
};
