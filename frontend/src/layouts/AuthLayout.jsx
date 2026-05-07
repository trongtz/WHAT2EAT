import AutoAwesomeRoundedIcon from "@mui/icons-material/AutoAwesomeRounded";
import LocationOnRoundedIcon from "@mui/icons-material/LocationOnRounded";
import RestaurantRoundedIcon from "@mui/icons-material/RestaurantRounded";
import StarRoundedIcon from "@mui/icons-material/StarRounded";
import { Box, Chip, Container, Grid, Stack, Typography } from "@mui/material";

const authHighlights = [
  { label: "Gợi ý hợp gu", value: "AI picks", icon: AutoAwesomeRoundedIcon, color: "var(--app-primary)" },
  { label: "Quán gần bạn", value: "Live map", icon: LocationOnRoundedIcon, color: "var(--app-secondary)" },
  { label: "Đánh giá tốt", value: "4.8+", icon: StarRoundedIcon, color: "var(--app-success)" },
];

function AuthLayout({ title, subtitle, children }) {
  return (
    <Box
      sx={{
        minHeight: "100svh",
        display: "flex",
        alignItems: "center",
        py: { xs: 2, md: 1.5 },
        background:
          "radial-gradient(circle at top left, var(--app-surface-glow-a), transparent 24%), radial-gradient(circle at top right, var(--app-surface-glow-b), transparent 22%), var(--app-background)",
      }}
    >
      <Container maxWidth="xl">
        <Box
          className="glass-panel"
          sx={{
            maxWidth: 1240,
            mx: "auto",
            width: "100%",
            p: { xs: 1.5, md: 2 },
            borderRadius: 4,
            background: "var(--app-surface-soft)",
            boxShadow: "0 28px 64px var(--app-glass-shadow)",
          }}
        >
          <Grid container spacing={{ xs: 2, md: 2 }} alignItems="stretch">
            <Grid size={{ xs: 12, md: 5.2 }}>
              <Box
                sx={{
                  height: "100%",
                  minHeight: { xs: 250, md: 520 },
                  borderRadius: 3.5,
                  overflow: "hidden",
                  position: "relative",
                  display: "flex",
                  alignItems: "flex-end",
                  p: { xs: 1.8, md: 2 },
                  backgroundImage:
                    "linear-gradient(180deg, rgba(15,23,42,0.10) 0%, rgba(15,23,42,0.68) 100%), url(https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1400&q=80)",
                  backgroundSize: "cover",
                  backgroundPosition: "center",
                }}
              >
                <Box
                  sx={{
                    position: "absolute",
                    top: 14,
                    left: 14,
                    px: 1.2,
                    py: 0.7,
                    borderRadius: 2,
                    bgcolor: "rgba(27,27,31,0.54)",
                    border: "1px solid rgba(255,255,255,0.18)",
                    backdropFilter: "blur(10px)",
                  }}
                >
                  <Stack direction="row" spacing={1} alignItems="center">
                    <RestaurantRoundedIcon sx={{ color: "white", fontSize: 20 }} />
                    <Typography
                      sx={{ color: "white", fontWeight: 800, letterSpacing: "0.05em", fontSize: "0.92rem" }}
                    >
                      WHAT2EAT
                    </Typography>
                  </Stack>
                </Box>

                <Stack spacing={1.05} sx={{ position: "relative", zIndex: 1, maxWidth: 390 }}>
                  <Chip
                    label="Ẩm thực gần bạn, đẹp và nhanh hơn"
                    sx={{
                      alignSelf: "flex-start",
                      height: 32,
                      bgcolor: "rgba(255,255,255,0.16)",
                      color: "white",
                      borderRadius: 2,
                      border: "1px solid rgba(255,255,255,0.24)",
                    }}
                  />
                  <Typography
                    variant="h1"
                    sx={{
                      color: "white",
                      maxWidth: 360,
                      fontSize: "clamp(1.65rem, 2.6vw, 2.9rem)",
                      lineHeight: 1.05,
                    }}
                  >
                    {title}
                  </Typography>
                  <Typography sx={{ color: "rgba(255,255,255,0.86)", fontSize: "0.9rem", maxWidth: 380 }}>
                    {subtitle}
                  </Typography>

                  <Grid container spacing={0.9} sx={{ pt: 0.2, display: { xs: "none", xl: "flex" } }}>
                    {authHighlights.map((item) => {
                      const Icon = item.icon;

                      return (
                        <Grid key={item.label} size={{ xs: 12, sm: 4 }}>
                          <Box
                            sx={{
                              p: 1,
                              height: "100%",
                              borderRadius: 2.5,
                              bgcolor: "rgba(255,255,255,0.14)",
                              border: "1px solid rgba(255,255,255,0.18)",
                              backdropFilter: "blur(10px)",
                            }}
                          >
                            <Icon sx={{ color: item.color, mb: 0.65, fontSize: 18 }} />
                            <Typography sx={{ color: "white", fontWeight: 800, fontSize: "0.86rem" }}>
                              {item.value}
                            </Typography>
                            <Typography sx={{ color: "rgba(255,255,255,0.76)", fontSize: "0.76rem" }}>
                              {item.label}
                            </Typography>
                          </Box>
                        </Grid>
                      );
                    })}
                  </Grid>
                </Stack>
              </Box>
            </Grid>

            <Grid size={{ xs: 12, md: 6.8 }}>
              <Box
                sx={{
                  height: "100%",
                  display: "flex",
                  alignItems: "center",
                  px: { xs: 0.5, md: 1.25 },
                  py: { xs: 0.5, md: 0.75 },
                }}
              >
                <Box sx={{ width: "100%" }}>{children}</Box>
              </Box>
            </Grid>
          </Grid>
        </Box>
      </Container>
    </Box>
  );
}

export default AuthLayout;
