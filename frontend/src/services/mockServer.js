import {
  mockAiRecommendations,
  mockBookings,
  mockRestaurants,
  mockReviews,
  mockUsers,
} from "../data/mockData";

let users = [...mockUsers];
let restaurants = [...mockRestaurants];
let bookings = [...mockBookings];
let reviews = [...mockReviews];

const wait = (ms = 500) => new Promise((resolve) => setTimeout(resolve, ms));

const parsePayload = (data) => {
  if (!data) return {};
  if (typeof data === "string") return JSON.parse(data);
  return data;
};

const ok = (data, status = 200) =>
  Promise.resolve({ data, status, statusText: "OK", headers: {}, config: {} });

const fail = (message, status = 400) =>
  Promise.reject({
    response: { data: { message }, status },
    message,
  });

const getRestaurantById = (id) => restaurants.find((item) => item.id === Number(id));

const getOwnerRestaurant = (restaurantId, ownerId) =>
  restaurants.find(
    (item) => item.id === Number(restaurantId) && item.ownerId === Number(ownerId)
  );

const nextMenuId = () =>
  restaurants.reduce(
    (maxId, restaurant) =>
      Math.max(maxId, ...restaurant.menu.map((menuItem) => Number(menuItem.id || 0))),
    0
  ) + 1;

