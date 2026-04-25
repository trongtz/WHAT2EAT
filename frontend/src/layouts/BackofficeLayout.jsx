import AnalyticsRoundedIcon from "@mui/icons-material/AnalyticsRounded";
import ApprovalRoundedIcon from "@mui/icons-material/ApprovalRounded";
import DashboardRoundedIcon from "@mui/icons-material/DashboardRounded";
import LogoutRoundedIcon from "@mui/icons-material/LogoutRounded";
import MenuBookRoundedIcon from "@mui/icons-material/MenuBookRounded";
import RateReviewRoundedIcon from "@mui/icons-material/RateReviewRounded";
import RestaurantRoundedIcon from "@mui/icons-material/RestaurantRounded";
import TableRestaurantRoundedIcon from "@mui/icons-material/TableRestaurantRounded";
import PeopleRoundedIcon from "@mui/icons-material/PeopleRounded";
import StorefrontRoundedIcon from "@mui/icons-material/StorefrontRounded";
import ArrowBackRoundedIcon from "@mui/icons-material/ArrowBackRounded";
import {
  Avatar,
  Box,
  Button,
  Chip,
  Container,
  Stack,
  Typography,
} from "@mui/material";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

const navByRole = {
  owner: [
    { label: "Tong quan", to: "/chu-nha-hang/dashboard", icon: <DashboardRoundedIcon /> },
    { label: "Nha hang", to: "/chu-nha-hang/nha-hang", icon: <StorefrontRoundedIcon /> },
    { label: "Menu", to: "/chu-nha-hang/menu", icon: <MenuBookRoundedIcon /> },
    { label: "Dat ban", to: "/chu-nha-hang/dat-ban", icon: <TableRestaurantRoundedIcon /> },
    { label: "Danh gia", to: "/chu-nha-hang/danh-gia", icon: <RateReviewRoundedIcon /> },
  ],
  admin: [
    { label: "Tong quan", to: "/admin/dashboard", icon: <DashboardRoundedIcon /> },
    { label: "Phan tich", to: "/admin/phan-tich", icon: <AnalyticsRoundedIcon /> },
    { label: "Nguoi dung", to: "/admin/nguoi-dung", icon: <PeopleRoundedIcon /> },
    { label: "Duyet nha hang", to: "/admin/nha-hang", icon: <ApprovalRoundedIcon /> },
  ],
};

const roleMeta = {
  owner: {
    title: "Trung tam van hanh nha hang",
    subtitle: "Quan ly ban, menu, danh gia va hieu suat theo thoi gian thuc.",
    accent: "linear-gradient(135deg, #FF9F1C 0%, #FFB347 100%)",
    chip: "Chu nha hang",
  },
  admin: {
    title: "Bang dieu khien quan tri",
    subtitle: "Kiem soat duyet nha hang, tai khoan va suc khoe he thong.",
    accent: "linear-gradient(135deg, #111827 0%, #334155 100%)",
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
        background:
          role === "admin"
            ? "linear-gradient(180deg, #F4F7FB 0%, #EEF3F9 100%)"
            : "linear-gradient(180deg, #FFF8F0 0%, #F7FAFF 100%)",
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
              bgcolor: "rgba(255,255,255,0.9)",
              border: "1px solid rgba(15,23,42,0.06)",
              boxShadow: "0 24px 50px rgba(15,23,42,0.08)",
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
                    boxShadow: "0 18px 36px rgba(15,23,42,0.16)",
                  }}
                >
                  {role === "admin" ? <RestaurantRoundedIcon /> : <StorefrontRoundedIcon />}
                </Box>
                <Box>
                  <Typography variant="h4" sx={{ fontSize: "1.2rem" }}>
                    SmartFood
                  </Typography>
                  <Typography color="text.secondary" sx={{ fontSize: "0.92rem" }}>
                    {meta.chip}
                  </Typography>
                </Box>
              </Stack>

              <Box
                sx={{
                  borderRadius: 2,
                  p: 2,
                  color: "white",
                  background: meta.accent,
                }}
              >
                <Chip
                  label={meta.chip}
                  size="small"
                  sx={{ mb: 1.5, bgcolor: "rgba(255,255,255,0.16)", color: "white" }}
                />
                <Typography variant="h4" sx={{ fontSize: "1.15rem", mb: 0.75 }}>
                  {meta.title}
                </Typography>
                <Typography sx={{ opacity: 0.9, fontSize: "0.92rem" }}>{meta.subtitle}</Typography>
              </Box>

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
                        boxShadow: "0 14px 28px rgba(15,23,42,0.14)",
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
                  bgcolor: "rgba(244,247,251,0.9)",
                  border: "1px solid rgba(15,23,42,0.06)",
                }}
              >
                <Stack direction="row" spacing={1.5} alignItems="center">
                  <Avatar sx={{ bgcolor: role === "admin" ? "#111827" : "#FF9F1C" }}>
                    {user?.fullName?.charAt(0)}
                  </Avatar>
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

              <Stack spacing={1.25}>
                <Button
                  component={NavLink}
                  to="/"
                  startIcon={<ArrowBackRoundedIcon />}
                  variant="outlined"
                  sx={{ justifyContent: "flex-start", borderRadius: 2 }}
                >
                  Ve giao dien khach hang
                </Button>
                <Button
                  onClick={handleLogout}
                  startIcon={<LogoutRoundedIcon />}
                  sx={{ justifyContent: "flex-start", borderRadius: 2 }}
                >
                  Dang xuat
                </Button>
              </Stack>
            </Stack>
          </Box>

          <Box>
            <Box
              sx={{
                borderRadius: 2,
                p: { xs: 2, md: 3 },
                bgcolor: "rgba(255,255,255,0.88)",
                border: "1px solid rgba(15,23,42,0.06)",
                boxShadow: "0 24px 50px rgba(15,23,42,0.08)",
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
