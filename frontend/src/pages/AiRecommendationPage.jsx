import AddCommentRoundedIcon from "@mui/icons-material/AddCommentRounded";
import FmdGoodRoundedIcon from "@mui/icons-material/FmdGoodRounded";
import LocationOnRoundedIcon from "@mui/icons-material/LocationOnRounded";
import PsychologyRoundedIcon from "@mui/icons-material/PsychologyRounded";
import RestaurantRoundedIcon from "@mui/icons-material/RestaurantRounded";
import SendRoundedIcon from "@mui/icons-material/SendRounded";
import StarRoundedIcon from "@mui/icons-material/StarRounded";
import { Alert, Avatar, Box, Chip, CircularProgress, Grid, Stack, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import { Link as RouterLink } from "react-router-dom";
import CustomButton from "../components/CustomButton";
import CustomCard from "../components/CustomCard";
import FormInput from "../components/FormInput";
import AppLogoImage from "../components/AppLogoImage";
import { useAuth } from "../hooks/useAuth";
import { aiService } from "../services/aiService";
import { normalizeRestaurant, restaurantService } from "../services/restaurantService";
import { formatPriceRangeDisplay } from "../utils/helpers";
import { validatePrompt } from "../utils/validators";

const fallbackMessage =
  "AI Assistant hiện chưa phản hồi được. Hệ thống đã chuyển sang tìm kiếm cơ bản dựa trên nội dung bạn nhập.";

const noResultMessage =
  "Không tìm thấy nhà hàng phù hợp với yêu cầu hiện tại. Bạn có thể thử mở rộng khu vực, tăng ngân sách hoặc thay đổi loại món ăn.";

const AI_CHAT_STORAGE_KEY = "what2eat:ai-recommendation-chat";

const createSessionId = () => crypto.randomUUID();

const getPromptSignals = (prompt) => {
  const normalizedPrompt = String(prompt || "").toLowerCase();

  return {
    hotFood: /(nong|lau|pho|bun|sup|chao)/.test(normalizedPrompt),
    cafe: /(cafe|ca phe|coffee)/.test(normalizedPrompt),
    quiet: /(yen tinh|hoc bai|lam viec|work|study)/.test(normalizedPrompt),
    dateNight: /(hen ho|lang man|am cung|date)/.test(normalizedPrompt),
    district1: /(quan 1|q1|district 1)/.test(normalizedPrompt),
    budgetLow: /(duoi 100|100k|binh dan|gia re|re)/.test(normalizedPrompt),
    tableNeed: /(con ban|dat ban|4 nguoi|19h|19:00)/.test(normalizedPrompt),
  };
};

const getRecommendationReason = (restaurant, prompt) => {
  const signals = getPromptSignals(prompt);
  const reasons = [];
  const title = `${restaurant.name || ""} ${restaurant.category || ""}`.toLowerCase();

  if (signals.cafe && /(cafe|coffee|tra|tea)/.test(title)) reasons.push("Phù hợp với nhu cầu tìm quán cà phê.");
  if (signals.quiet) reasons.push("Không gian phù hợp cho nhu cầu ngồi lâu, trò chuyện hoặc học bài.");
  if (signals.dateNight) reasons.push("Phong cách quán hợp cho buổi hẹn hò hoặc bữa tối ấm cúng.");
  if (signals.hotFood && /(lau|pho|bun|nuoc|sup|chao|bo|nuong)/.test(title)) reasons.push("Menu có xu hướng hợp với món nóng.");
  if (signals.budgetLow && restaurant.priceRange === "cheap") reasons.push("Mức giá đang nằm trong nhóm dễ tiếp cận.");
  if (signals.district1 && /quan 1|district 1/i.test(restaurant.address || "")) reasons.push("Vị trí có vẻ gần khu vực Quận 1.");
  if (signals.tableNeed && Number(restaurant.availableCapacity || 0) > 0) reasons.push("Hiện còn bàn trống cho nhu cầu đặt bàn.");
  if (Number(restaurant.averageRating || restaurant.rating || 0) >= 4.2) reasons.push("Điểm đánh giá đang ở mức tốt.");

  return reasons[0] || "Thông tin nhà hàng khớp khá tốt với mô tả bạn vừa nhập.";
};

const buildFallbackRecommendation = (prompt, restaurants) => {
  const signals = getPromptSignals(prompt);

  const picks = restaurants
    .map((item) => {
      const restaurant = normalizeRestaurant(item);
      let score = Number(restaurant.averageRating || restaurant.rating || 0) * 10;
      const title = `${restaurant.name || ""} ${restaurant.category || ""}`.toLowerCase();
      const address = String(restaurant.address || "").toLowerCase();

      if (signals.cafe && /(cafe|coffee|tra|tea)/.test(title)) score += 24;
      if (signals.quiet) score += 12;
      if (signals.dateNight && /(au|nhat|han|steak|bbq|fine|grill)/.test(title)) score += 20;
      if (signals.hotFood && /(lau|pho|bun|sup|chao|nuoc)/.test(title)) score += 18;
      if (signals.budgetLow && restaurant.priceRange === "cheap") score += 22;
      if (signals.district1 && /quan 1|district 1/.test(address)) score += 18;
      if (signals.tableNeed && Number(restaurant.availableCapacity || 0) > 0) score += 20;
      if (Number(restaurant.reviewCount || 0) > 0) score += Math.min(Number(restaurant.reviewCount || 0), 20);

      return {
        ...restaurant,
        score,
        aiReason: getRecommendationReason(restaurant, prompt),
      };
    })
    .sort((a, b) => b.score - a.score)
    .slice(0, 4);

  return {
    restaurants: picks,
    isEmpty: picks.length === 0,
  };
};

const createAssistantMessage = ({ text, restaurants = [], isFallback = false, isEmpty = false, agent = null, booking = null }) => {
  const safeRestaurants = Array.isArray(restaurants) ? restaurants : [];

  return {
    id: `assistant-${Date.now()}-${Math.random().toString(16).slice(2)}`,
    role: "assistant",
    text,
    restaurants: safeRestaurants,
    isFallback,
    isEmpty: Boolean(isEmpty && safeRestaurants.length === 0),
    agent,
    booking,
  };
};

const createUserMessage = (text) => ({
  id: `user-${Date.now()}-${Math.random().toString(16).slice(2)}`,
  role: "user",
  text,
});

const createInitialMessages = (text = "Chào bạn, hãy mô tả nhu cầu của bạn để mình gợi ý nhà hàng phù hợp.") => [
  createAssistantMessage({ text }),
];

const getStoredChat = () => {
  if (typeof window === "undefined") return null;

  try {
    const rawValue = window.sessionStorage.getItem(AI_CHAT_STORAGE_KEY);
    if (!rawValue) return null;

    const parsed = JSON.parse(rawValue);
    if (!parsed?.sessionId || !Array.isArray(parsed?.messages)) return null;

    return {
      sessionId: parsed.sessionId,
      messages: parsed.messages,
    };
  } catch {
    window.sessionStorage.removeItem(AI_CHAT_STORAGE_KEY);
    return null;
  }
};

const getRatingLabel = (restaurant) => {
  const rating = Number(restaurant.averageRating || restaurant.rating || 0);
  return rating > 0 ? rating.toFixed(1) : "Mới";
};

const buildRecommendationReply = (message, restaurants) => {
  if (!restaurants.length) return message || noResultMessage;

  const reasonText = restaurants
    .flatMap((restaurant) => String(restaurant.aiReason || restaurant.reason || "").split("."))
    .map((reason) => reason.trim())
    .filter(Boolean);
  const uniqueReasons = [...new Set(reasonText)].slice(0, 3);
  const names = restaurants
    .slice(0, 3)
    .map((restaurant) => restaurant.name)
    .filter(Boolean)
    .join(", ");
  const reasonSentence = uniqueReasons.length
    ? uniqueReasons.join(". ") + "."
    : "các quán này phù hợp với mô tả bạn vừa nhập.";

  return `Mình tìm được vài lựa chọn hợp nè. Mình ưu tiên các quán trong danh sách vì ${reasonSentence}`;
};

const buildAssistantReply = ({ source, message, restaurants }) => {
  if (source === "AGENT") return message || "";
  if (restaurants.length) return buildRecommendationReply(message, restaurants);
  return buildRecommendationReply(message, restaurants);
};

const getAgentStatusLabel = (status) => {
  const labels = {
    restaurant_selected: "Đã chọn quán",
    needs_restaurant: "Cần chọn quán",
    needs_booking_info: "Cần thêm thông tin",
    awaiting_booking_confirmation: "Chờ xác nhận đặt bàn",
    booking_created: "Đã tạo booking",
    booking_cancelled: "Đã hủy bước đặt",
    booking_rejected: "Không thể đặt",
    needs_login: "Cần đăng nhập",
    preference_saved: "Đã ghi nhớ sở thích",
  };
  return labels[status] || "Agent đang xử lý";
};

const getAgentStatusColor = (status) => {
  if (status === "booking_created") return "success";
  if (["booking_rejected", "needs_login"].includes(status)) return "error";
  if (["awaiting_booking_confirmation", "needs_booking_info", "needs_restaurant"].includes(status)) return "warning";
  return "info";
};

function RecommendationListCard({ restaurant, index }) {
  return (
    <Box
      component={RouterLink}
      to={`/nha-hang/${restaurant.id}`}
      sx={{
        display: "block",
        p: 1.3,
        borderRadius: 3.5,
        textDecoration: "none",
        bgcolor: "rgba(255,255,255,0.9)",
        border: "1px solid rgba(15,23,42,0.06)",
        boxShadow: "0 18px 40px rgba(15,23,42,0.06)",
        transition: "transform 0.2s ease, box-shadow 0.2s ease",
        "&:hover": {
          transform: "translateY(-2px)",
          boxShadow: "0 24px 44px rgba(15,23,42,0.1)",
        },
      }}
    >
      <Stack direction="row" spacing={1.2} alignItems="stretch">
        <Box
          sx={{
            width: 88,
            minWidth: 88,
            height: 88,
            borderRadius: 3,
            overflow: "hidden",
            backgroundImage: restaurant.image
              ? `linear-gradient(180deg, rgba(18,22,44,0.04), rgba(18,22,44,0.18)), url(${restaurant.image})`
              : "linear-gradient(135deg, rgba(47,133,90,0.92), rgba(104,211,145,0.72))",
            backgroundSize: "cover",
            backgroundPosition: "center",
          }}
        />

        <Stack spacing={0.7} sx={{ minWidth: 0, flex: 1, justifyContent: "space-between" }}>
          <Stack sx={{ minWidth: 0 }}>
            <Typography
              variant="h4"
              sx={{
                fontSize: "0.95rem",
                lineHeight: 1.22,
                color: "var(--app-text-primary)",
                display: "-webkit-box",
                WebkitLineClamp: 2,
                WebkitBoxOrient: "vertical",
                overflow: "hidden",
              }}
            >
              {restaurant.name}
            </Typography>
            <Typography
              color="text.secondary"
              sx={{
                fontSize: "0.86rem",
                mt: 0.1,
                display: "-webkit-box",
                WebkitLineClamp: 2,
                WebkitBoxOrient: "vertical",
                overflow: "hidden",
              }}
            >
              {restaurant.address || "Chưa cập nhật địa chỉ"}
            </Typography>
          </Stack>

          <Stack direction="row" spacing={0.8} alignItems="center" justifyContent="space-between">
            <Stack direction="row" spacing={0.55} alignItems="center">
              <FmdGoodRoundedIcon sx={{ fontSize: 15, color: "var(--app-secondary)" }} />
              <Typography
                fontWeight={700}
                sx={{
                  color: "var(--app-secondary)",
                  fontSize: "0.82rem",
                  whiteSpace: "nowrap",
                }}
              >
                {restaurant.distance || "Chưa xác định"}
              </Typography>
            </Stack>

            <Chip
              size="small"
              icon={<StarRoundedIcon sx={{ color: "#F6B500 !important", fontSize: 15 }} />}
              label={getRatingLabel(restaurant)}
              sx={{
                height: 28,
                bgcolor: "color-mix(in srgb, var(--app-primary) 10%, white)",
                color: "var(--app-primary)",
                flexShrink: 0,
                "& .MuiChip-label": {
                  px: 1,
                  fontSize: "0.78rem",
                },
              }}
            />
          </Stack>

          <Chip
            size="small"
            label={`Gợi ý ${index + 1}`}
            sx={{
              alignSelf: "flex-start",
              height: 26,
              bgcolor: "color-mix(in srgb, var(--app-secondary) 12%, white)",
              color: "var(--app-secondary)",
              fontWeight: 800,
            }}
          />
        </Stack>
      </Stack>
    </Box>
  );
}

function AgentActionButtons({ message, onQuickAction }) {
  const status = message.agent?.status;
  if (!status) return null;

  const buttonSx = {
    minHeight: 34,
    px: 1.4,
    py: 0.55,
    fontSize: "0.78rem",
    boxShadow: "none",
    backgroundImage: "none",
    bgcolor: "rgba(255,255,255,0.92)",
    color: "var(--app-primary)",
    border: "1px solid color-mix(in srgb, var(--app-primary) 20%, white)",
    "&:hover": {
      backgroundImage: "none",
      bgcolor: "rgba(255,255,255,1)",
    },
  };

  const actionsByStatus = {
    restaurant_selected: [
      { label: "Đặt quán này", prompt: "đặt quán này cho 4 người lúc 19h" },
      { label: "Chọn quán khác", prompt: "quán khác đi" },
    ],
    needs_restaurant: [
      { label: "Chọn quán 1", prompt: "đặt quán thứ 1" },
      { label: "Chọn quán 2", prompt: "đặt quán thứ 2" },
    ],
    needs_booking_info: [
      { label: "4 người lúc 19h", prompt: "4 người lúc 19h" },
      { label: "Đổi quán", prompt: "quán khác đi" },
    ],
    awaiting_booking_confirmation: [
      { label: "Xác nhận đặt", prompt: "ok đặt đi" },
      { label: "Đổi thành 6 người", prompt: "đổi thành 6 người" },
      { label: "Hủy", prompt: "thôi không đặt nữa" },
    ],
    booking_created: [
      { label: "Xem lịch sử đặt bàn", to: "/lich-su-dat-ban" },
      { label: "Gợi ý tiếp", prompt: "gợi ý quán khác gần đây" },
    ],
    booking_rejected: [
      { label: "Đổi giờ 20h", prompt: "đổi sang 20h" },
      { label: "Chọn quán khác", prompt: "quán khác đi" },
    ],
    needs_login: [
      { label: "Đăng nhập", to: "/dang-nhap" },
      { label: "Hủy", prompt: "thôi không đặt nữa" },
    ],
  };

  const actions = actionsByStatus[status] || [];

  return (
    <Stack spacing={1}>
      <Stack direction="row" spacing={0.8} alignItems="center" flexWrap="wrap">
        <Chip
          size="small"
          color={getAgentStatusColor(status)}
          label={getAgentStatusLabel(status)}
          sx={{ fontWeight: 800 }}
        />
      </Stack>

      {actions.length ? (
        <Stack direction="row" spacing={0.8} flexWrap="wrap" useFlexGap>
          {actions.map((action) => (
            <CustomButton
              key={action.label}
              component={action.to ? RouterLink : "button"}
              to={action.to}
              type="button"
              onClick={action.prompt ? () => onQuickAction(action.prompt) : undefined}
              sx={buttonSx}
            >
              {action.label}
            </CustomButton>
          ))}
        </Stack>
      ) : null}
    </Stack>
  );
}

function MessageBubble({ message, onQuickAction }) {
  const isAssistant = message.role === "assistant";

  return (
    <Stack
      direction="row"
      spacing={1.5}
      justifyContent={isAssistant ? "flex-start" : "flex-end"}
      alignItems="center"
    >
      {isAssistant ? (
        <Avatar sx={{ bgcolor: "#050505", width: 42, height: 42, flexShrink: 0 }}>
          <AppLogoImage size={32} />
        </Avatar>
      ) : null}

      <Box
        sx={{
          width: "100%",
          maxWidth: { xs: "100%", md: "86%" },
          px: 2,
          py: 1.6,
          borderRadius: 3,
          bgcolor: isAssistant ? "rgba(255,255,255,0.95)" : "var(--app-primary)",
          color: isAssistant ? "var(--app-text-primary)" : "white",
          border: isAssistant ? "1px solid rgba(15,23,42,0.08)" : "none",
          boxShadow: isAssistant ? "0 18px 36px rgba(15,23,42,0.06)" : "0 18px 36px rgba(15,23,42,0.12)",
        }}
      >
        <Stack spacing={1.2}>
          <Typography sx={{ whiteSpace: "pre-wrap", lineHeight: 1.65 }}>{message.text}</Typography>
          {isAssistant ? <AgentActionButtons message={message} onQuickAction={onQuickAction} /> : null}
          {message.booking?.reservation_id ? (
            <Alert severity="success">
              Booking #{String(message.booking.reservation_id).slice(0, 8)} đang ở trạng thái {message.booking.status}.
            </Alert>
          ) : null}
          {message.isFallback ? <Alert severity="warning">{fallbackMessage}</Alert> : null}
          {message.isEmpty ? <Alert severity="info">{noResultMessage}</Alert> : null}
        </Stack>
      </Box>

      {!isAssistant ? (
        <Avatar
          sx={{
            bgcolor: "color-mix(in srgb, var(--app-secondary) 22%, white)",
            color: "var(--app-secondary)",
            width: 38,
            height: 38,
            flexShrink: 0,
          }}
        >
          U
        </Avatar>
      ) : null}
    </Stack>
  );
}

function AiRecommendationPage() {
  const { user } = useAuth();
  const [sessionId, setSessionId] = useState(() => getStoredChat()?.sessionId || createSessionId());
  const [prompt, setPrompt] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState(() => getStoredChat()?.messages || createInitialMessages());
  const [userLocation, setUserLocation] = useState(null);
  const [locationStatus, setLocationStatus] = useState("checking");

  useEffect(() => {
    window.sessionStorage.setItem(
      AI_CHAT_STORAGE_KEY,
      JSON.stringify({
        sessionId,
        messages,
      })
    );
  }, [messages, sessionId]);

  useEffect(() => {
    if (!navigator.geolocation) {
      setLocationStatus("unavailable");
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setUserLocation({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        });
        setLocationStatus("ready");
      },
      () => setLocationStatus("denied"),
      {
        enableHighAccuracy: true,
        maximumAge: 5 * 60 * 1000,
        timeout: 7000,
      }
    );
  }, []);

  const latestRecommendationMessage = [...messages]
    .reverse()
    .find((message) => message.role === "assistant" && (message.restaurants?.length || message.isEmpty || message.isFallback));

  const recommendedRestaurants = latestRecommendationMessage?.restaurants || [];

  const handleNewChat = () => {
    setSessionId(createSessionId());
    setPrompt("");
    setError("");
    setLoading(false);
    setMessages(createInitialMessages("Phiên chat mới đã sẵn sàng. Bạn đang muốn tìm trải nghiệm ăn uống như thế nào?"));
  };

  const sendPrompt = async (rawPrompt) => {
    const nextError = validatePrompt(rawPrompt);
    setError(nextError);
    if (nextError) return;

    const userPrompt = rawPrompt.trim();
    setMessages((current) => [...current, createUserMessage(userPrompt)]);
    setPrompt("");
    setLoading(true);

    try {
      const data = await aiService.recommend({
        prompt: userPrompt,
        query: userPrompt,
        customer_id: user?.id ?? null,
        session_id: sessionId,
        latitude: userLocation?.latitude,
        longitude: userLocation?.longitude,
      });

      const restaurants = Array.isArray(data.restaurants)
        ? data.restaurants.map((restaurant) => {
            const normalized = normalizeRestaurant(restaurant);
            return {
              ...normalized,
              aiReason: restaurant.reason || restaurant.aiReason || getRecommendationReason(normalized, userPrompt),
            };
          })
        : [];

      setMessages((current) => [
        ...current,
        createAssistantMessage({
          text: buildAssistantReply({
            source: data.source,
            message: data.message,
            restaurants,
          }),
          restaurants,
          isFallback: data.source === "FALLBACK",
          isEmpty: restaurants.length === 0,
          agent: data.agent,
          booking: data.booking,
        }),
      ]);
    } catch (requestError) {
      try {
        const restaurants = await restaurantService.getRestaurants();
        const fallbackResult = buildFallbackRecommendation(userPrompt, restaurants);

        setMessages((current) => [
          ...current,
          createAssistantMessage({
            text: buildRecommendationReply(
              fallbackResult.restaurants.length
                ? "Mình vẫn tìm được một vài lựa chọn gần với nội dung bạn nhập."
                : noResultMessage,
              fallbackResult.restaurants
            ),
            restaurants: fallbackResult.restaurants,
            isFallback: true,
            isEmpty: fallbackResult.isEmpty,
          }),
        ]);
      } catch {
        setMessages((current) => [
          ...current,
          createAssistantMessage({
            text: `Mình chưa gọi được backend recommend. Bạn kiểm tra backend có đang chạy ở http://localhost:8000 không nhé.\n\nChi tiết lỗi: ${requestError.message || "Không rõ lỗi"}`,
            restaurants: [],
            isFallback: true,
            isEmpty: true,
          }),
        ]);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    await sendPrompt(prompt);
  };

  const handleQuickAction = async (quickPrompt) => {
    if (loading) return;
    await sendPrompt(quickPrompt);
  };

  return (
    <Box sx={{ pb: { xs: 2, lg: 8 } }}>
      <Grid container spacing={3} alignItems="start">
        <Grid size={{ xs: 12, lg: 8 }}>
          <CustomCard
            sx={{
              display: "flex",
              flexDirection: "column",
              background: "linear-gradient(180deg, rgba(255,255,255,0.96) 0%, rgba(247,249,255,0.98) 100%)",
            }}
          >
            <Stack spacing={2.2}>
              <Box
                sx={{
                  p: { xs: 1.2, md: 1.6 },
                  borderRadius: 3,
                  overflowY: "auto",
                  bgcolor: "rgba(244,247,255,0.95)",
                  border: "1px solid rgba(15,23,42,0.08)",
                  minHeight: { xs: 220, lg: 320 },
                  maxHeight: { xs: 360, lg: 380 },
                }}
              >
                <Stack spacing={2}>
                  {messages.map((message) => (
                    <MessageBubble key={message.id} message={message} onQuickAction={handleQuickAction} />
                  ))}

                  {loading ? (
                    <Stack direction="row" spacing={1.5} alignItems="center">
                      <Avatar sx={{ bgcolor: "#050505", width: 42, height: 42, flexShrink: 0 }}>
                        <AppLogoImage size={32} />
                      </Avatar>
                      <Box
                        sx={{
                          px: 2,
                          py: 1.5,
                          borderRadius: 3,
                          bgcolor: "rgba(255,255,255,0.95)",
                          border: "1px solid rgba(15,23,42,0.08)",
                        }}
                      >
                        <Stack direction="row" spacing={1.25} alignItems="center">
                          <CircularProgress size={18} />
                          <Typography color="text.secondary">AI Assistant đang xử lý yêu cầu của bạn...</Typography>
                        </Stack>
                      </Box>
                    </Stack>
                  ) : null}
                </Stack>
              </Box>

              <Stack component="form" spacing={1.4} onSubmit={handleSubmit}>
                {error ? <Alert severity="error">{error}</Alert> : null}
                <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                  <Chip
                    size="small"
                    icon={<LocationOnRoundedIcon />}
                    color={locationStatus === "ready" ? "success" : "default"}
                    label={
                      locationStatus === "ready"
                        ? "Đang dùng vị trí hiện tại để lọc bán kính"
                        : locationStatus === "checking"
                          ? "Đang xin quyền vị trí..."
                          : "Chưa có vị trí, kết quả không lọc theo bán kính"
                    }
                  />
                </Stack>

                <Box
                  sx={{
                    position: "relative",
                    width: "100%",
                    maxWidth: { xs: "100%", lg: 860 },
                  }}
                >
                  <FormInput
                    multiline
                    minRows={1}
                    maxRows={2}
                    label="Tin nhắn"
                    placeholder="Ví dụ: Gợi ý nhà hàng ấm cúng cho buổi hẹn hò gần Quận 1."
                    value={prompt}
                    disabled={loading}
                    onChange={(event) => setPrompt(event.target.value)}
                    sx={{
                      "& .MuiOutlinedInput-root": {
                        pr: { xs: 18, sm: 20 },
                        pb: 1,
                        minHeight: 78,
                        alignItems: "center",
                      },
                    }}
                  />

                  <CustomButton
                    type="submit"
                    disabled={loading}
                    endIcon={<SendRoundedIcon />}
                    sx={{
                      position: "absolute",
                      right: 18,
                      top: "50%",
                      transform: "translateY(-50%)",
                      minWidth: "auto",
                      px: 2.2,
                      zIndex: 1,
                    }}
                  >
                    Send
                  </CustomButton>
                </Box>

                <Stack direction="row" justifyContent="flex-end">
                  <CustomButton
                    variant="outlined"
                    startIcon={<AddCommentRoundedIcon />}
                    onClick={handleNewChat}
                    sx={{
                      boxShadow: "none",
                      color: "var(--app-primary)",
                      bgcolor: "rgba(255,255,255,0.9)",
                      backgroundImage: "none",
                      border: "1px solid color-mix(in srgb, var(--app-primary) 22%, white)",
                      "&:hover": {
                        backgroundImage: "none",
                        bgcolor: "rgba(255,255,255,1)",
                      },
                    }}
                  >
                    New Chat
                  </CustomButton>
                </Stack>
              </Stack>
            </Stack>
          </CustomCard>
        </Grid>

        <Grid size={{ xs: 12, lg: 4 }}>
          <CustomCard sx={{ display: "flex", flexDirection: "column" }}>
            <Stack spacing={2}>
              <Stack direction="row" spacing={1} alignItems="center">
                <RestaurantRoundedIcon sx={{ color: "var(--app-primary)" }} />
                <Typography variant="h4">Quán được gợi ý</Typography>
              </Stack>

              <Box
                sx={{
                  overflowY: "auto",
                  pr: 0.5,
                  minHeight: { xs: 220, lg: 320 },
                  maxHeight: { xs: "none", lg: 620 },
                }}
              >
                {latestRecommendationMessage?.isFallback ? (
                  <Alert severity="warning" sx={{ mb: 2 }}>
                    {fallbackMessage}
                  </Alert>
                ) : null}

                {recommendedRestaurants.length ? (
                  <Stack spacing={2}>
                    {recommendedRestaurants.map((restaurant, index) => (
                      <RecommendationListCard
                        key={restaurant.id || `${restaurant.name}-${index}`}
                        restaurant={restaurant}
                        index={index}
                      />
                    ))}
                  </Stack>
                ) : (
                  <Box
                    sx={{
                      minHeight: { xs: 220, lg: 0 },
                      height: "100%",
                      display: "grid",
                      placeItems: "center",
                      borderRadius: 3,
                      border: "1px dashed rgba(140, 177, 255, 0.45)",
                      px: 3,
                      py: 4,
                    }}
                  >
                    <Stack spacing={1.2} alignItems="center" sx={{ maxWidth: 320, textAlign: "center" }}>
                      <Typography variant="h4">Chưa có gợi ý nhà hàng</Typography>
                      <Typography color="text.secondary">
                        {latestRecommendationMessage?.isEmpty
                          ? noResultMessage
                          : "Hãy gửi một yêu cầu ở khung chat để xem danh sách nhà hàng được đề xuất."}
                      </Typography>
                    </Stack>
                  </Box>
                )}
              </Box>
            </Stack>
          </CustomCard>
        </Grid>
      </Grid>
    </Box>
  );
}

export default AiRecommendationPage;
