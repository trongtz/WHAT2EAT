export const formatCurrency = (value) =>
  new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND", maximumFractionDigits: 0 }).format(value);

export const formatDate = (value) =>
  new Intl.DateTimeFormat("vi-VN", { day: "2-digit", month: "2-digit", year: "numeric" }).format(new Date(value));

export const getStatusColor = (status) => {
  const map = {
    "Còn chỗ": "success",
    "Sắp đầy": "warning",
    "Hết chỗ": "error",
    "Đã xác nhận": "success",
    "Chờ duyệt": "warning",
    "Đã hủy": "error",
  };
  return map[status] || "default";
};
