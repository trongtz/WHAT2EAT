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

const normalizeTimeRange = (value) => {
  if (!value) return "";
  const text = String(value).trim();
  if (!text || text.toLowerCase() === "closed") return "";
  if (!text.includes("-")) return text;

  const [start, end] = text.split("-", 2).map((item) => item.trim());
  if (!start || !end) return text;
  return `${start} - ${end}`;
};

export const getPrimaryOpenHoursValue = (openHours) => {
  if (!openHours) return "";
  if (typeof openHours === "string") return normalizeTimeRange(openHours);
  if (typeof openHours !== "object") return "";

  for (const key of ["regular", "main", "default", "primary"]) {
    const value = openHours[key];
    const normalized = typeof value === "object" && value?.open && value?.close
      ? normalizeTimeRange(`${value.open} - ${value.close}`)
      : normalizeTimeRange(value);
    if (normalized) return normalized;
  }

  const dayKeys = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"];
  const ranges = dayKeys
    .map((dayKey) => {
      const value = openHours[dayKey];
      return typeof value === "object" && value?.open && value?.close
        ? normalizeTimeRange(`${value.open} - ${value.close}`)
        : normalizeTimeRange(value);
    })
    .filter(Boolean);

  if (!ranges.length) return "";

  const countByRange = ranges.reduce((accumulator, range) => {
    accumulator[range] = (accumulator[range] || 0) + 1;
    return accumulator;
  }, {});
  return Object.entries(countByRange).sort((first, second) => second[1] - first[1])[0][0];
};

export const getPrimaryOpenHours = (openHours) => getPrimaryOpenHoursValue(openHours) || "Chưa khai báo";

export const formatOpenHours = getPrimaryOpenHours;

export const getTableAvailabilityLabel = (availableTables, maxTables) => {
  const available = Number(availableTables);
  const max = Number(maxTables);
  if (!Number.isFinite(max) || max <= 0) return "Chưa cập nhật";
  if (!Number.isFinite(available)) return `0/${max} bàn`;
  return `${Math.max(available, 0)}/${max} bàn`;
};
