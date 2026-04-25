import { Alert, Chip, Grid, Stack, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import CustomButton from "../../components/CustomButton";
import CustomCard from "../../components/CustomCard";
import LoadingScreen from "../../components/LoadingScreen";
import SectionHeader from "../../components/SectionHeader";
import { dashboardService } from "../../services/dashboardService";

function AdminUsersPage() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");

  const loadData = async () => {
    const data = await dashboardService.getAdminUsers();
    setUsers(data);
    setLoading(false);
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleToggleStatus = async (userId) => {
    await dashboardService.toggleUserStatus(userId);
    setMessage("Đã cập nhật trạng thái tài khoản.");
    await loadData();
  };

  if (loading) return <LoadingScreen message="Đang tải danh sách người dùng..." />;

  return (
    <Stack spacing={3}>
      <SectionHeader
        title="Quản lý người dùng"
        description="Khóa hoặc mở lại tài khoản và kiểm tra thông tin của từng vai trò trong hệ thống."
      />

      {message ? <Alert severity="success">{message}</Alert> : null}

      <Grid container spacing={3}>
        {users.map((user) => (
          <Grid key={user.id} size={{ xs: 12, xl: 6 }}>
            <CustomCard>
              <Stack spacing={1.5}>
                <Stack direction="row" justifyContent="space-between" alignItems="center">
                  <Typography variant="h4">{user.fullName}</Typography>
                  <Chip
                    label={user.role}
                    color={
                      user.role === "admin" ? "error" : user.role === "owner" ? "warning" : "primary"
                    }
                  />
                </Stack>
                <Typography color="text.secondary">Email: {user.email}</Typography>
                <Typography color="text.secondary">Số điện thoại: {user.phone}</Typography>
                <Typography color="text.secondary">
                  Trạng thái: {user.status === "active" ? "Đang hoạt động" : "Tạm khóa"}
                </Typography>
                <CustomButton
                  onClick={() => handleToggleStatus(user.id)}
                  sx={{
                    alignSelf: "flex-start",
                    background:
                      user.status === "active"
                        ? "linear-gradient(135deg, #E85D75 0%, #FB7185 100%)"
                        : "linear-gradient(135deg, #10B981 0%, #34D399 100%)",
                  }}
                >
                  {user.status === "active" ? "Khóa tài khoản" : "Mở khóa tài khoản"}
                </CustomButton>
              </Stack>
            </CustomCard>
          </Grid>
        ))}
      </Grid>
    </Stack>
  );
}

export default AdminUsersPage;
