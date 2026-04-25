import { Box, Container, Grid, Typography } from "@mui/material";

function AuthLayout({ title, subtitle, children }) {
  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        py: 4,
        background:
          "radial-gradient(circle at top left, rgba(255,179,71,0.28), transparent 28%), radial-gradient(circle at bottom right, rgba(47,107,255,0.18), transparent 30%)",
      }}
    >
      <Container maxWidth="lg">
        <Grid container spacing={4} alignItems="center">
          <Grid size={{ xs: 12, md: 6 }}>
            <Typography variant="h1" mb={2}>
              {title}
            </Typography>
            <Typography color="text.secondary" fontSize="1.1rem" maxWidth={520}>
              {subtitle}
            </Typography>
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>{children}</Grid>
        </Grid>
      </Container>
    </Box>
  );
}

export default AuthLayout;
