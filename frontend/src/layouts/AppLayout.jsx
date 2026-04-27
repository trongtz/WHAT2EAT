import AutoAwesomeRoundedIcon from "@mui/icons-material/AutoAwesomeRounded";
import FavoriteBorderRoundedIcon from "@mui/icons-material/FavoriteBorderRounded";
import HistoryRoundedIcon from "@mui/icons-material/HistoryRounded";
import HomeRoundedIcon from "@mui/icons-material/HomeRounded";
import SearchRoundedIcon from "@mui/icons-material/SearchRounded";
import { Box, Button, Container, Stack, Toolbar, Typography } from "@mui/material";
import { Link as RouterLink, NavLink, useNavigate } from "react-router-dom";
import BrandLogo from "../components/BrandLogo";
import ProfileMenu from "../components/ProfileMenu";
import { useAuth } from "../hooks/useAuth";

const navItems = [
  { label: "Trang chủ", to: "/", icon: HomeRoundedIcon },
  { label: "Tìm kiếm", to: "/tim-kiem", icon: SearchRoundedIcon },
  { label: "Yêu thích", to: "/yeu-thich", icon: FavoriteBorderRoundedIcon },
  { label: "Lịch sử", to: "/lich-su-dat-ban", icon: HistoryRoundedIcon },
  { label: "AI Gợi ý", to: "/ai-goi-y", icon: AutoAwesomeRoundedIcon },
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
      <Box
        sx={{
          position: "sticky",
          top: 0,
          zIndex: 1200,
          px: { xs: 1.5, md: 2.5 },
          pt: { xs: 1.5, md: 2 },
          pb: 1.25,
          background:
            "linear-gradient(180deg, rgba(247,248,250,0.96) 0%, rgba(247,248,250,0.88) 78%, rgba(247,248,250,0) 100%)",
          backdropFilter: "blur(16px)",
        }}
      >
        <Container maxWidth="xl" disableGutters>
          <Toolbar
            sx={{
              minHeight: 76,
              px: { xs: 1.25, md: 1.5 },
              borderRadius: 4,
              backdropFilter: "blur(20px)",
              background: "rgba(255,255,255,0.72)",
              border: "1px solid rgba(255,255,255,0.72)",
              boxShadow: "0 24px 50px rgba(15, 23, 42, 0.10)",
              gap: 1.5,
            }}
          >
            <Box
              component={RouterLink}
              to="/"
              sx={{
                display: "flex",
                alignItems: "center",
                flexShrink: 0,
                pr: { md: 1 },
                maxWidth: { md: 320, lg: 360 },
              }}
            >
              <BrandLogo />
            </Box>

            <Stack
              direction="row"
              spacing={0.5}
              sx={{
                display: { xs: "none", md: "flex" },
                flex: 1,
                minWidth: 0,
                alignItems: "center",
                minHeight: 60,
                px: 0.5,
                py: 0.5,
                borderRadius: 4,
                bgcolor: "rgba(248,250,252,0.9)",
                border: "1px solid rgba(15,23,42,0.05)",
              }}
            >
              {navItems.map((item) => {
                const Icon = item.icon;

                return (
                  <Button
                    key={item.to}
                    component={NavLink}
                    to={item.to}
                    startIcon={<Icon />}
                    sx={{
                      minHeight: 50,
                      px: 2.1,
                      borderRadius: 3,
                      color: "text.secondary",
                      whiteSpace: "nowrap",
                      "& .MuiButton-startIcon": {
                        mr: 0.75,
                      },
                      "&.active": {
                        color: "white",
                        background: "linear-gradient(135deg, #FF7A18 0%, #FFB347 100%)",
                        boxShadow: "0 16px 34px rgba(255, 140, 64, 0.26)",
                      },
                    }}
                  >
                    {item.label}
                  </Button>
                );
              })}
            </Stack>

            <Stack
              direction="row"
              spacing={1}
              alignItems="center"
              sx={{
                ml: "auto",
                flexShrink: 1,
                justifyContent: "flex-end",
                minWidth: 0,
                maxWidth: { md: 300, lg: 340 },
              }}
            >
              {isAuthenticated && user ? (
                <ProfileMenu user={user} onLogout={handleLogout} />
              ) : (
                <Button
                  component={RouterLink}
                  to="/dang-nhap"
                  variant="contained"
                  sx={{
                    px: 2.6,
                    background: "linear-gradient(135deg, #FF7A18 0%, #FFB347 100%)",
                    boxShadow: "0 16px 34px rgba(255, 140, 64, 0.25)",
                  }}
                >
                  Đăng nhập / Đăng ký
                </Button>
              )}
            </Stack>
          </Toolbar>
        </Container>
      </Box>

      <Container maxWidth="xl" sx={{ flex: 1, pt: { xs: 2, md: 2.5 }, pb: { xs: 4, md: 6 } }}>
        {children}
      </Container>

      <Box sx={{ pt: 2, pb: 4 }}>
        <Container maxWidth="xl">
          <Box
            className="glass-panel"
            sx={{
              px: { xs: 2.5, md: 3.5 },
              py: 2.25,
              borderRadius: 2.5,
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              flexWrap: "wrap",
              gap: 1.5,
            }}
          >
            <Typography variant="body2" color="text.secondary">
              WHAT2EAT © 2026 • Khám phá món ngon gần bạn với bản đồ, AI và trải nghiệm đặt bàn tinh gọn.
            </Typography>
            <Typography variant="body2" sx={{ color: "#169A52", fontWeight: 700 }}>
              Curated for modern food discovery
            </Typography>
          </Box>
        </Container>
      </Box>
    </Box>
  );
}

export default AppLayout;
