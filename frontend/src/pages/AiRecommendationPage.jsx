import AutoAwesomeRoundedIcon from "@mui/icons-material/AutoAwesomeRounded";
import PsychologyRoundedIcon from "@mui/icons-material/PsychologyRounded";
import { Alert, Grid, Stack, Typography } from "@mui/material";
import { useState } from "react";
import { Link as RouterLink } from "react-router-dom";
import CustomButton from "../components/CustomButton";
import CustomCard from "../components/CustomCard";
import FormInput from "../components/FormInput";
import LoadingScreen from "../components/LoadingScreen";
import RestaurantCard from "../components/RestaurantCard";
import SectionHeader from "../components/SectionHeader";
import { aiService } from "../services/aiService";
import { validatePrompt } from "../utils/validators";

function AiRecommendationPage() {
  const [prompt, setPrompt] = useState("Mình muốn ăn tối lãng mạn, ngân sách 500k cho 2 người ở trung tâm");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleSubmit = async (event) => {
    event.preventDefault();
    const nextError = validatePrompt(prompt);
    setError(nextError);
    if (nextError) return;
    setLoading(true);
    try {
      const data = await aiService.recommend({ prompt });
      setResult(data);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Stack spacing={3}>
      <SectionHeader
        eyebrow="AI Recommendation"
        title="Nhập prompt để nhận gợi ý"
        description="Mô tả tâm trạng, ngân sách, khu vực hoặc loại món. Hệ thống mock sẽ phản hồi như một AI assistant đề xuất nhà hàng."
      />

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 5 }}>
          <CustomCard
            sx={{
              background: "linear-gradient(180deg, rgba(255,255,255,0.95) 0%, rgba(246,240,255,0.92) 100%)",
            }}
          >
            <Stack component="form" spacing={2.5} onSubmit={handleSubmit}>
              <Typography variant="h4">Mô tả nhu cầu</Typography>
              {error ? <Alert severity="error">{error}</Alert> : null}
              <FormInput multiline rows={8} label="Prompt tiếng Việt" value={prompt} onChange={(event) => setPrompt(event.target.value)} />
              <CustomButton type="submit" startIcon={<PsychologyRoundedIcon />}>
                Phân tích và gợi ý
              </CustomButton>
            </Stack>
          </CustomCard>
        </Grid>
        <Grid size={{ xs: 12, md: 7 }}>
          {loading ? (
            <LoadingScreen message="AI đang tổng hợp gợi ý phù hợp..." />
          ) : result ? (
            <Stack spacing={3}>
              <CustomCard>
                <Stack direction="row" spacing={1.5} alignItems="center">
                  <AutoAwesomeRoundedIcon color="secondary" />
                  <Typography color="text.secondary">{result.summary}</Typography>
                </Stack>
              </CustomCard>
              <Grid container spacing={3}>
                {result.restaurants.map((restaurant) => (
                  <Grid key={restaurant.id} size={{ xs: 12 }}>
                    <RestaurantCard
                      compact
                      restaurant={restaurant}
                      action={
                        <CustomButton component={RouterLink} to={`/nha-hang/${restaurant.id}`}>
                          Xem chi tiết
                        </CustomButton>
                      }
                    />
                  </Grid>
                ))}
              </Grid>
            </Stack>
          ) : (
            <CustomCard>
              <Typography color="text.secondary">Kết quả AI sẽ hiển thị ở đây sau khi bạn nhập prompt.</Typography>
            </CustomCard>
          )}
        </Grid>
      </Grid>
    </Stack>
  );
}

export default AiRecommendationPage;
