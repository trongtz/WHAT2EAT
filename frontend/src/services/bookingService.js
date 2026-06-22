import apiClient from "./apiClient";
import { invalidateCachePrefix } from "./requestCache";

const AI_RECENT_BOOKINGS_KEY = "smartfood_recent_ai_bookings";

const BOOKING_STATUS_LABELS = {
  PENDING: "Chờ duyệt",
  CONFIRMED: "Đã xác nhận",
  REJECTED: "Từ chối",
  CANCELLED: "Đã hủy",
  COMPLETED: "Hoàn thành",
};

const toDateInputValue = (value) => {
  if (!value) return "";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "" : date.toISOString().slice(0, 10);
};

const toTimeInputValue = (value) => {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit", hour12: false });
};

const buildReservationTime = (dateValue, timeValue) => {
  const reservationTime = new Date(`${dateValue}T${timeValue}`);
  if (Number.isNaN(reservationTime.getTime())) {
    throw new Error("Ngày hoặc giờ đặt bàn không hợp lệ");
  }
  return reservationTime.toISOString();
};

const normalizeBooking = (booking) => {
  const reservationTime = booking.reservation_time ?? booking.reservationTime;
  const guestCount = Number(booking.guest_count ?? booking.guestCount ?? booking.guests ?? 0);
  const notes = booking.notes ?? booking.note ?? "";

  return {
    ...booking,
    id: booking.id ?? booking.reservation_id,
    reservationId: booking.reservation_id ?? booking.id,
    restaurantId: booking.restaurant_id ?? booking.restaurantId,
    reservationTime,
    guestCount,
    guests: guestCount,
    date: booking.date ?? toDateInputValue(reservationTime),
    time: booking.time ?? toTimeInputValue(reservationTime),
    notes,
    note: notes,
    statusLabel: BOOKING_STATUS_LABELS[booking.status] || booking.status || "",
    rejectionReason: booking.rejection_reason ?? booking.rejectionReason ?? "",
    createdAt: booking.created_at ?? booking.createdAt,
  };
};

const readRecentAiBookings = () => {
  if (typeof window === "undefined") return [];
  try {
    const rawValue = window.sessionStorage.getItem(AI_RECENT_BOOKINGS_KEY);
    if (!rawValue) return [];
    const parsed = JSON.parse(rawValue);
    return Array.isArray(parsed) ? parsed.map(normalizeBooking) : [];
  } catch {
    return [];
  }
};

const writeRecentAiBookings = (bookings) => {
  if (typeof window === "undefined") return;
  window.sessionStorage.setItem(AI_RECENT_BOOKINGS_KEY, JSON.stringify(bookings));
};

export const rememberRecentAiBooking = (booking) => {
  if (!booking) return null;
  const normalized = normalizeBooking(booking);
  const current = readRecentAiBookings().filter((item) => item.id !== normalized.id);
  writeRecentAiBookings([normalized, ...current].slice(0, 20));
  return normalized;
};

export const getRecentAiBookings = () => readRecentAiBookings();

export const bookingService = {
  getHistory: async () => {
    const response = await apiClient.get("/bookings/my-bookings");
    return response.data.map(normalizeBooking);
  },
  create: async (payload) => {
    const reservationTime = buildReservationTime(payload.date, payload.time);
    const response = await apiClient.post("/bookings", {
      restaurant_id: payload.restaurantId,
      reservation_time: reservationTime,
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
  update: async (bookingId, payload) => {
    const reservationTime = buildReservationTime(payload.date, payload.time);
    const response = await apiClient.put(`/bookings/${bookingId}`, {
      reservation_time: reservationTime,
      guest_count: Number(payload.guests),
      notes: payload.note || null,
    });
    invalidateCachePrefix("booking:history");
    invalidateCachePrefix("owner:bookings");
    invalidateCachePrefix("restaurants:detail:");
    invalidateCachePrefix("restaurants:list");
    return normalizeBooking(response.data);
  },
};
