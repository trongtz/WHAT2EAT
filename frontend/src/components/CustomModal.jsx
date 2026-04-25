import { Box, Modal, Typography } from "@mui/material";

function CustomModal({ open, onClose, title, children }) {
  return (
    <Modal open={open} onClose={onClose}>
      <Box
        sx={{
          width: { xs: "92%", sm: 520 },
          p: 3,
          bgcolor: "background.paper",
          borderRadius: 2,
          boxShadow: "0 30px 60px rgba(28, 36, 64, 0.18)",
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
        }}
      >
        <Typography variant="h4" mb={2}>
          {title}
        </Typography>
        {children}
      </Box>
    </Modal>
  );
}

export default CustomModal;
