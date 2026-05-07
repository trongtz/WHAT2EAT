import { Box, Modal, Typography } from "@mui/material";

function CustomModal({ open, onClose, title, children, width = 520 }) {
  return (
    <Modal
      open={open}
      onClose={onClose}
      sx={{
        display: "flex",
        alignItems: { xs: "flex-start", md: "center" },
        justifyContent: "center",
        p: { xs: 1.5, sm: 2.5 },
        overflowY: "auto",
      }}
    >
      <Box
        sx={{
          width: { xs: "100%", sm: width },
          maxWidth: "100%",
          my: { xs: 1.5, md: 0 },
          maxHeight: "calc(100dvh - 24px)",
          p: { xs: 2.2, sm: 2.6 },
          bgcolor: "background.paper",
          borderRadius: 2,
          boxShadow: "0 30px 60px rgba(28, 36, 64, 0.18)",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
        <Typography variant="h4" mb={2} sx={{ flexShrink: 0 }}>
          {title}
        </Typography>
        <Box sx={{ overflowY: "auto", pr: 0.4 }}>{children}</Box>
      </Box>
    </Modal>
  );
}

export default CustomModal;
