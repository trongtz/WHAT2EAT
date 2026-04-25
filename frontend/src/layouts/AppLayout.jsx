import RestaurantMenuRoundedIcon from "@mui/icons-material/RestaurantMenuRounded";
import { AppBar, Avatar, Box, Button, Container, Stack, Toolbar, Typography } from "@mui/material";
import { Link as RouterLink, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

const navItems = [
  { label: "Trang chủ", to: "/" },
  { label: "Tìm kiếm", to: "/tim-kiem" },
  { label: "Yêu thích", to: "/yeu-thich" },
  { label: "Lịch sử", to: "/lich-su-dat-ban" },
  { label: "AI Gợi ý", to: "/ai-goi-y" },
];

function AppLayout({ children }) {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/dang-nhap");
  };

  return (
    <Box sx={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <AppBar
        position="sticky"
        color="transparent"
        elevation={0}
        sx={{ backdropFilter: "blur(14px)", backgroundColor: "rgba(255,255,255,0.78)", borderBottom: "1px solid rgba(47,107,255,0.08)" }}
      >
        <Toolbar sx={{ py: 1.5 }}>
          <Container maxWidth="xl" sx={{ display: "flex", alignItems: "center", gap: 2 }}>
            <Stack direction="row" spacing={1.5} alignItems="center" component={RouterLink} to="/" sx={{ mr: 2 }}>
              <Box
                sx={{
                  width: 52,
                  height: 52,
                  borderRadius: "8px",
                  background: "linear-gradient(135deg, #FFB347 0%, #FF8C42 100%)",
                  display: "grid",
                  placeItems: "center",
                  boxShadow: "0 18px 34px rgba(255, 159, 28, 0.28)",
                }}
              >
                <RestaurantMenuRoundedIcon sx={{ color: "white" }} />
              </Box>
              <Typography variant="h4" lineHeight={1}>
                SmartFood
              </Typography>
            </Stack>

            <Stack direction="row" spacing={1} sx={{ display: { xs: "none", md: "flex" }, flex: 1 }}>
              {navItems.map((item) => (
                <Button
                  key={item.to}
                  component={NavLink}
                  to={item.to}
                  sx={{
                    px: 2.2,
                    color: "text.primary",
                    "&.active": {
                      color: "white",
                      background: "linear-gradient(135deg, #2F6BFF 0%, #5B8CFF 100%)",
                      boxShadow: "0 14px 30px rgba(47,107,255,0.25)",
                    },
                  }}
                >
                  {item.label}
                </Button>
              ))}
            </Stack>

            <Stack direction="row" spacing={1.5} alignItems="center">
              {isAuthenticated && user ? (
                <>
                  <Button component={RouterLink} to="/ho-so">
                    Hồ sơ
                  </Button>
                  <Avatar sx={{ bgcolor: "primary.main" }}>{user.fullName?.charAt(0)}</Avatar>
                  <Button variant="outlined" onClick={handleLogout}>
                    Đăng xuất
                  </Button>
                </>
              ) : (
                <Button
                  component={RouterLink}
                  to="/dang-nhap"
                  variant="contained"
                  sx={{
                    background: "linear-gradient(135deg, #2F6BFF 0%, #5B8CFF 100%)",
                  }}
                >
                  Đăng nhập / Đăng ký
                </Button>
              )}
            </Stack>
          </Container>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ flex: 1, py: { xs: 3, md: 5 } }}>
        {children}
      </Container>

      <Box sx={{ py: 4, borderTop: "1px solid rgba(47,107,255,0.08)", background: "rgba(255,255,255,0.55)" }}>
        <Container maxWidth="xl">
          <Typography variant="body2" color="text.secondary">
            SmartFood © 2026 • Khám phá nhà hàng, đặt bàn nhanh, gợi ý bằng AI.
          </Typography>
        </Container>
      </Box>
    </Box>
  );
}

export default AppLayout;
