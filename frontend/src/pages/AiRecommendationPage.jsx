import AutoAwesomeRoundedIcon from "@mui/icons-material/AutoAwesomeRounded";
import InsightsRoundedIcon from "@mui/icons-material/InsightsRounded";
import PlaceRoundedIcon from "@mui/icons-material/PlaceRounded";
import PsychologyRoundedIcon from "@mui/icons-material/PsychologyRounded";
import RadarRoundedIcon from "@mui/icons-material/RadarRounded";
import RestaurantRoundedIcon from "@mui/icons-material/RestaurantRounded";
import TipsAndUpdatesRoundedIcon from "@mui/icons-material/TipsAndUpdatesRounded";
import TuneRoundedIcon from "@mui/icons-material/TuneRounded";
import {
  Alert,
  Box,
  Chip,
  Divider,
  Grid,
  Stack,
  Typography,
} from "@mui/material";
import { useMemo, useState } from "react";
import { Link as RouterLink } from "react-router-dom";
import CustomButton from "../components/CustomButton";
import CustomCard from "../components/CustomCard";
import EmptyState from "../components/EmptyState";
import FormInput from "../components/FormInput";
import RestaurantCard from "../components/RestaurantCard";
import SectionHeader from "../components/SectionHeader";
import { aiService } from "../services/aiService";
import { restaurantService } from "../services/restaurantService";
import { formatPriceRangeDisplay } from "../utils/helpers";
import { validatePrompt } from "../utils/validators";

const starterPrompts = [
  "Tối nay muốn ăn lãng mạn, yên tĩnh, ngân sách khoảng 500k cho 2 người ở quận 1.",
  "Nhóm 4 người muốn ăn no, nhiều món chia sẻ, giá vừa phải và có chỗ ngồi thoải mái.",
  "Mình cần quán gần trung tâm để gặp đối tác, không gian gọn gàng và phục vụ nhanh.",
];

const scenarioChips = [
  "Hẹn hò buổi tối",
  "Đi ăn cùng nhóm bạn",
  "Gia đình có trẻ nhỏ",
  "Ăn trưa nhanh gần công ty",
  "Tiệc sinh nhật nhỏ",
  "Muốn thử món mới",
];

const getPromptSignals = (prompt) => {
  const normalizedPrompt = prompt.toLowerCase();

  return {
    romantic: /(lang man|lãng mạn|hen ho|hẹn hò|toi|tối)/.test(normalizedPrompt),
    group: /(nhom|nhóm|ban be|bạn bè|dong nghiep|đồng nghiệp|gia dinh|gia đình)/.test(normalizedPrompt),
    premium: /(500k|cao cap|cao cấp|sang|fine dining|dat tien|đắt tiền)/.test(normalizedPrompt),
    budget: /(re|rẻ|tiet kiem|tiết kiệm|duoi 100|cheap|binh dan|bình dân)/.test(normalizedPrompt),
    quick: /(nhanh|gap|gấp|trua|trưa|van phong|văn phòng)/.test(normalizedPrompt),
  };
};

const buildLocalRecommendation = (prompt, restaurants) => {
  const signals = getPromptSignals(prompt);

  const scoredRestaurants = restaurants
    .map((restaurant) => {
      let score = Number(restaurant.averageRating || restaurant.rating || 0) * 12;

      if (signals.romantic && /(Âu|Nhật|Hàn|steak|cafe|cà phê|fine)/i.test(restaurant.name + restaurant.category)) {
        score += 20;
      }

      if (signals.group && Number(restaurant.maxCapacity || 0) >= 20) {
        score += 16;
      }

      if (signals.premium && restaurant.priceRange === "expensive") {
        score += 18;
      }

      if (signals.budget && restaurant.priceRange === "cheap") {
        score += 18;
      }

      if (signals.quick && /(ăn nhanh|fast|gà|cơm|bún|phở)/i.test(restaurant.category || restaurant.name)) {
        score += 14;
      }

      if (restaurant.reviewCount) {
        score += Math.min(Number(restaurant.reviewCount), 30);
      }

      return { ...restaurant, score };
    })
    .sort((firstRestaurant, secondRestaurant) => secondRestaurant.score - firstRestaurant.score);

  const picks = scoredRestaurants.slice(0, 4);
  const averageBudget =
    picks.find((restaurant) => restaurant.priceRange)?.priceRange || restaurants[0]?.priceRange || "mid";

  return {
    summary: "Đây là bản xem trước giao diện gợi ý AI. Hệ thống đang dựng đề xuất từ dữ liệu nhà hàng hiện có để bạn hoàn thiện backend prompt sau.",
    strategy: signals.romantic
      ? "Ưu tiên không gian có cảm giác riêng tư, điểm đánh giá ổn định và mức giá phù hợp cho trải nghiệm buổi tối."
      : signals.group
        ? "Ưu tiên nhà hàng có sức chứa tốt, menu dễ chia sẻ và review đủ nhiều để giảm rủi ro khi đi nhóm."
        : signals.quick
          ? "Ưu tiên quán dễ chọn nhanh, tín hiệu phục vụ gọn và mức giá dễ tiếp cận cho nhu cầu hằng ngày."
          : "Ưu tiên nhà hàng có đánh giá tốt, thông tin đầy đủ và mức giá cân bằng để ra quyết định nhanh hơn.",
    highlights: [
      `Ngân sách tham chiếu phù hợp nhất hiện tại: ${formatPriceRangeDisplay(averageBudget)}.`,
      `${picks.length} lựa chọn đầu bảng được gom từ dữ liệu nhà hàng hiện có.`,
      "Có thể thay phần scoring này bằng response thật từ backend AI mà không cần đổi cấu trúc màn hình.",
    ],
    restaurants: picks,
  };
};

