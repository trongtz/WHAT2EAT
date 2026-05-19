import apiClient from "./apiClient";
import { getCachedResource, invalidateCachePrefix } from "./requestCache";
import { getPriceRangeLabel, getPrimaryOpenHoursValue } from "../utils/helpers";

const RESTAURANT_LIST_TTL_MS = 5 * 60 * 1000;
const RESTAURANT_DETAIL_TTL_MS = 5 * 60 * 1000;
const OWNER_RESTAURANTS_TTL_MS = 5 * 60 * 1000;
const OWNER_MANAGE_TTL_MS = 3 * 60 * 1000;
const MENU_TTL_MS = 3 * 60 * 1000;
const ADMIN_TTL_MS = 2 * 60 * 1000;

const stableSerialize = (value) => JSON.stringify(value || {});

const invalidateRestaurantCaches = (restaurantId, ownerId) => {
  invalidateCachePrefix("restaurants:list");
  invalidateCachePrefix("restaurants:detail:");
  invalidateCachePrefix("restaurants:menu:");
  invalidateCachePrefix("restaurants:owner:");
  invalidateCachePrefix("restaurants:manage:");
  invalidateCachePrefix("admin:restaurants");
  invalidateCachePrefix("admin:overview");
  invalidateCachePrefix("owner:bookings");
  invalidateCachePrefix("owner:reviews");

  if (restaurantId) {
    invalidateCachePrefix(`restaurants:detail:${restaurantId}`);
    invalidateCachePrefix(`restaurants:menu:${restaurantId}`);
    invalidateCachePrefix(`restaurants:manage:${restaurantId}`);
  }

  if (ownerId) {
    invalidateCachePrefix(`restaurants:owner:${ownerId}`);
  }
};

