import apiClient from "./apiClient";
import { getPriceRangeLabel } from "../utils/helpers";

const normalizeMenuItem = (item) => ({
  ...item,
  id: item.id ?? item.item_id,
  itemId: item.item_id ?? item.id,
  restaurantId: item.restaurant_id ?? item.restaurantId,
  price: Number(item.price || 0),
  imageUrl: item.image_url ?? item.imageUrl ?? "",
  isAvailable: item.is_available ?? item.isAvailable ?? true,
});

const normalizeReview = (review) => ({
  ...review,
  id: review.id ?? review.review_id,
  reviewId: review.review_id ?? review.id,
  restaurantId: review.restaurant_id ?? review.restaurantId,
  customerId: review.customer_id ?? review.customerId,
  rating: Number(review.rating || 0),
  comment: review.comment ?? "",
  userName: review.userName ?? "Khách hàng",
  createdAt: review.created_at ?? review.createdAt,
});

const normalizeRestaurant = (restaurant) => {
  const images = Array.isArray(restaurant.images) ? restaurant.images.filter(Boolean) : [];
  const status = restaurant.status ?? "PENDING";
  const priceRange = restaurant.price_range ?? restaurant.priceRange ?? "";
  const cuisineType = restaurant.cuisine_type ?? restaurant.cuisineType ?? "";
  const cuisineTags = String(cuisineType)
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
  const menu = Array.isArray(restaurant.menu) ? restaurant.menu.map(normalizeMenuItem) : [];
  const reviewsList = Array.isArray(restaurant.reviewsList)
    ? restaurant.reviewsList.map(normalizeReview)
    : [];
  const reviewCount = Number(
    restaurant.review_count ?? restaurant.reviewCount ?? restaurant.reviews ?? reviewsList.length ?? 0
  );

  return {
    ...restaurant,
    id: restaurant.id ?? restaurant.restaurant_id,
    restaurantId: restaurant.restaurant_id ?? restaurant.id,
    ownerId: restaurant.owner_id ?? restaurant.ownerId,
    ownerName: restaurant.owner_name ?? restaurant.ownerName ?? "",
    ownerEmail: restaurant.owner_email ?? restaurant.ownerEmail ?? "",
    averageRating: Number(restaurant.average_rating ?? restaurant.averageRating ?? 0),
    rating: Number(restaurant.average_rating ?? restaurant.averageRating ?? 0),
    reviewCount,
    approved: status === "APPROVED",
    status,
    category: cuisineTags[0] || cuisineType,
    cuisineType,
    priceRange,
    priceRangeLabel: getPriceRangeLabel(priceRange),
    latitude:
      restaurant.latitude === null || restaurant.latitude === undefined || restaurant.latitude === ""
        ? null
        : Number(restaurant.latitude),
    longitude:
      restaurant.longitude === null || restaurant.longitude === undefined || restaurant.longitude === ""
        ? null
        : Number(restaurant.longitude),
    openHours: restaurant.open_hours ?? restaurant.openHours ?? "",
    maxCapacity: Number(restaurant.max_capacity ?? restaurant.maxCapacity ?? 0),
    availableCapacity: Number(restaurant.available_capacity ?? restaurant.availableCapacity ?? 0),
    description: restaurant.description ?? "",
    images,
    image: images[0] || "",
    tags: [...cuisineTags, getPriceRangeLabel(priceRange)].filter(Boolean),
    menu,
    reviewsList,
    reviews: reviewCount,
    createdAt: restaurant.created_at ?? restaurant.createdAt,
    updatedAt: restaurant.updated_at ?? restaurant.updatedAt,
    phone: restaurant.phone ?? "",
    address: restaurant.address ?? "",
  };
};

const mapRestaurantPayload = (payload) => ({
  name: payload.name?.trim(),
  address: payload.address?.trim(),
  phone: payload.phone?.trim(),
  description: payload.description?.trim() || null,
  latitude: payload.latitude === "" || payload.latitude == null ? null : Number(payload.latitude),
  longitude: payload.longitude === "" || payload.longitude == null ? null : Number(payload.longitude),
  open_hours: payload.open_hours?.trim() || null,
  max_capacity: Number(payload.max_capacity),
  images: payload.images ?? [],
  cuisine_type: payload.cuisine_type?.trim() || null,
  price_range: payload.price_range || null,
});

export const restaurantService = {
  getRestaurants: async (params) => {
    const response = await apiClient.get("/restaurants", { params });
    return response.data.map(normalizeRestaurant);
  },

  getRestaurantDetail: async (restaurantId) => {
    const [restaurantResponse, menuResponse, reviewResponse] = await Promise.all([
      apiClient.get(`/restaurants/${restaurantId}`),
      apiClient.get(`/restaurants/${restaurantId}/menu`),
      apiClient.get(`/restaurants/${restaurantId}/reviews`),
    ]);

    return normalizeRestaurant({
      ...restaurantResponse.data,
      menu: menuResponse.data,
      reviewsList: reviewResponse.data,
      reviews: reviewResponse.data.length,
    });
  },

  getOwnerRestaurants: async (ownerId) => {
    const response = await apiClient.get(`/restaurants/owner/${ownerId}`);
    return response.data.map(normalizeRestaurant);
  },

  getManageRestaurant: async (restaurantId) => {
    const [restaurantResponse, menuResponse] = await Promise.all([
      apiClient.get(`/restaurants/manage/${restaurantId}`),
      apiClient.get(`/dishes/restaurant/${restaurantId}`),
    ]);

    return normalizeRestaurant({
      ...restaurantResponse.data,
      menu: menuResponse.data,
    });
  },

  createRestaurant: async (payload) => {
    const response = await apiClient.post("/restaurants", mapRestaurantPayload(payload));
    return normalizeRestaurant(response.data);
  },

  updateRestaurant: async (restaurantId, payload) => {
    const response = await apiClient.put(`/restaurants/${restaurantId}`, mapRestaurantPayload(payload));
    return normalizeRestaurant(response.data);
  },

  getRestaurantMenu: async (restaurantId) => {
    const response = await apiClient.get(`/dishes/restaurant/${restaurantId}`);
    return response.data.map(normalizeMenuItem);
  },

  createMenuItem: async (restaurantId, payload) => {
    const response = await apiClient.post(`/dishes/restaurant/${restaurantId}`, {
      name: payload.name?.trim(),
      description: payload.description?.trim() || null,
      price: Number(payload.price),
      category: payload.category?.trim() || null,
      image_url: payload.image_url?.trim() || null,
      is_available: Boolean(payload.is_available),
    });
    return normalizeMenuItem(response.data);
  },

  updateMenuItem: async (itemId, payload) => {
    const response = await apiClient.put(`/dishes/${itemId}`, {
      name: payload.name?.trim(),
      description: payload.description?.trim() || null,
      price: Number(payload.price),
      category: payload.category?.trim() || null,
      image_url: payload.image_url?.trim() || null,
      is_available: Boolean(payload.is_available),
    });
    return normalizeMenuItem(response.data);
  },

  deleteMenuItem: async (itemId) => {
    await apiClient.delete(`/dishes/${itemId}`);
  },

  getAdminRestaurants: async (status) => {
    const response = await apiClient.get("/admin/restaurants", {
      params: status ? { status } : undefined,
    });
    return response.data.map(normalizeRestaurant);
  },

  updateAdminRestaurantStatus: async (restaurantId, status) => {
    const response = await apiClient.put(`/admin/restaurants/${restaurantId}/status`, { status });
    return normalizeRestaurant(response.data);
  },
};
