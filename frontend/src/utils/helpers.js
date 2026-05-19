export const formatCurrency = (value) =>
  new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND", maximumFractionDigits: 0 }).format(
    Number(value || 0)
  );

export const formatPriceText = (value) => {
  const amount = Number(value);
  if (!Number.isFinite(amount)) return "";
  return `${new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 0 }).format(amount)} VND`;
};

export const formatPriceRangeDisplay = (value) => {
  if (!value) return "Chưa cập nhật";

  if (["cheap", "mid", "expensive"].includes(value)) {
    return getPriceRangeLabel(value);
  }

  const matches = String(value).match(/\d+(?:[.,]\d+)?/g);
  if (!matches?.length) return value;

  const formatted = matches
    .map((item) => Number(String(item).replace(/,/g, "")))
    .filter((item) => Number.isFinite(item))
    .map((item) => new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 0 }).format(item));

  if (!formatted.length) return value;
  if (formatted.length === 1) return `${formatted[0]} VND`;
  return `${formatted[0]} - ${formatted[1]} VND`;
};

export const formatDate = (value) =>
  value
    ? new Intl.DateTimeFormat("vi-VN", { day: "2-digit", month: "2-digit", year: "numeric" }).format(
        new Date(value)
      )
    : "--";

export const formatDateTime = (value) =>
  value
    ? new Intl.DateTimeFormat("vi-VN", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      }).format(new Date(value))
    : "--";

export const getStatusColor = (status) => {
  const map = {
    "Còn chỗ": "success",
    "Sắp đầy": "warning",
    "Hết chỗ": "error",
    "Đã xác nhận": "success",
    "Chờ duyệt": "warning",
    "Đã hủy": "error",
    "Cần xử lý": "warning",
    PENDING: "warning",
    CONFIRMED: "success",
    CANCELLED: "error",
    REJECTED: "error",
    APPROVED: "success",
    ACTIVE: "success",
    BANNED: "error",
  };
  return map[status] || "default";
};

export const getRestaurantStatusLabel = (status) => {
  const map = {
    PENDING: "Chờ duyệt",
    APPROVED: "Đã duyệt",
    REJECTED: "Từ chối",
  };
  return map[status] || status || "--";
};

export const getPriceRangeLabel = (priceRange) => {
  const map = {
    cheap: "Dưới 100k",
    mid: "100k - 300k",
    expensive: "Trên 300k",
  };
  return map[priceRange] || "Chưa cập nhật";
};

export const formatCoordinates = (latitude, longitude) => {
  if (latitude == null || longitude == null) return "Chưa cập nhật tọa độ";
  return `${latitude}, ${longitude}`;
};

export const formatOpenHours = (openHours) => {
  if (!openHours) return "Chưa khai báo";
  if (typeof openHours === "string") return openHours;
  if (typeof openHours !== "object") return "Chưa khai báo";

  const dayLabels = {
    mon: "Thứ 2",
    tue: "Thứ 3",
    wed: "Thứ 4",
    thu: "Thứ 5",
    fri: "Thứ 6",
    sat: "Thứ 7",
    sun: "Chủ nhật",
  };

  return Object.entries(openHours)
    .map(([day, value]) => {
      if (!value?.open || !value?.close) return null;
      return `${dayLabels[day] || day}: ${value.open} - ${value.close}`;
    })
    .filter(Boolean)
    .join(" | ");
};
