export const isEmail = (value) => /\S+@\S+\.\S+/.test(value);

export const validateLogin = (values) => {
  const errors = {};

  if (!values.email) errors.email = "Vui lòng nhập email";
  else if (!isEmail(values.email)) errors.email = "Email không hợp lệ";

  if (!values.password) errors.password = "Vui lòng nhập mật khẩu";
  else if (values.password.length < 6) errors.password = "Mật khẩu tối thiểu 6 ký tự";

  return errors;
};

export const validateRegister = (values) => {
  const errors = validateLogin(values);

  if (!values.fullName) errors.fullName = "Vui lòng nhập họ tên";
  if (!values.role) errors.role = "Vui lòng chọn vai trò";
  else if (!["customer", "owner"].includes(values.role)) errors.role = "Vai trò không hợp lệ";

  if (!values.confirmPassword) errors.confirmPassword = "Vui lòng xác nhận mật khẩu";
  if (values.password && values.confirmPassword && values.password !== values.confirmPassword) {
    errors.confirmPassword = "Mật khẩu xác nhận không khớp";
  }

  return errors;
};

export const validateBooking = (values) => {
  const errors = {};

  if (!values.restaurantId) errors.restaurantId = "Vui lòng chọn nhà hàng";
  if (!values.date) errors.date = "Vui lòng chọn ngày";
  if (!values.time) errors.time = "Vui lòng chọn giờ";
  if (!values.guests) errors.guests = "Vui lòng nhập số khách";
  if (Number(values.guests) <= 0) errors.guests = "Số khách phải lớn hơn 0";
  if (values.date && values.time) {
    const reservationTime = new Date(`${values.date}T${values.time}`);
    const minimumTime = new Date(Date.now() + 30 * 60 * 1000);
    if (Number.isNaN(reservationTime.getTime()) || reservationTime <= minimumTime) {
      errors.time = "Vui lòng chọn thời gian sau hiện tại ít nhất 30 phút";
    }
  }

  return errors;
};

export const validatePrompt = (value) => {
  if (!value?.trim()) return "Vui lòng nhập mô tả nhu cầu của bạn";
  if (value.trim().length < 12) return "Mô tả chi tiết hơn để AI gợi ý tốt hơn";
  return "";
};
