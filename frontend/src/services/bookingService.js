import apiClient from "./apiClient";
import { getCachedResource, invalidateCachePrefix } from "./requestCache";

const BOOKING_HISTORY_TTL_MS = 30 * 1000;

const normalizeBooking = (booking) => ({
  ...booking,
  id: booking.id ?? booking.reservation_id,
  reservationId: booking.reservation_id ?? booking.id,
  restaurantId: booking.restaurant_id ?? booking.restaurantId,
  reservationTime: booking.reservation_time ?? booking.reservationTime,
  guestCount: Number(booking.guest_count ?? booking.guestCount ?? booking.guests ?? 0),
  notes: booking.notes ?? booking.note ?? "",
  createdAt: booking.created_at ?? booking.createdAt,
});

export const bookingService = {
  getHistory: async () => {
    return getCachedResource(
      "booking:history",
      async () => {
        const response = await apiClient.get("/bookings/my-bookings");
        return response.data.map(normalizeBooking);
      },
      { ttlMs: BOOKING_HISTORY_TTL_MS }
    );
  },
  create: async (payload) => {
    const reservationTime = new Date(`${payload.date}T${payload.time}`);
    const response = await apiClient.post("/bookings", {
      restaurant_id: payload.restaurantId,
      reservation_time: reservationTime.toISOString(),
      guest_count: Number(payload.guests),
      notes: payload.note || null,
    });
    invalidateCachePrefix("booking:history");
    invalidateCachePrefix("owner:bookings");
    invalidateCachePrefix("restaurants:detail:");
    invalidateCachePrefix("restaurants:list");
    return normalizeBooking(response.data);
  },
  cancel: async (bookingId) => {
    const response = await apiClient.put(`/bookings/${bookingId}/cancel`);
    invalidateCachePrefix("booking:history");
    invalidateCachePrefix("owner:bookings");
    invalidateCachePrefix("restaurants:detail:");
    invalidateCachePrefix("restaurants:list");
    return normalizeBooking(response.data);
  },
};
