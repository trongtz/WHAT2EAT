import ReplyRoundedIcon from "@mui/icons-material/ReplyRounded";
import StarRoundedIcon from "@mui/icons-material/StarRounded";
import { Alert, Grid, Stack, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import CustomButton from "../../components/CustomButton";
import CustomCard from "../../components/CustomCard";
import CustomModal from "../../components/CustomModal";
import EmptyState from "../../components/EmptyState";
import FormInput from "../../components/FormInput";
import LoadingScreen from "../../components/LoadingScreen";
import SectionHeader from "../../components/SectionHeader";
import { useAuth } from "../../hooks/useAuth";
import { dashboardService } from "../../services/dashboardService";
import { restaurantService } from "../../services/restaurantService";
import { formatDate } from "../../utils/helpers";

function OwnerReviewsPage() {
  const { user } = useAuth();
  const [reviews, setReviews] = useState([]);
  const [restaurantMap, setRestaurantMap] = useState({});
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [replyOpen, setReplyOpen] = useState(false);
  const [selectedReview, setSelectedReview] = useState(null);
  const [reply, setReply] = useState("");

  const loadData = async () => {
    const [reviewData, restaurantData] = await Promise.all([
      dashboardService.getOwnerReviews(user.id),
      restaurantService.getRestaurants(),
    ]);
    setReviews(reviewData);
    setRestaurantMap(Object.fromEntries(restaurantData.map((item) => [item.id, item])));
    setLoading(false);
  };

  useEffect(() => {
    loadData();
  }, [user.id]);

  const handleOpenReply = (review) => {
    setSelectedReview(review);
    setReply(review.ownerReply || "");
    setReplyOpen(true);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    await dashboardService.replyReview({ reviewId: selectedReview.id, reply });
    setMessage("Đã lưu phản hồi của nhà hàng.");
    setReplyOpen(false);
    await loadData();
  };

  if (loading) return <LoadingScreen message="Đang tải đánh giá của khách..." />;

  return (
    <Stack spacing={3}>
      <SectionHeader
        title="Quản lý đánh giá"
        description="Đọc phản hồi của khách và trả lời trực tiếp ngay trong hệ thống."
      />
      {message ? <Alert severity="success">{message}</Alert> : null}
      {reviews.length ? (
        <Grid container spacing={3}>
          {reviews.map((review) => (
            <Grid key={review.id} size={{ xs: 12, xl: 6 }}>
              <CustomCard>
                <Stack spacing={1.5}>
                  <Typography variant="h4">
                    {restaurantMap[review.restaurantId]?.name || "Nhà hàng"}
                  </Typography>
                  <Typography color="text.secondary">{review.userName}</Typography>
                  <Stack direction="row" spacing={0.5} alignItems="center">
                    <StarRoundedIcon sx={{ color: "#F59E0B" }} />
                    <Typography fontWeight={700}>{review.rating}/5</Typography>
                  </Stack>
                  <Typography color="text.secondary">{review.comment}</Typography>
                  <Typography color="text.secondary">{formatDate(review.createdAt)}</Typography>
                  <Typography fontWeight={700}>Phản hồi của nhà hàng</Typography>
                  <Typography color="text.secondary">
                    {review.ownerReply || "Chưa có phản hồi"}
                  </Typography>
                  <CustomButton
                    startIcon={<ReplyRoundedIcon />}
                    onClick={() => handleOpenReply(review)}
                    sx={{ alignSelf: "flex-start" }}
                  >
                    {review.ownerReply ? "Cập nhật phản hồi" : "Trả lời đánh giá"}
                  </CustomButton>
                </Stack>
              </CustomCard>
            </Grid>
          ))}
        </Grid>
      ) : (
        <EmptyState
          title="Chưa có đánh giá nào"
          description="Đánh giá mới từ khách hàng sẽ được cập nhật tại đây."
        />
      )}

      <CustomModal open={replyOpen} onClose={() => setReplyOpen(false)} title="Phản hồi đánh giá">
        <Stack component="form" spacing={2} onSubmit={handleSubmit}>
          <Typography color="text.secondary">{selectedReview?.comment}</Typography>
          <FormInput
            multiline
            rows={4}
            label="Nội dung phản hồi"
            value={reply}
            onChange={(event) => setReply(event.target.value)}
          />
          <Stack direction="row" spacing={1.5}>
            <CustomButton type="submit">Lưu phản hồi</CustomButton>
            <CustomButton
              type="button"
              onClick={() => setReplyOpen(false)}
              sx={{ background: "linear-gradient(135deg, #64748B 0%, #94A3B8 100%)" }}
            >
              Đóng
            </CustomButton>
          </Stack>
        </Stack>
      </CustomModal>
    </Stack>
  );
}

export default OwnerReviewsPage;
