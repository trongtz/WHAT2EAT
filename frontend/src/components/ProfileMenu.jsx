import KeyboardArrowDownRoundedIcon from "@mui/icons-material/KeyboardArrowDownRounded";
import LogoutRoundedIcon from "@mui/icons-material/LogoutRounded";
import PersonOutlineRoundedIcon from "@mui/icons-material/PersonOutlineRounded";
import SettingsRoundedIcon from "@mui/icons-material/SettingsRounded";
import {
  Avatar,
  Box,
  ButtonBase,
  Chip,
  Fade,
  ListItemIcon,
  Menu,
  MenuItem,
  Stack,
  Typography,
} from "@mui/material";
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

const roleLabel = {
  customer: "Food Explorer",
  owner: "Restaurant Curator",
  admin: "Taste Director",
};

function ProfileMenu({ user, onLogout }) {
  const [anchorEl, setAnchorEl] = useState(null);
  const navigate = useNavigate();

  const initials = useMemo(() => {
    if (!user?.fullName) return "W";
    return user.fullName
      .split(" ")
      .slice(0, 2)
      .map((word) => word.charAt(0).toUpperCase())
      .join("");
  }, [user]);

  const open = Boolean(anchorEl);

  return (
    <>
      <ButtonBase
        onClick={(event) => setAnchorEl(event.currentTarget)}
        sx={{
          minHeight: 60,
          borderRadius: 4,
          px: 1.1,
          py: 0.5,
          gap: 1.25,
          maxWidth: "100%",
          display: "flex",
          alignItems: "center",
          backgroundColor: "rgba(255,255,255,0.78)",
          border: "1px solid rgba(255,255,255,0.72)",
          boxShadow: "0 16px 34px rgba(31, 41, 55, 0.10)",
          transition: "transform 0.2s ease, box-shadow 0.2s ease, background-color 0.2s ease",
          "&:hover": {
            transform: "translateY(-1px)",
            boxShadow: "0 18px 36px rgba(31, 41, 55, 0.14)",
            backgroundColor: "rgba(255,255,255,0.92)",
          },
        }}
      >
        <Avatar
          sx={{
            width: 42,
            height: 42,
            color: "white",
            fontWeight: 800,
            background: "linear-gradient(135deg, #FF7A18 0%, #FFB347 100%)",
            boxShadow: "inset 0 0 0 2px rgba(255,255,255,0.32)",
          }}
        >
          {initials}
        </Avatar>

        <Box sx={{ display: { xs: "none", md: "block" }, textAlign: "left", minWidth: 0 }}>
          <Typography
            sx={{
              fontWeight: 700,
              lineHeight: 1.1,
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
              maxWidth: { md: 150, lg: 180 },
            }}
          >
            {user?.fullName}
          </Typography>
          <Typography sx={{ mt: 0.25, fontSize: "0.82rem", color: "text.secondary", lineHeight: 1.1 }}>
            {roleLabel[user?.role] || "Food Explorer"}
          </Typography>
        </Box>

        <KeyboardArrowDownRoundedIcon sx={{ ml: 0.25, color: "text.secondary" }} />
      </ButtonBase>

      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={() => setAnchorEl(null)}
        TransitionComponent={Fade}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
        transformOrigin={{ vertical: "top", horizontal: "right" }}
        slotProps={{
          paper: {
            sx: {
              mt: 1.25,
              minWidth: 240,
              borderRadius: 3,
              p: 1,
              background: "rgba(255,255,255,0.92)",
              backdropFilter: "blur(18px)",
              border: "1px solid rgba(255,255,255,0.75)",
              boxShadow: "0 28px 60px rgba(31, 41, 55, 0.16)",
            },
          },
        }}
      >
        <Box sx={{ px: 1.25, py: 1 }}>
          <Typography sx={{ fontWeight: 800 }}>{user?.fullName}</Typography>
          <Stack direction="row" spacing={1} alignItems="center" sx={{ mt: 0.75 }}>
            <Chip
              size="small"
              label={roleLabel[user?.role] || "Food Explorer"}
              sx={{
                bgcolor: "rgba(34, 197, 94, 0.12)",
                color: "#169A52",
                fontWeight: 700,
              }}
            />
          </Stack>
        </Box>

        <MenuItem
          onClick={() => {
            setAnchorEl(null);
            navigate("/ho-so");
          }}
          sx={{ borderRadius: 2 }}
        >
          <ListItemIcon>
            <PersonOutlineRoundedIcon fontSize="small" />
          </ListItemIcon>
          Hồ sơ
        </MenuItem>
        <MenuItem
          onClick={() => {
            setAnchorEl(null);
            navigate("/ho-so");
          }}
          sx={{ borderRadius: 2 }}
        >
          <ListItemIcon>
            <SettingsRoundedIcon fontSize="small" />
          </ListItemIcon>
          Cài đặt
        </MenuItem>
        <MenuItem
          onClick={() => {
            setAnchorEl(null);
            onLogout();
          }}
          sx={{ borderRadius: 2, color: "#D44F5A" }}
        >
          <ListItemIcon>
            <LogoutRoundedIcon fontSize="small" sx={{ color: "#D44F5A" }} />
          </ListItemIcon>
          Đăng xuất
        </MenuItem>
      </Menu>
    </>
  );
}

export default ProfileMenu;
