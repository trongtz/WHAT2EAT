import LoginRoundedIcon from "@mui/icons-material/LoginRounded";
import PersonOutlineRoundedIcon from "@mui/icons-material/PersonOutlineRounded";
import TipsAndUpdatesRoundedIcon from "@mui/icons-material/TipsAndUpdatesRounded";
import { Alert, Box, Chip, Link, Stack, Typography } from "@mui/material";
import { useState } from "react";
import { Link as RouterLink, useLocation, useNavigate } from "react-router-dom";
import CustomButton from "../components/CustomButton";
import CustomCard from "../components/CustomCard";
import FormInput from "../components/FormInput";
import AuthLayout from "../layouts/AuthLayout";
import { useAuth } from "../hooks/useAuth";
import { validateLogin } from "../utils/validators";

function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, loginAsGuest, loading } = useAuth();
  const [values, setValues] = useState({ email: "", password: "" });
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState("");
  const successMessage = location.state?.message || "";

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
      setMessage("");
      const response = await login(values);
      if (response.user.role === "owner") navigate("/chu-nha-hang/dashboard");
      else if (response.user.role === "admin") navigate("/admin/dashboard");
      else navigate("/");
    } catch (error) {
      setMessage(error.message);
    }
  };

  const handleGuestLogin = async () => {
    try {
      setMessage("");
      await loginAsGuest();
      navigate("/", { replace: true });
    } catch (error) {
      setMessage(error.message);
    }
  };

  return (
    <AuthLayout
      title="Đăng nhập để tiếp tục hành trình khám phá món ngon."
      subtitle="Lưu quán yêu thích, đặt bàn nhanh và nhận gợi ý phù hợp với khẩu vị của bạn trong một trải nghiệm gọn gàng, hiện đại."
    >
      <CustomCard
        sx={{
          width: "100%",
          borderRadius: 0,
          background: "transparent",
          boxShadow: "none",
          border: "none",
          backdropFilter: "none",
        }}
        contentSx={{ p: { xs: 2, md: 2.2 }, "&:last-child": { pb: { xs: 2, md: 2.2 } } }}
      >
        <Box component="form" onSubmit={handleSubmit}>
          <Stack spacing={1.35}>
            <Stack spacing={0.8}>
              <Chip
                icon={<TipsAndUpdatesRoundedIcon />}
                label="Đăng nhập / Đăng ký để đồng bộ trải nghiệm"
                sx={{
                  alignSelf: "flex-start",
                  height: 34,
                  bgcolor: "rgba(255,138,42,0.10)",
                  color: "primary.main",
                  borderRadius: 2,
                }}
              />
              <Typography variant="h3">Đăng nhập</Typography>
            </Stack>

            {successMessage ? <Alert severity="success">{successMessage}</Alert> : null}
            {message ? <Alert severity="error">{message}</Alert> : null}

            <FormInput label="Email" name="email" value={values.email} onChange={handleChange} error={!!errors.email} helperText={errors.email} />
            <FormInput type="password" label="Mật khẩu" name="password" value={values.password} onChange={handleChange} error={!!errors.password} helperText={errors.password} />
            <CustomButton type="submit" disabled={loading} startIcon={<LoginRoundedIcon />}>
              {loading ? "Đang đăng nhập..." : "Đăng nhập"}
            </CustomButton>
            <CustomButton
              type="button"
              disabled={loading}
              onClick={handleGuestLogin}
              startIcon={<PersonOutlineRoundedIcon />}
              sx={{
                background: "linear-gradient(135deg, #0F766E 0%, #14B8A6 100%)",
                boxShadow: "0 14px 28px rgba(20, 184, 166, 0.24)",
              }}
            >
              {loading ? "Đang vào với tư cách khách..." : "Vào với tư cách Khách"}
            </CustomButton>
            <Typography color="text.secondary" sx={{ fontSize: "0.94rem" }}>
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