function AiRecommendationPage() {
  const [prompt, setPrompt] = useState(starterPrompts[0]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const promptMeta = useMemo(() => {
    const words = prompt.trim() ? prompt.trim().split(/\s+/).length : 0;
    return {
      words,
      hasEnoughContext: words >= 8,
    };
  }, [prompt]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    const nextError = validatePrompt(prompt);
    setError(nextError);
    if (nextError) return;

    setLoading(true);

    try {
      const data = await aiService.recommend({ prompt });
      setResult(data);
    } catch {
      const restaurants = await restaurantService.getRestaurants();
      setResult(buildLocalRecommendation(prompt, restaurants));
    } finally {
      setLoading(false);
    }
  };

  const handleUsePrompt = (value) => {
    setPrompt(value);
    setError("");
  };

  return (
    <Stack spacing={4}>
      <SectionHeader
        eyebrow="AI Concierge"
        title="Gợi ý quán ăn theo ngữ cảnh của bạn"
        description="Thiết kế theo kiểu trợ lý chọn quán: nhập brief, xem cách hệ thống hiểu nhu cầu, rồi nhận danh sách đề xuất có cấu trúc rõ ràng."
      />

      <Grid container spacing={3} alignItems="stretch">
        <Grid size={{ xs: 12, lg: 4.5 }}>
          <CustomCard sx={{ height: "100%" }}>
            <Stack component="form" spacing={2.3} onSubmit={handleSubmit}>
              <Stack spacing={0.75}>
                <Stack direction="row" spacing={1} alignItems="center">
                  <TuneRoundedIcon sx={{ color: "var(--app-secondary)" }} />
                  <Typography variant="h4">Viết brief cho trợ lý gợi ý</Typography>
                </Stack>
                <Typography color="text.secondary">
                  Cứ mô tả như đang nhắn với một người bạn biết nhiều quán ăn.
                </Typography>
              </Stack>

              {error ? <Alert severity="error">{error}</Alert> : null}

              <FormInput
                multiline
                rows={9}
                label="Prompt mô tả nhu cầu"
                value={prompt}
                onChange={(event) => setPrompt(event.target.value)}
                helperText={
                  promptMeta.hasEnoughContext
                    ? `${promptMeta.words} từ. Mô tả hiện đã đủ để trả về gợi ý có cấu trúc.`
                    : `${promptMeta.words} từ. Thêm ngân sách, số người hoặc bối cảnh để kết quả tốt hơn.`
                }
              />

              <Stack spacing={1}>
                <Typography sx={{ fontSize: "0.92rem", fontWeight: 700 }}>Prompt mẫu</Typography>
                <Stack spacing={1}>
                  {starterPrompts.map((item) => (
                    <Box
                      key={item}
                      onClick={() => handleUsePrompt(item)}
                      sx={{
                        p: 1.25,
                        borderRadius: 2,
                        cursor: "pointer",
                        bgcolor: "rgba(248,250,255,0.9)",
                        border: "1px solid rgba(15,23,42,0.08)",
                        transition: "border-color 0.2s ease, transform 0.2s ease",
                        "&:hover": {
                          borderColor: "color-mix(in srgb, var(--app-primary) 24%, white)",
                          transform: "translateY(-1px)",
                        },
                      }}
                    >
                      <Typography color="text.secondary" sx={{ fontSize: "0.93rem", lineHeight: 1.55 }}>
                        {item}
                      </Typography>
                    </Box>
                  ))}
                </Stack>
              </Stack>

              <CustomButton type="submit" startIcon={<PsychologyRoundedIcon />} sx={{ alignSelf: "flex-start" }}>
                Tạo gợi ý ngay
              </CustomButton>
            </Stack>
          </CustomCard>
        </Grid>

        <Grid size={{ xs: 12, lg: 7.5 }}>
          <Stack spacing={3}>
            {!result && !loading ? (
              <CustomCard>
                <Stack spacing={2}>
                  <Stack direction="row" spacing={1} alignItems="center">
                    <RestaurantRoundedIcon sx={{ color: "var(--app-primary)" }} />
                    <Typography variant="h4">Kết quả đề xuất sẽ hiện ở đây</Typography>
                  </Stack>
                  <Typography color="text.secondary">
                    Sau khi nhập prompt, màn hình sẽ hiển thị 3 phần chính: tóm tắt brief, logic gợi ý và danh sách
                    quán nên xem trước.
                  </Typography>
                  <Grid container spacing={1.5}>
                    {[
                      { label: "Brief", text: "AI hiểu bạn đang tìm trải nghiệm gì." },
                      { label: "Insight", text: "Vì sao hệ thống chọn nhóm quán này." },
                      { label: "Picks", text: "Danh sách quán với CTA rõ ràng để đi tiếp." },
                    ].map((item) => (
                      <Grid key={item.label} size={{ xs: 12, md: 4 }}>
                        <Box
                          sx={{
                            p: 1.5,
                            borderRadius: 2,
                            bgcolor: "rgba(248,250,255,0.92)",
                            border: "1px solid rgba(15,23,42,0.06)",
                            height: "100%",
                          }}
                        >
                          <Typography sx={{ fontWeight: 800, mb: 0.55 }}>{item.label}</Typography>
                          <Typography color="text.secondary" sx={{ fontSize: "0.92rem" }}>
                            {item.text}
                          </Typography>
                        </Box>
                      </Grid>
                    ))}
                  </Grid>
                </Stack>
              </CustomCard>
            ) : null}

            {loading ? (
              <CustomCard>
                <Stack spacing={2}>
                  <Chip
                    icon={<AutoAwesomeRoundedIcon />}
                    label="Đang dựng đề xuất"
                    sx={{
                      alignSelf: "flex-start",
                      bgcolor: "color-mix(in srgb, var(--app-primary) 10%, white)",
                      color: "var(--app-primary)",
                    }}
                  />
                  <Typography variant="h4">Hệ thống đang đọc brief và ghép nhóm quán phù hợp.</Typography>
                  <Typography color="text.secondary">
                    Sau này bạn có thể thay bước này bằng response streaming hoặc reasoning thật từ backend AI.
                  </Typography>
                </Stack>
              </CustomCard>
            ) : null}

            {result ? (
              <>
                <Grid container spacing={2}>
                  <Grid size={{ xs: 12, md: 6 }}>
                    <CustomCard sx={{ height: "100%" }}>
                      <Stack spacing={1.25}>
                        <Chip
                          icon={<TipsAndUpdatesRoundedIcon />}
                          label="Tóm tắt đề xuất"
                          sx={{
                            alignSelf: "flex-start",
                            bgcolor: "color-mix(in srgb, var(--app-primary) 10%, white)",
                            color: "var(--app-primary)",
                          }}
                        />
                        <Typography variant="h4">AI brief</Typography>
                        <Typography color="text.secondary">{result.summary}</Typography>
                      </Stack>
                    </CustomCard>
                  </Grid>

                  <Grid size={{ xs: 12, md: 6 }}>
                    <CustomCard sx={{ height: "100%" }}>
                      <Stack spacing={1.25}>
                        <Chip
                          icon={<InsightsRoundedIcon />}
                          label="Cách hệ thống đang suy luận"
                          sx={{
                            alignSelf: "flex-start",
                            bgcolor: "color-mix(in srgb, var(--app-secondary) 10%, white)",
                            color: "var(--app-secondary)",
                          }}
                        />
                        <Typography variant="h4">Strategy</Typography>
                        <Typography color="text.secondary">
                          {result.strategy || "Backend AI có thể trả về phần giải thích này để người dùng hiểu vì sao được gợi ý."}
                        </Typography>
                      </Stack>
                    </CustomCard>
                  </Grid>
                </Grid>

                {Array.isArray(result.highlights) && result.highlights.length ? (
                  <CustomCard>
                    <Stack spacing={1.35}>
                      <Typography variant="h4">Điểm đáng chú ý</Typography>
                      <Grid container spacing={1.5}>
                        {result.highlights.map((item) => (
                          <Grid key={item} size={{ xs: 12, md: 4 }}>
                            <Box
                              sx={{
                                p: 1.55,
                                height: "100%",
                                borderRadius: 2,
                                bgcolor: "rgba(248,250,255,0.92)",
                                border: "1px solid rgba(15,23,42,0.06)",
                              }}
                            >
                              <Typography color="text.secondary" sx={{ lineHeight: 1.6 }}>
                                {item}
                              </Typography>
                            </Box>
                          </Grid>
                        ))}
                      </Grid>
                    </Stack>
                  </CustomCard>
                ) : null}

                {Array.isArray(result.restaurants) && result.restaurants.length ? (
                  <Stack spacing={2}>
                    <SectionHeader
                      eyebrow="Top Picks"
                      title="Những quán nên xem trước"
                      description="Giữ bố cục kiểu editorial để sau này backend AI có thể thay đổi nội dung mà không phải sửa lại màn hình."
                    />
                    <Grid container spacing={3}>
                      {result.restaurants.map((restaurant, index) => (
                        <Grid key={restaurant.id || `${restaurant.name}-${index}`} size={{ xs: 12, md: 6 }}>
                          <Stack spacing={1.1}>
                            <Stack direction="row" spacing={1} alignItems="center">
                              <Chip
                                label={`Lựa chọn ${index + 1}`}
                                sx={{
                                  bgcolor: "rgba(255,255,255,0.92)",
                                  color: "var(--app-primary)",
                                  fontWeight: 800,
                                }}
                              />
                              <Stack direction="row" spacing={0.6} alignItems="center">
                                <PlaceRoundedIcon sx={{ fontSize: 16, color: "var(--app-secondary)" }} />
                                <Typography color="text.secondary" sx={{ fontSize: "0.92rem" }}>
                                  {restaurant.address || "Chưa có địa chỉ chi tiết"}
                                </Typography>
                              </Stack>
                            </Stack>
                            <RestaurantCard
                              compact
                              restaurant={restaurant}
                              hideFavoriteButton
                              action={
                                <CustomButton component={RouterLink} to={`/nha-hang/${restaurant.id}`}>
                                  Xem nhà hàng
                                </CustomButton>
                              }
                            />
                          </Stack>
                        </Grid>
                      ))}
                    </Grid>
                  </Stack>
                ) : (
                  <EmptyState
                    title="Chưa có gợi ý phù hợp"
                    description="Bạn có thể nới ngân sách, đổi khu vực hoặc mô tả mục tiêu buổi ăn cụ thể hơn."
                  />
                )}
              </>
            ) : null}
          </Stack>
        </Grid>
      </Grid>

      <Box
        className="glass-panel"
        sx={{
          p: { xs: 2, md: 2.4 },
          borderRadius: 3,
          overflow: "hidden",
          background:
            "linear-gradient(135deg, color-mix(in srgb, var(--app-primary) 10%, white) 0%, rgba(255,255,255,0.94) 42%, color-mix(in srgb, var(--app-secondary) 10%, white) 100%)",
          border: "1px solid rgba(255,255,255,0.8)",
          boxShadow: "0 26px 56px rgba(15, 23, 42, 0.08)",
        }}
      >
        <Grid container spacing={2.2} alignItems="stretch">
          <Grid size={{ xs: 12, lg: 7.4 }}>
            <Stack spacing={2.2} sx={{ height: "100%", justifyContent: "space-between" }}>
              <Stack spacing={1.35}>
                <Chip
                  icon={<TipsAndUpdatesRoundedIcon />}
                  label="Preview mode cho màn AI suggestion"
                  sx={{
                    alignSelf: "flex-start",
                    bgcolor: "rgba(255,255,255,0.84)",
                    color: "var(--app-primary)",
                  }}
                />
                <Typography
                  variant="h1"
                  sx={{
                    maxWidth: 760,
                    fontSize: { xs: "2rem", md: "2.9rem" },
                    lineHeight: { xs: 1.14, md: 1.06 },
                  }}
                >
                  Một màn gợi ý đủ đẹp để sau này chỉ việc cắm backend AI thật vào.
                </Typography>
                <Typography color="text.secondary" sx={{ maxWidth: 700, fontSize: "1.03rem" }}>
                  Trang này tập trung vào trải nghiệm nhập nhu cầu và đọc kết quả. Nếu backend AI chưa sẵn sàng,
                  hệ thống sẽ tự dùng dữ liệu nhà hàng hiện có để dựng bản xem trước có cấu trúc tương tự.
                </Typography>
              </Stack>

              <Grid container spacing={1.5}>
                {[
                  {
                    icon: PsychologyRoundedIcon,
                    label: "Prompt rõ ngữ cảnh",
                    value: "mood, ngân sách, khu vực",
                  },
                  {
                    icon: InsightsRoundedIcon,
                    label: "Tóm tắt lý do chọn",
                    value: "đọc nhanh trong 5 giây",
                  },
                  {
                    icon: RadarRoundedIcon,
                    label: "Kết quả có cấu trúc",
                    value: "brief, insight, danh sách",
                  },
                ].map((item) => {
                  const Icon = item.icon;

                  return (
                    <Grid key={item.label} size={{ xs: 12, md: 4 }}>
                      <Box
                        sx={{
                          p: 1.65,
                          height: "100%",
                          borderRadius: 2.4,
                          bgcolor: "rgba(255,255,255,0.76)",
                          border: "1px solid rgba(255,255,255,0.72)",
                        }}
                      >
                        <Stack spacing={0.8}>
                          <Box
                            sx={{
                              width: 44,
                              height: 44,
                              borderRadius: 1.8,
                              display: "grid",
                              placeItems: "center",
                              background:
                                "linear-gradient(135deg, color-mix(in srgb, var(--app-primary) 16%, white), color-mix(in srgb, var(--app-secondary) 12%, white))",
                            }}
                          >
                            <Icon sx={{ color: "var(--app-primary)" }} />
                          </Box>
                          <Typography sx={{ fontWeight: 800 }}>{item.label}</Typography>
                          <Typography color="text.secondary" sx={{ fontSize: "0.92rem" }}>
                            {item.value}
                          </Typography>
                        </Stack>
                      </Box>
                    </Grid>
                  );
                })}
              </Grid>
            </Stack>
          </Grid>

          <Grid size={{ xs: 12, lg: 4.6 }}>
            <CustomCard
              sx={{
                height: "100%",
                background: "rgba(255,255,255,0.88)",
                boxShadow: "0 24px 48px rgba(15, 23, 42, 0.08)",
              }}
            >
              <Stack spacing={1.8}>
                <Stack direction="row" spacing={1.1} alignItems="center">
                  <AutoAwesomeRoundedIcon sx={{ color: "var(--app-primary)" }} />
                  <Typography variant="h4">Những gì AI nên hiểu từ prompt</Typography>
                </Stack>

                <Stack spacing={1.2}>
                  {[
                    "Bạn đi một mình, đi đôi hay đi nhóm.",
                    "Mức ngân sách mong muốn và khung thời gian.",
                    "Khu vực, khoảng cách chấp nhận hoặc phong cách quán.",
                    "Mục tiêu buổi ăn: chill, hẹn hò, gặp đối tác hay ăn nhanh.",
                  ].map((item) => (
                    <Stack key={item} direction="row" spacing={1.1} alignItems="flex-start">
                      <Box
                        sx={{
                          width: 8,
                          height: 8,
                          mt: "8px",
                          borderRadius: "50%",
                          bgcolor: "var(--app-secondary)",
                          flexShrink: 0,
                        }}
                      />
                      <Typography color="text.secondary">{item}</Typography>
                    </Stack>
                  ))}
                </Stack>

                <Divider />

                <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                  {scenarioChips.map((item) => (
                    <Chip
                      key={item}
                      label={item}
                      onClick={() => handleUsePrompt(`Mình cần gợi ý cho trường hợp: ${item}.`)}
                      sx={{
                        bgcolor: "color-mix(in srgb, var(--app-primary) 9%, white)",
                        color: "var(--app-primary)",
                      }}
                    />
                  ))}
                </Stack>
              </Stack>
            </CustomCard>
          </Grid>
        </Grid>
      </Box>
    </Stack>
  );
}

export default AiRecommendationPage;
