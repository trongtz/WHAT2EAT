import apiClient from "./apiClient";
import { getCachedResource, invalidateCachePrefix } from "./requestCache";
import { restaurantService } from "./restaurantService";

const OWNER_DASHBOARD_TTL_MS = 2 * 60 * 1000;
const ADMIN_OVERVIEW_TTL_MS = 2 * 60 * 1000;

const BOOKING_STATUS_LABELS = {
  PENDING: "Chờ duyệt",
  CONFIRMED: "Đã xác nhận",
  REJECTED: "Từ chối",
  CANCELLED: "Đã hủy",
  COMPLETED: "Hoàn thành",
};

const normalizeOwnerReview = (review) => ({
  ...review,
  id: review.id ?? review.review_id,
  reviewId: review.review_id ?? review.id,
  restaurantId: review.restaurant_id ?? review.restaurantId,
  restaurantName: review.restaurant_name ?? review.restaurantName ?? "",
  customerId: review.customer_id ?? review.customerId,
  createdAt: review.created_at ?? review.createdAt,
  rating: Number(review.rating || 0),
});

const normalizeOwnerBooking = (booking) => ({
  ...booking,
  id: booking.id ?? booking.reservation_id,
  reservationId: booking.reservation_id ?? booking.id,
  restaurantId: booking.restaurant_id ?? booking.restaurantId,
  createdAt: booking.created_at ?? booking.createdAt,
  reservationTime: booking.reservation_time ?? booking.reservationTime,
  notes: booking.notes ?? booking.note ?? "",
  rejectionReason: booking.rejection_reason ?? booking.rejectionReason ?? "",
  guestCount: Number(booking.guest_count ?? booking.guestCount ?? booking.guests ?? 0),
  statusLabel: BOOKING_STATUS_LABELS[booking.status] || booking.status || "",
});

const normalizeAdminUser = (user) => ({
  ...user,
  id: user.id ?? user.user_id,
  userId: user.user_id ?? user.id,
  fullName: user.fullName ?? user.full_name ?? "",
  avatarUrl: user.avatarUrl ?? user.avatar_url ?? null,
  role: typeof user.role === "string" ? user.role.toLowerCase() : user.role,
  status: typeof user.status === "string" ? user.status.toLowerCase() : user.status,
  createdAt: user.created_at ?? user.createdAt,
});

export const dashboardService = {
  getOwnerRestaurants: async (ownerId) => restaurantService.getOwnerRestaurants(ownerId),

  getOwnerBookings: async () => {
    const response = await apiClient.get("/owner/bookings");
    return response.data.map(normalizeOwnerBooking);
  },

  getOwnerReviews: async ({ skip = 0, limit = 100, restaurantId = null } = {}) => {
    return getCachedResource(
      `owner:reviews:${skip}:${limit}:${restaurantId || "all"}`,
      async () => {
        const response = await apiClient.get("/owner/reviews", { params: { skip, limit, restaurant_id: restaurantId || undefined } });
        return response.data.map(normalizeOwnerReview);
      },
      { ttlMs: OWNER_DASHBOARD_TTL_MS }
    );
  },

  updateBookingStatus: async (payload) => {
    const response = await apiClient.post("/owner/bookings/update-status", payload);
    invalidateCachePrefix("owner:bookings");
    invalidateCachePrefix("admin:overview");
    invalidateCachePrefix("restaurants:list");
    invalidateCachePrefix("restaurants:detail:");
    invalidateCachePrefix("restaurants:owner:");
    invalidateCachePrefix("restaurants:manage:");
    return normalizeOwnerBooking(response.data);
  },

  markBookingCheckin: async (payload) => {
    const response = await apiClient.post("/owner/bookings/check-in", payload);
    invalidateCachePrefix("owner:bookings");
    invalidateCachePrefix("admin:overview");
    invalidateCachePrefix("restaurants:list");
    invalidateCachePrefix("restaurants:detail:");
    invalidateCachePrefix("restaurants:owner:");
    invalidateCachePrefix("restaurants:manage:");
    return normalizeOwnerBooking(response.data);
  },

  getAdminOverview: async (options = {}) => {
    return getCachedResource(
      "admin:overview",
      async () => {
        const response = await apiClient.get("/admin/overview");
        return response.data;
      },
      { ttlMs: ADMIN_OVERVIEW_TTL_MS, forceRefresh: options.forceRefresh }
    );
  },

  getAdminRestaurants: async (status) => restaurantService.getAdminRestaurants(status),

  getAdminUsers: async () => {
    const response = await apiClient.get("/admin/users");
    return response.data.map(normalizeAdminUser);
  },

  toggleUserStatus: async (userId) => {
    const response = await apiClient.put(`/admin/users/${userId}/toggle-status`);
    invalidateCachePrefix("admin:overview");
    return normalizeAdminUser(response.data);
  },
};