export const mockAdapter = async (config) => {
  await wait();

  const { method, url, params } = config;
  const payload = parsePayload(config.data);

  if (method === "post" && url === "/auth/login") {
    const user = users.find(
      (item) => item.email === payload.email && item.password === payload.password
    );
    if (!user) return fail("Email hoặc mật khẩu không đúng", 401);
    if (user.status && user.status !== "active") return fail("Tài khoản đang bị khóa", 403);
    return ok({ token: `token-${user.id}`, user: { ...user, password: undefined } });
  }

  if (method === "post" && url === "/auth/register") {
    const existedUser = users.some((item) => item.email === payload.email);
    if (existedUser) return fail("Email này đã tồn tại");
    const nextUser = {
      id: users.length + 1,
      role: "customer",
      status: "active",
      favoriteIds: [],
      ...payload,
    };
    users = [...users, nextUser];
    return ok({ token: `token-${nextUser.id}`, user: { ...nextUser, password: undefined } }, 201);
  }

  if (method === "post" && url === "/profile/update") {
    const user = users.find((item) => item.id === Number(payload.userId));
    if (!user) return fail("Không tìm thấy người dùng", 404);
    Object.assign(user, {
      fullName: payload.fullName,
      email: payload.email,
      phone: payload.phone,
    });
    return ok({ ...user, password: undefined });
  }

  if (method === "get" && url === "/restaurants") {
    const keyword = params?.keyword?.toLowerCase?.() || "";
    const category = params?.category || "";
    const price = Number(params?.price || 0);
    const filtered = restaurants.filter((item) => {
      const matchKeyword =
        !keyword ||
        item.name.toLowerCase().includes(keyword) ||
        item.category.toLowerCase().includes(keyword) ||
        item.address.toLowerCase().includes(keyword);
      const matchCategory = !category || item.category === category;
      const matchPrice = !price || item.averagePrice <= price;
      return matchKeyword && matchCategory && matchPrice;
    });
    return ok(filtered);
  }

  if (method === "get" && url?.startsWith("/restaurants/")) {
    const restaurant = getRestaurantById(url.split("/")[2]);
    if (!restaurant) return fail("Không tìm thấy nhà hàng", 404);
    const restaurantReviews = reviews.filter((item) => item.restaurantId === restaurant.id);
    return ok({ ...restaurant, reviewsList: restaurantReviews });
  }

  if (method === "get" && url === "/bookings") {
    return ok(bookings.filter((item) => item.userId === Number(params?.userId)));
  }

  if (method === "post" && url === "/bookings") {
    const newBooking = {
      id: bookings.length + 1,
      status: "Chờ duyệt",
      ...payload,
    };
    bookings = [newBooking, ...bookings];
    return ok(newBooking, 201);
  }

  if (method === "get" && url === "/favorites") {
    const user = users.find((item) => item.id === Number(params?.userId));
    const favoriteRestaurants = restaurants.filter((item) =>
      user?.favoriteIds?.includes(item.id)
    );
    return ok(favoriteRestaurants);
  }

  if (method === "post" && url === "/favorites/toggle") {
    const user = users.find((item) => item.id === Number(payload.userId));
    if (!user) return fail("Không tìm thấy người dùng", 404);
    const isFavorite = user.favoriteIds.includes(payload.restaurantId);
    user.favoriteIds = isFavorite
      ? user.favoriteIds.filter((id) => id !== payload.restaurantId)
      : [...user.favoriteIds, payload.restaurantId];
    return ok({ favoriteIds: user.favoriteIds });
  }

  if (method === "post" && url === "/reviews") {
    const newReview = {
      id: reviews.length + 1,
      createdAt: new Date().toISOString(),
      ownerReply: "",
      ...payload,
    };
    reviews = [newReview, ...reviews];
    return ok(newReview, 201);
  }

  if (method === "post" && url === "/ai/recommend") {
    const matchedPrompt = mockAiRecommendations.find((item) =>
      payload.prompt?.toLowerCase().includes(item.prompt.split(" ")[2]?.toLowerCase() || "")
    );
    const resultIds = matchedPrompt?.result || [1, 2, 3];
    return ok({
      summary:
        "AI đề xuất các lựa chọn cân bằng giữa khoảng cách, ngân sách và phong cách ăn uống của bạn.",
      restaurants: restaurants.filter((item) => resultIds.includes(item.id)),
    });
  }

  if (method === "get" && url === "/owner/restaurants") {
    return ok(restaurants.filter((item) => item.ownerId === Number(params?.ownerId)));
  }

  if (method === "post" && url === "/owner/restaurants/update") {
    const restaurant = getOwnerRestaurant(payload.restaurantId, payload.ownerId);
    if (!restaurant) return fail("Không tìm thấy nhà hàng", 404);
    Object.assign(restaurant, {
      name: payload.name,
      category: payload.category,
      address: payload.address,
      description: payload.description,
      priceRange: payload.priceRange,
      status: payload.status,
    });
    return ok(restaurant);
  }

  if (method === "post" && url === "/owner/menu/create") {
    const restaurant = getOwnerRestaurant(payload.restaurantId, payload.ownerId);
    if (!restaurant) return fail("Không tìm thấy nhà hàng", 404);
    const newItem = {
      id: nextMenuId(),
      name: payload.name,
      price: Number(payload.price),
    };
    restaurant.menu = [...restaurant.menu, newItem];
    return ok(newItem, 201);
  }

  if (method === "post" && url === "/owner/menu/update") {
    const restaurant = getOwnerRestaurant(payload.restaurantId, payload.ownerId);
    if (!restaurant) return fail("Không tìm thấy nhà hàng", 404);
    restaurant.menu = restaurant.menu.map((item) =>
      item.id === Number(payload.menuItemId)
        ? { ...item, name: payload.name, price: Number(payload.price) }
        : item
    );
    return ok(restaurant.menu);
  }

  if (method === "post" && url === "/owner/menu/delete") {
    const restaurant = getOwnerRestaurant(payload.restaurantId, payload.ownerId);
    if (!restaurant) return fail("Không tìm thấy nhà hàng", 404);
    restaurant.menu = restaurant.menu.filter(
      (item) => item.id !== Number(payload.menuItemId)
    );
    return ok(restaurant.menu);
  }

  if (method === "get" && url === "/owner/bookings") {
    const ownerRestaurantIds = restaurants
      .filter((item) => item.ownerId === Number(params?.ownerId))
      .map((item) => item.id);

    return ok(
      bookings
        .filter((item) => ownerRestaurantIds.includes(item.restaurantId))
        .map((booking) => {
          const customer = users.find((user) => user.id === booking.userId);
          return {
            ...booking,
            customerName: customer?.fullName || "Khách hàng",
          };
        })
    );
  }

  if (method === "post" && url === "/owner/bookings/update-status") {
    const booking = bookings.find((item) => item.id === Number(payload.bookingId));
    if (!booking) return fail("Không tìm thấy đơn đặt bàn", 404);
    booking.status = payload.status;
    return ok(booking);
  }

  if (method === "get" && url === "/owner/reviews") {
    const ownerRestaurantIds = restaurants
      .filter((item) => item.ownerId === Number(params?.ownerId))
      .map((item) => item.id);
    return ok(reviews.filter((item) => ownerRestaurantIds.includes(item.restaurantId)));
  }

  if (method === "post" && url === "/owner/reviews/reply") {
    const review = reviews.find((item) => item.id === Number(payload.reviewId));
    if (!review) return fail("Không tìm thấy đánh giá", 404);
    review.ownerReply = payload.reply;
    return ok(review);
  }

  if (method === "get" && url === "/admin/users") {
    return ok(users.map((item) => ({ ...item, password: undefined })));
  }

  if (method === "post" && url === "/admin/users/toggle-status") {
    const user = users.find((item) => item.id === Number(payload.userId));
    if (!user) return fail("Không tìm thấy người dùng", 404);
    user.status = user.status === "active" ? "blocked" : "active";
    return ok({ ...user, password: undefined });
  }

  if (method === "get" && url === "/admin/restaurants") {
    return ok(restaurants);
  }

  if (method === "get" && url === "/admin/restaurants/pending") {
    return ok(restaurants.filter((item) => !item.approved));
  }

  if (method === "get" && url === "/admin/overview") {
    return ok({
      totalUsers: users.length,
      totalOwners: users.filter((item) => item.role === "owner").length,
      totalCustomers: users.filter((item) => item.role === "customer").length,
      totalRestaurants: restaurants.length,
      pendingRestaurants: restaurants.filter((item) => !item.approved).length,
      activeRestaurants: restaurants.filter((item) => item.approved).length,
      totalBookings: bookings.length,
      averageRating:
        reviews.length > 0
          ? Number(
              (reviews.reduce((sum, item) => sum + Number(item.rating || 0), 0) / reviews.length).toFixed(1)
            )
          : 0,
    });
  }

  if (method === "post" && url === "/admin/restaurants/approve") {
    restaurants = restaurants.map((item) =>
      item.id === Number(payload.restaurantId) ? { ...item, approved: true } : item
    );
    return ok({ success: true });
  }

  if (method === "post" && url === "/admin/restaurants/reject") {
    restaurants = restaurants.map((item) =>
      item.id === Number(payload.restaurantId)
        ? { ...item, approved: false, featured: false }
        : item
    );
    return ok({ success: true });
  }

  if (method === "post" && url === "/admin/restaurants/toggle-featured") {
    restaurants = restaurants.map((item) =>
      item.id === Number(payload.restaurantId) ? { ...item, featured: !item.featured } : item
    );
    return ok({ success: true });
  }

  return fail("Endpoint mock chưa được hỗ trợ", 404);
};
