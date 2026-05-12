import apiClient from "./apiClient";

const statusLabelMap = {
  PENDING: "Chờ duyệt",
  CONFIRMED: "Đã xác nhận",
  REJECTED: "Từ chối",
  CANCELLED: "Đã hủy",
};

const normalizeBooking = (booking) => {
  const reservationTime = booking.reservation_time ?? booking.reservationTime;
  const parsedDate = reservationTime ? new Date(reservationTime) : null;

  return {
    ...booking,
    id: booking.id ?? booking.reservation_id ?? booking.reservationId,
    bookingId: booking.reservation_id ?? booking.id,
    restaurantId: booking.restaurant_id ?? booking.restaurantId,
    reservationTime,
    date: parsedDate
      ? new Intl.DateTimeFormat("en-CA", {
          year: "numeric",
          month: "2-digit",
          day: "2-digit",
        }).format(parsedDate)
      : "",
    time: parsedDate
      ? new Intl.DateTimeFormat("en-GB", {
          hour: "2-digit",
          minute: "2-digit",
          hour12: false,
        }).format(parsedDate)
      : "",
    guests: booking.guest_count ?? booking.guestCount ?? 0,
    note: booking.notes ?? booking.note ?? "",
    status: statusLabelMap[booking.status] || booking.status,
  };
};

export const bookingService = {
  getHistory: async () => {
    const response = await apiClient.get("/bookings/my-bookings");
    return response.data.map(normalizeBooking);
  },

  create: async (payload) => {
    const reservationTime = new Date(`${payload.date}T${payload.time}`);
    const response = await apiClient.post("/bookings", {
      restaurant_id: payload.restaurantId,
      reservation_time: reservationTime.toISOString(),
      guest_count: Number(payload.guests),
      notes: payload.note?.trim() || null,
    });
    return normalizeBooking(response.data);
  },
};
