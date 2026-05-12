import apiClient from "./apiClient";
import { getCachedResource, invalidateCachePrefix } from "./requestCache";
import { restaurantService } from "./restaurantService";

const OWNER_DASHBOARD_TTL_MS = 30 * 1000;
const ADMIN_OVERVIEW_TTL_MS = 30 * 1000;

const normalizeOwnerReview = (review) => ({
  ...review,
  id: review.id ?? review.review_id,
  reviewId: review.review_id ?? review.id,
  restaurantId: review.restaurant_id ?? review.restaurantId,
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
  guestCount: Number(booking.guest_count ?? booking.guestCount ?? booking.guests ?? 0),
});

export const dashboardService = {
  getOwnerRestaurants: async (ownerId) => restaurantService.getOwnerRestaurants(ownerId),

  getOwnerBookings: async () => {
    return getCachedResource(
      "owner:bookings",
      async () => {
        const response = await apiClient.get("/owner/bookings");
        return response.data.map(normalizeOwnerBooking);
      },
      { ttlMs: OWNER_DASHBOARD_TTL_MS }
    );
  },

  getOwnerReviews: async () => {
    return getCachedResource(
      "owner:reviews",
      async () => {
        const response = await apiClient.get("/owner/reviews");
        return response.data.map(normalizeOwnerReview);
      },
      { ttlMs: OWNER_DASHBOARD_TTL_MS }
    );
  },

  updateBookingStatus: async (payload) => {
    const response = await apiClient.post("/owner/bookings/update-status", payload);
    invalidateCachePrefix("owner:bookings");
    invalidateCachePrefix("admin:overview");
    return normalizeOwnerBooking(response.data);
  },

  getAdminOverview: async () => {
    return getCachedResource(
      "admin:overview",
      async () => {
        const response = await apiClient.get("/admin/overview");
        return response.data;
      },
      { ttlMs: ADMIN_OVERVIEW_TTL_MS }
    );
  },

  getAdminRestaurants: async (status) => restaurantService.getAdminRestaurants(status),
};
