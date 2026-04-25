import EditRoundedIcon from "@mui/icons-material/EditRounded";
import ShieldRoundedIcon from "@mui/icons-material/ShieldRounded";
import StorefrontRoundedIcon from "@mui/icons-material/StorefrontRounded";
import {
  Alert,
  Chip,
  Grid,
  Link,
  Stack,
  Typography,
} from "@mui/material";
import { useMemo, useState } from "react";
import { Link as RouterLink } from "react-router-dom";
import CustomButton from "../components/CustomButton";
import CustomCard from "../components/CustomCard";
import CustomModal from "../components/CustomModal";
import FormInput from "../components/FormInput";
import SectionHeader from "../components/SectionHeader";
import { useAuth } from "../hooks/useAuth";
import { authService } from "../services/authService";

function ProfilePage() {
  const { user, updateUser } = useAuth();
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    fullName: user?.fullName || "",
    email: user?.email || "",
    phone: user?.phone || "",
  });

  const accountStatus = useMemo(
    () => (user?.status === "active" ? "Tài khoản đang hoạt động" : "Tài khoản đang bị khóa"),
    [user?.status]
  );

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSaving(true);
    try {
      const updatedUser = await authService.updateProfile({ userId: user.id, ...form });
      updateUser(updatedUser);
      setMessage("Cập nhật hồ sơ thành công.");
      setOpen(false);
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <SectionHeader
        title="Hồ sơ cá nhân"
        description="Cập nhật thông tin cơ bản và chuyển nhanh sang khu làm việc theo vai trò."
      />
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 8 }}>
          <CustomCard>
            <Stack spacing={2}>
              {message ? <Alert severity="success">{message}</Alert> : null}
              <Typography variant="h4">{user?.fullName}</Typography>
              <Typography color="text.secondary">Email: {user?.email}</Typography>
              <Typography color="text.secondary">Số điện thoại: {user?.phone}</Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                <Chip label={`Vai trò: ${user?.role}`} color="primary" />
                <Chip
                  label={accountStatus}
                  color={user?.status === "active" ? "success" : "error"}
                />
              </Stack>
              <Alert severity="info">
                Bạn có thể chỉnh trực tiếp họ tên, email và số điện thoại ngay trong hồ sơ này.
              </Alert>
              <CustomButton
                startIcon={<EditRoundedIcon />}
                sx={{ alignSelf: "flex-start" }}
                onClick={() => setOpen(true)}
              >
                Chỉnh sửa hồ sơ
              </CustomButton>
            </Stack>
          </CustomCard>
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <CustomCard>
            <Stack spacing={2}>
              <Typography variant="h4">Điều hướng nhanh</Typography>
              <Link component={RouterLink} to="/" underline="hover">
                Quay lại trang khách hàng
              </Link>
              {user?.role === "owner" ? (
                <CustomButton
                  component={RouterLink}
                  to="/chu-nha-hang/dashboard"
                  startIcon={<StorefrontRoundedIcon />}
                >
                  Đi tới khu chủ nhà hàng
                </CustomButton>
              ) : null}
              {user?.role === "admin" ? (
                <CustomButton
                  component={RouterLink}
                  to="/admin/dashboard"
                  startIcon={<ShieldRoundedIcon />}
                >
                  Đi tới khu quản trị
                </CustomButton>
              ) : null}
            </Stack>
          </CustomCard>
        </Grid>
      </Grid>

      <CustomModal open={open} onClose={() => setOpen(false)} title="Cập nhật hồ sơ">
        <Stack component="form" spacing={2} onSubmit={handleSubmit}>
          <FormInput label="Họ và tên" name="fullName" value={form.fullName} onChange={handleChange} />
          <FormInput label="Email" name="email" value={form.email} onChange={handleChange} />
          <FormInput label="Số điện thoại" name="phone" value={form.phone} onChange={handleChange} />
          <Stack direction="row" spacing={1.5}>
            <CustomButton type="submit" disabled={saving}>
              {saving ? "Đang lưu..." : "Lưu thay đổi"}
            </CustomButton>
            <CustomButton
              type="button"
              onClick={() => setOpen(false)}
              sx={{ background: "linear-gradient(135deg, #64748B 0%, #94A3B8 100%)" }}
            >
              Đóng
            </CustomButton>
          </Stack>
        </Stack>
      </CustomModal>
    </>
  );
}

export default ProfilePage;
