import { Stack, Typography } from "@mui/material";
import { Link as RouterLink } from "react-router-dom";
import CustomButton from "../components/CustomButton";
import CustomCard from "../components/CustomCard";

function NotFoundPage() {
  return (
    <CustomCard>
      <Stack spacing={2} alignItems="flex-start">
        <Typography variant="h2">Không tìm thấy trang</Typography>
        <Typography color="text.secondary">Đường dẫn bạn truy cập không tồn tại hoặc đã được thay đổi.</Typography>
        <CustomButton component={RouterLink} to="/">
          Quay về trang chủ
        </CustomButton>
      </Stack>
    </CustomCard>
  );
}

export default NotFoundPage;