const normalizeMenuItem = (item) => ({
  ...item,
  id: item.id ?? item.item_id,
  itemId: item.item_id ?? item.id,
  restaurantId: item.restaurant_id ?? item.restaurantId,
  price: Number(item.price || 0),
  imageUrl: item.image_url ?? item.imageUrl ?? "",
  availabilityStatus: item.availability_status ?? item.availabilityStatus ?? (item.is_available === false ? "UNAVAILABLE" : "AVAILABLE"),
  isAvailable: item.is_available ?? item.isAvailable ?? item.availability_status !== "UNAVAILABLE",
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

const normalizeOpenHoursValue = (restaurant) =>
  getPrimaryOpenHoursValue(restaurant.open_hours ?? restaurant.opening_hours ?? restaurant.openHours);

const mapOpeningHoursPayload = (payload) => {
  const value = payload.open_hours?.trim() || payload.opening_hours || null;
  if (!value) return null;
  if (typeof value === "object") return value;
  return {
    regular: value,
    special_days: payload.special_days ?? payload.specialDays ?? [],
  };
};

export const normalizeRestaurant = (restaurant) => {
  const images = Array.isArray(restaurant.images) ? restaurant.images.filter(Boolean) : [];
  const status = restaurant.approval_status ?? restaurant.status ?? "PENDING";
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
    averageRating: Number(restaurant.rating_avg ?? restaurant.average_rating ?? restaurant.averageRating ?? 0),
    rating: Number(restaurant.rating_avg ?? restaurant.average_rating ?? restaurant.averageRating ?? 0),
    reviewCount,
    menuCount: Number(restaurant.menu_count ?? restaurant.menuCount ?? menu.length),
    approved: status === "APPROVED",
    status,
    approvalStatus: status,
    isActive: restaurant.is_active ?? restaurant.isActive ?? true,
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
    openHours: normalizeOpenHoursValue(restaurant),
    maxCapacity: Number(restaurant.max_tables ?? restaurant.max_capacity ?? restaurant.maxCapacity ?? 0),
    availableCapacity: Number(
      restaurant.available_tables ?? restaurant.available_capacity ?? restaurant.availableCapacity ?? 0
    ),
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
  opening_hours: mapOpeningHoursPayload(payload),
  max_capacity: Number(payload.max_capacity),
  images: payload.images ?? [],
  cuisine_type: payload.cuisine_type?.trim() || null,
  price_range: payload.price_range || null,
});

export const restaurantService = {
  getRestaurants: async (params) => {
    const hasFilters =
      params &&
      Object.values({
        keyword: params.keyword,
        category: params.category,
        price: params.price,
      }).some(Boolean);
    const apiParams = hasFilters
      ? {
          query: params.keyword || undefined,
          cuisine_type: params.category || undefined,
          price_range: params.price || undefined,
        }
      : params;
    const cacheKey = `restaurants:list:${hasFilters ? "search" : "all"}:${stableSerialize(apiParams)}`;

    return getCachedResource(
      cacheKey,
      async () => {
        const response = await apiClient.get(hasFilters ? "/restaurants/search" : "/restaurants", { params: apiParams });
        return response.data.map(normalizeRestaurant);
      },
      { ttlMs: RESTAURANT_LIST_TTL_MS }
    );
  },

  getRestaurantDetail: async (restaurantId) => {
    return getCachedResource(
      `restaurants:detail:${restaurantId}`,
      async () => {
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
      { ttlMs: RESTAURANT_DETAIL_TTL_MS }
    );
  },

  getOwnerRestaurants: async (ownerId) => {
    return getCachedResource(
      `restaurants:owner:${ownerId}`,
      async () => {
        const response = await apiClient.get(`/restaurants/owner/${ownerId}`);
        return response.data.map(normalizeRestaurant);
      },
      { ttlMs: OWNER_RESTAURANTS_TTL_MS }
    );
  },

  getManageRestaurant: async (restaurantId) => {
    return getCachedResource(
      `restaurants:manage:${restaurantId}`,
      async () => {
        const [restaurantResponse, menuResponse] = await Promise.all([
          apiClient.get(`/restaurants/manage/${restaurantId}`),
          apiClient.get(`/dishes/restaurant/${restaurantId}`),
        ]);

        return normalizeRestaurant({
          ...restaurantResponse.data,
          menu: menuResponse.data,
        });
      },
      { ttlMs: OWNER_MANAGE_TTL_MS }
    );
  },

  createRestaurant: async (payload) => {
    const response = await apiClient.post("/restaurants", mapRestaurantPayload(payload));
    const restaurant = normalizeRestaurant(response.data);
    invalidateRestaurantCaches(restaurant.id, restaurant.ownerId ?? payload.owner_id ?? payload.ownerId);
    return restaurant;
  },

  updateRestaurant: async (restaurantId, payload) => {
    const response = await apiClient.put(`/restaurants/${restaurantId}`, mapRestaurantPayload(payload));
    const restaurant = normalizeRestaurant(response.data);
    invalidateRestaurantCaches(restaurantId, restaurant.ownerId ?? payload.owner_id ?? payload.ownerId);
    return restaurant;
  },

  getRestaurantMenu: async (restaurantId) => {
    return getCachedResource(
      `restaurants:menu:${restaurantId}`,
      async () => {
        const response = await apiClient.get(`/dishes/restaurant/${restaurantId}`);
        return response.data.map(normalizeMenuItem);
      },
      { ttlMs: MENU_TTL_MS }
    );
  },

  createMenuItem: async (restaurantId, payload) => {
    const response = await apiClient.post(`/dishes/restaurant/${restaurantId}`, {
      name: payload.name?.trim(),
      description: payload.description?.trim() || null,
      price: Number(payload.price),
      category: payload.category?.trim() || null,
      image_url: payload.image_url?.trim() || null,
      is_available: Boolean(payload.is_available),
      availability_status: payload.is_available ? "AVAILABLE" : "UNAVAILABLE",
    });
    invalidateRestaurantCaches(restaurantId);
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
      availability_status: payload.is_available ? "AVAILABLE" : "UNAVAILABLE",
    });
    invalidateRestaurantCaches(payload.restaurantId ?? payload.restaurant_id);
    return normalizeMenuItem(response.data);
  },

  deleteMenuItem: async (itemId) => {
    await apiClient.delete(`/dishes/${itemId}`);
    invalidateRestaurantCaches();
  },

  getAdminRestaurants: async (status, options = {}) => {
    return getCachedResource(
      `admin:restaurants:${status || "all"}`,
      async () => {
        const response = await apiClient.get("/admin/restaurants", {
          params: status ? { status_filter: status } : undefined,
        });
        return response.data.map(normalizeRestaurant);
      },
      { ttlMs: ADMIN_TTL_MS, forceRefresh: options.forceRefresh }
    );
  },

  updateAdminRestaurantStatus: async (restaurantId, status) => {
    const response = await apiClient.put(`/admin/restaurants/${restaurantId}/status`, { approval_status: status });
    const restaurant = normalizeRestaurant(response.data);
    invalidateRestaurantCaches(restaurantId, restaurant.ownerId);
    return restaurant;
  },
};
