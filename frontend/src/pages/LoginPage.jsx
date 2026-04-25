import LoginRoundedIcon from "@mui/icons-material/LoginRounded";
import { Alert, Box, Link, Stack, Typography } from "@mui/material";
import { useState } from "react";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import CustomButton from "../components/CustomButton";
import CustomCard from "../components/CustomCard";
import FormInput from "../components/FormInput";
import AuthLayout from "../layouts/AuthLayout";
import { useAuth } from "../hooks/useAuth";
import { validateLogin } from "../utils/validators";

function LoginPage() {
  const navigate = useNavigate();
  const { login, loading } = useAuth();
  const [values, setValues] = useState({ email: "user@smartfood.vn", password: "123456" });
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState("");

  const handleChange = (event) => {
    const { name, value } = event.target;
    setValues((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    const nextErrors = validateLogin(values);
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length) return;

    try {
      const response = await login(values);
      if (response.user.role === "owner") navigate("/chu-nha-hang/dashboard");
      else if (response.user.role === "admin") navigate("/admin/dashboard");
      else navigate("/");
    } catch (error) {
      setMessage(error.message);
    }
  };

  return (
    <AuthLayout
      title="Chào mừng quay lại"
      subtitle="Đăng nhập để đặt bàn nhanh, lưu nhà hàng yêu thích và nhận gợi ý AI theo đúng gu ăn uống của bạn."
    >
      <CustomCard>
        <Box component="form" onSubmit={handleSubmit}>
          <Stack spacing={2.5}>
            <Typography variant="h3">Đăng nhập</Typography>
            <Typography color="text.secondary">
              Tài khoản demo: `user@smartfood.vn`, `owner@smartfood.vn`, `admin@smartfood.vn` / mật khẩu `123456`
            </Typography>
            {message ? <Alert severity="error">{message}</Alert> : null}
            <FormInput label="Email" name="email" value={values.email} onChange={handleChange} error={!!errors.email} helperText={errors.email} />
            <FormInput
              type="password"
              label="Mật khẩu"
              name="password"
              value={values.password}
              onChange={handleChange}
              error={!!errors.password}
              helperText={errors.password}
            />
            <CustomButton type="submit" disabled={loading} startIcon={<LoginRoundedIcon />}>
              {loading ? "Đang đăng nhập..." : "Đăng nhập"}
            </CustomButton>
            <Typography color="text.secondary">
              Chưa có tài khoản?{" "}
              <Link component={RouterLink} to="/dang-ky" underline="hover">
                Đăng ký ngay
              </Link>
            </Typography>
          </Stack>
        </Box>
      </CustomCard>
    </AuthLayout>
  );
}

export default LoginPage;
