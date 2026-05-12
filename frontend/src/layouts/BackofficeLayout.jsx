import ApprovalRoundedIcon from "@mui/icons-material/ApprovalRounded";
import DashboardRoundedIcon from "@mui/icons-material/DashboardRounded";
import LogoutRoundedIcon from "@mui/icons-material/LogoutRounded";
import RateReviewRoundedIcon from "@mui/icons-material/RateReviewRounded";
import RestaurantRoundedIcon from "@mui/icons-material/RestaurantRounded";
import StorefrontRoundedIcon from "@mui/icons-material/StorefrontRounded";
import TableRestaurantRoundedIcon from "@mui/icons-material/TableRestaurantRounded";
import { Avatar, Box, Button, Container, Stack, Typography } from "@mui/material";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

const navByRole = {
  owner: [
    { label: "Tổng quan", to: "/chu-nha-hang/dashboard", icon: <DashboardRoundedIcon /> },
    { label: "Nhà hàng", to: "/chu-nha-hang/nha-hang", icon: <StorefrontRoundedIcon /> },
    { label: "Đặt bàn", to: "/chu-nha-hang/dat-ban", icon: <TableRestaurantRoundedIcon /> },
    { label: "Đánh giá", to: "/chu-nha-hang/danh-gia", icon: <RateReviewRoundedIcon /> },
  ],
  admin: [
    { label: "Tổng quan", to: "/admin/dashboard", icon: <DashboardRoundedIcon /> },
    { label: "Duyệt nhà hàng", to: "/admin/nha-hang", icon: <ApprovalRoundedIcon /> },
  ],
};

const roleMeta = {
  owner: {
    accent: "var(--app-primary-gradient)",
    avatarColor: "var(--app-primary)",
    chip: "Chủ nhà hàng",
  },
  admin: {
    accent: "var(--app-secondary-gradient)",
    avatarColor: "var(--app-secondary-dark)",
    chip: "Admin",
  },
};

function BackofficeLayout({ role, children }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const navItems = navByRole[role] || [];
  const meta = roleMeta[role];

  const handleLogout = () => {
    logout();
    navigate("/dang-nhap");
  };

  return (
    <Box
      sx={{
        minHeight: "100vh",
        background: "var(--app-shell-gradient)",
      }}
    >
      <Container maxWidth="xl" sx={{ py: 3 }}>
        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: { xs: "1fr", lg: "300px minmax(0, 1fr)" },
            gap: 3,
            alignItems: "start",
          }}
        >
          <Box
            sx={{
              position: { lg: "sticky" },
              top: { lg: 24 },
              borderRadius: 2,
              p: 2.5,
              bgcolor: "var(--app-surface-soft)",
              border: "1px solid color-mix(in srgb, var(--app-text-primary) 6%, transparent)",
              boxShadow: "0 24px 50px var(--app-glass-shadow)",
            }}
          >
            <Stack spacing={2.5}>
              <Stack direction="row" spacing={1.5} alignItems="center">
                <Box
                  sx={{
                    width: 56,
                    height: 56,
                    borderRadius: 2,
                    display: "grid",
                    placeItems: "center",
                    color: "white",
                    background: meta.accent,
                    boxShadow: "0 18px 36px color-mix(in srgb, var(--app-text-primary) 16%, transparent)",
                  }}
                >
                  {role === "admin" ? <RestaurantRoundedIcon /> : <StorefrontRoundedIcon />}
                </Box>
                <Box>
                  <Typography variant="h4" sx={{ fontSize: "1.2rem" }}>
                    WHAT2EAT
                  </Typography>
                  <Typography color="text.secondary" sx={{ fontSize: "0.92rem" }}>
                    {meta.chip}
                  </Typography>
                </Box>
              </Stack>

              <Stack spacing={1}>
                {navItems.map((item) => (
                  <Button
                    key={item.to}
                    component={NavLink}
                    to={item.to}
                    startIcon={item.icon}
                    sx={{
                      justifyContent: "flex-start",
                      px: 2,
                      py: 1.35,
                      color: "text.primary",
                      borderRadius: 2,
                      "&.active": {
                        color: "white",
                        background: meta.accent,
                        boxShadow: "0 14px 28px color-mix(in srgb, var(--app-text-primary) 14%, transparent)",
                      },
                    }}
                  >
                    {item.label}
                  </Button>
                ))}
              </Stack>

              <Box
                sx={{
                  borderRadius: 2,
                  p: 1.75,
                  bgcolor: "var(--app-surface-muted)",
                  border: "1px solid color-mix(in srgb, var(--app-text-primary) 6%, transparent)",
                }}
              >
                <Stack direction="row" spacing={1.5} alignItems="center">
                  <Avatar sx={{ bgcolor: meta.avatarColor }}>{user?.fullName?.charAt(0)}</Avatar>
                  <Box minWidth={0}>
                    <Typography fontWeight={700} noWrap>
                      {user?.fullName}
                    </Typography>
                    <Typography color="text.secondary" sx={{ fontSize: "0.9rem" }} noWrap>
                      {user?.email}
                    </Typography>
                  </Box>
                </Stack>
              </Box>

              <Button
                onClick={handleLogout}
                startIcon={<LogoutRoundedIcon />}
                sx={{ justifyContent: "flex-start", borderRadius: 2 }}
              >
                Đăng xuất
              </Button>
            </Stack>
          </Box>

          <Box>
            <Box
              sx={{
                borderRadius: 2,
                p: { xs: 2, md: 3 },
                bgcolor: "var(--app-surface-strong)",
                border: "1px solid color-mix(in srgb, var(--app-text-primary) 6%, transparent)",
                boxShadow: "0 24px 50px var(--app-glass-shadow)",
              }}
            >
              {children}
            </Box>
          </Box>
        </Box>
      </Container>
    </Box>
  );
}

export default BackofficeLayout;
