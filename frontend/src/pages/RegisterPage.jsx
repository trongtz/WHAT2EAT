import PersonAddAltRoundedIcon from "@mui/icons-material/PersonAddAltRounded";
import { Alert, Box, Link, MenuItem, Stack, Typography } from "@mui/material";
import { useState } from "react";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import CustomButton from "../components/CustomButton";
import CustomCard from "../components/CustomCard";
import FormInput from "../components/FormInput";
import { useAuth } from "../hooks/useAuth";
import AuthLayout from "../layouts/AuthLayout";
import { validateRegister } from "../utils/validators";

function RegisterPage() {
  const navigate = useNavigate();
  const { register, loading } = useAuth();
  const [values, setValues] = useState({
    fullName: "",
    email: "",
    phone: "",
    role: "customer",
    password: "",
    confirmPassword: "",
  });
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState("");

  const handleChange = (event) => {
    const { name, value } = event.target;
    setValues((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    const nextErrors = validateRegister(values);
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length) return;

    try {
      await register(values);
      navigate("/dang-nhap", {
        replace: true,
        state: {
          message: "Đăng ký thành công. Vui lòng đăng nhập để tiếp tục.",
        },
      });
    } catch (error) {
      setMessage(error.message);
    }
  };

  return (
    <AuthLayout
      title="Tạo tài khoản mới để bắt đầu khám phá WHAT2EAT."
      subtitle="Gia nhập ứng dụng để quản lý lịch sử đặt bàn, lưu quán yêu thích và nhận thêm nhiều gợi ý ăn uống hợp gu mỗi ngày."
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
            <Typography variant="h3">Đăng ký</Typography>
            {message ? <Alert severity="error">{message}</Alert> : null}
            <FormInput label="Họ và tên" name="fullName" value={values.fullName} onChange={handleChange} error={!!errors.fullName} helperText={errors.fullName} />
            <FormInput label="Email" name="email" value={values.email} onChange={handleChange} error={!!errors.email} helperText={errors.email} />
            <FormInput label="Số điện thoại" name="phone" value={values.phone} onChange={handleChange} error={!!errors.phone} helperText={errors.phone} />
            <FormInput select label="Vai trò" name="role" value={values.role} onChange={handleChange} error={!!errors.role} helperText={errors.role}>
              <MenuItem value="customer">Khách hàng</MenuItem>
              <MenuItem value="owner">Chủ nhà hàng</MenuItem>
            </FormInput>
            <FormInput type="password" label="Mật khẩu" name="password" value={values.password} onChange={handleChange} error={!!errors.password} helperText={errors.password} />
            <FormInput
              type="password"
              label="Xác nhận mật khẩu"
              name="confirmPassword"
              value={values.confirmPassword}
              onChange={handleChange}
              error={!!errors.confirmPassword}
              helperText={errors.confirmPassword}
            />
            <CustomButton type="submit" disabled={loading} startIcon={<PersonAddAltRoundedIcon />}>
              {loading ? "Đang tạo tài khoản..." : "Tạo tài khoản"}
            </CustomButton>
            <Typography color="text.secondary" sx={{ fontSize: "0.94rem" }}>
              Đã có tài khoản?{" "}
              <Link component={RouterLink} to="/dang-nhap" underline="hover">
                Đăng nhập
              </Link>
            </Typography>
          </Stack>
        </Box>
      </CustomCard>
    </AuthLayout>
  );
}

export default RegisterPage;
