export const mockUsers = [
  {
    id: 1,
    fullName: "Nguyễn Minh Anh",
    email: "user@smartfood.vn",
    phone: "0901234567",
    password: "123456",
    role: "customer",
    status: "active",
    favoriteIds: [1, 3],
  },
  {
    id: 2,
    fullName: "Trần Quang Huy",
    email: "owner@smartfood.vn",
    phone: "0908881234",
    password: "123456",
    role: "owner",
    status: "active",
    favoriteIds: [2],
  },
  {
    id: 3,
    fullName: "Lê Thu Hà",
    email: "admin@smartfood.vn",
    phone: "0907778888",
    password: "123456",
    role: "admin",
    status: "active",
    favoriteIds: [],
  }
];

export const mockRestaurants = [
  {
    id: 1,
    name: "Spicy Hotpot",
    category: "Lẩu",
    city: "Quận 1",
    address: "22 Lê Thánh Tôn, Quận 1, TP.HCM",
    distance: "900 m",
    rating: 4.8,
    reviews: 1280,
    priceRange: "150.000đ - 350.000đ",
    averagePrice: 220000,
    status: "Còn chỗ",
    image: "https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=900&q=80",
    description: "Không gian hiện đại, nước lẩu đậm vị và menu phong phú cho nhóm bạn.",
    tags: ["Gia đình", "Lẩu cay", "Đi nhóm"],
    featured: true,
    ownerId: 2,
    approved: true,
    menu: [
      { id: 1, name: "Lẩu tứ xuyên", price: 289000 },
      { id: 2, name: "Bò mỹ cuộn", price: 159000 },
      { id: 3, name: "Combo nấm", price: 99000 },
    ],
  },
  {
    id: 2,
    name: "Sushi VN",
    category: "Nhật Bản",
    city: "Phú Nhuận",
    address: "127 Đinh Tiên Hoàng, Phú Nhuận, TP.HCM",
    distance: "1.1 km",
    rating: 4.7,
    reviews: 1389,
    priceRange: "120.000đ - 420.000đ",
    averagePrice: 260000,
    status: "Sắp đầy",
    image: "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?auto=format&fit=crop&w=900&q=80",
    description: "Sushi tươi mỗi ngày, phù hợp hẹn hò và tiếp khách.",
    tags: ["Sushi", "Hẹn hò", "Set lunch"],
    featured: true,
    ownerId: 2,
    approved: true,
    menu: [
      { id: 4, name: "Sashimi tổng hợp", price: 319000 },
      { id: 5, name: "Salmon roll", price: 119000 },
      { id: 6, name: "Tempura tôm", price: 139000 },
    ],
  },
  {
    id: 3,
    name: "Vinbeer BBQ",
    category: "Nướng",
    city: "Quận 4",
    address: "99 Võ Văn Kiệt, Quận 4, TP.HCM",
    distance: "1.3 km",
    rating: 4.5,
    reviews: 911,
    priceRange: "180.000đ - 390.000đ",
    averagePrice: 250000,
    status: "Còn chỗ",
    image: "https://images.unsplash.com/photo-1529193591184-b1d58069ecdd?auto=format&fit=crop&w=900&q=80",
    description: "BBQ phong cách đường phố với view mở và không khí sôi động.",
    tags: ["BBQ", "Bạn bè", "Buổi tối"],
    featured: true,
    ownerId: 2,
    approved: true,
    menu: [
      { id: 7, name: "Set thịt nướng đặc biệt", price: 259000 },
      { id: 8, name: "Sườn cay", price: 149000 },
    ],
  },
  {
    id: 4,
    name: "Boba Milk Tea",
    category: "Đồ uống",
    city: "Bình Thạnh",
    address: "54 Trần Quang Khải, Bình Thạnh, TP.HCM",
    distance: "2.5 km",
    rating: 4.6,
    reviews: 1160,
    priceRange: "35.000đ - 75.000đ",
    averagePrice: 55000,
    status: "Còn chỗ",
    image: "https://images.unsplash.com/photo-1558857563-b371033873b8?auto=format&fit=crop&w=900&q=80",
    description: "Trà sữa signature, góc ngồi xinh và nhiều topping lạ.",
    tags: ["Trà sữa", "Check-in", "Nhẹ nhàng"],
    featured: false,
    ownerId: 2,
    approved: false,
    menu: [
      { id: 9, name: "Brown sugar milk tea", price: 49000 },
      { id: 10, name: "Oolong kem sữa", price: 45000 },
    ],
  }
];

export const mockBookings = [
  {
    id: 1,
    userId: 1,
    restaurantId: 1,
    date: "2026-04-20",
    time: "19:00",
    guests: 4,
    note: "Bàn gần cửa sổ",
    status: "Đã xác nhận",
  },
  {
    id: 2,
    userId: 1,
    restaurantId: 2,
    date: "2026-04-12",
    time: "18:30",
    guests: 2,
    note: "Kỷ niệm ngày quen nhau",
    status: "Chờ duyệt",
  }
];

export const mockReviews = [
  {
    id: 1,
    restaurantId: 1,
    userName: "Phạm Gia Hân",
    rating: 5,
    comment: "Nước lẩu ngon, phục vụ nhanh và rất dễ đặt bàn.",
    createdAt: "2026-04-10",
  },
  {
    id: 2,
    restaurantId: 2,
    userName: "Lý Thanh Vân",
    rating: 4,
    comment: "Không gian đẹp, món lên hơi chậm vào cuối tuần.",
    createdAt: "2026-04-09",
  }
];

export const mockAiRecommendations = [
  {
    id: 1,
    prompt: "Mình muốn ăn tối lãng mạn, ngân sách 500k cho 2 người ở trung tâm",
    result: [2, 1],
  },
  {
    id: 2,
    prompt: "Tìm quán đi nhóm đông, có đồ nướng vui vẻ cuối tuần",
    result: [3, 1],
  }
];
