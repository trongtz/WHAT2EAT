const guestSessionKeys = {
  favorites: "smartfood_guest_favorites",
  bookings: "smartfood_guest_bookings",
  reviews: "smartfood_guest_reviews",
};

const readSessionArray = (key) => {
  const rawValue = sessionStorage.getItem(key);
  if (!rawValue) return [];

  try {
    const parsedValue = JSON.parse(rawValue);
    return Array.isArray(parsedValue) ? parsedValue : [];
  } catch {
    return [];
  }
};

const writeSessionArray = (key, value) => {
  sessionStorage.setItem(key, JSON.stringify(value));
};

export const createGuestUser = () => ({
  id: "guest",
  fullName: "Khách",
  email: "",
  phone: "",
  role: "guest",
  status: "active",
  isGuest: true,
});

export const clearGuestSessionData = () => {
  Object.values(guestSessionKeys).forEach((key) => {
    sessionStorage.removeItem(key);
  });
};

export const getGuestFavoriteIds = () => readSessionArray(guestSessionKeys.favorites);

export const toggleGuestFavorite = (restaurantId) => {
  const normalizedRestaurantId = String(restaurantId);
  const favoriteIds = getGuestFavoriteIds();
  const nextFavoriteIds = favoriteIds.includes(normalizedRestaurantId)
    ? favoriteIds.filter((id) => id !== normalizedRestaurantId)
    : [...favoriteIds, normalizedRestaurantId];

  writeSessionArray(guestSessionKeys.favorites, nextFavoriteIds);
  return nextFavoriteIds;
};

export const getGuestBookings = () => readSessionArray(guestSessionKeys.bookings);

export const createGuestBooking = (payload) => {
  const nextBooking = {
    id: Date.now(),
    userId: "guest",
    restaurantId: Number(payload.restaurantId),
    date: payload.date,
    time: payload.time,
    guests: Number(payload.guests),
    note: payload.note || "",
    status: "Chờ duyệt",
    createdAt: new Date().toISOString(),
  };

  const nextBookings = [nextBooking, ...getGuestBookings()];
  writeSessionArray(guestSessionKeys.bookings, nextBookings);
  return nextBooking;
};

export const getGuestReviews = () => readSessionArray(guestSessionKeys.reviews);

export const getGuestReviewsByRestaurant = (restaurantId) =>
  getGuestReviews().filter((review) => review.restaurantId === Number(restaurantId));

export const createGuestReview = (payload) => {
  const nextReview = {
    id: Date.now(),
    restaurantId: Number(payload.restaurantId),
    rating: Number(payload.rating),
    comment: payload.comment,
    userName: payload.userName,
    createdAt: new Date().toISOString(),
  };

  const nextReviews = [nextReview, ...getGuestReviews()];
  writeSessionArray(guestSessionKeys.reviews, nextReviews);
  return nextReview;
};
