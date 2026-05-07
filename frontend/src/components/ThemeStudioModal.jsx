import AutoAwesomeRoundedIcon from "@mui/icons-material/AutoAwesomeRounded";
import RestartAltRoundedIcon from "@mui/icons-material/RestartAltRounded";
import {
  Box,
  Chip,
  Divider,
  MenuItem,
  Slider,
  Stack,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from "@mui/material";
import { useThemePreferences } from "../hooks/useThemePreferences";
import CustomButton from "./CustomButton";
import CustomCard from "./CustomCard";
import CustomModal from "./CustomModal";
import FormInput from "./FormInput";

function ThemeStudioModal({ open, onClose }) {
  const { preferences, themePresets, setPreset, setRadius, setDensity, resetPreferences } =
    useThemePreferences();

  return (
    <CustomModal open={open} onClose={onClose} title="Giao diện" width={560}>
      <Stack spacing={2.4}>
        <Typography color="text.secondary" sx={{ fontSize: "0.96rem" }}>
          Tùy biến màu sắc, độ bo góc và nhịp thở giao diện để trải nghiệm nhìn có gu hơn.
        </Typography>

        <Stack spacing={1.1}>
          <Typography variant="h4">Bảng màu</Typography>
          <FormInput
            select
            value={preferences.presetId}
            onChange={(event) => setPreset(event.target.value)}
          >
            {themePresets.map((preset) => (
              <MenuItem key={preset.id} value={preset.id}>
                {preset.name}
              </MenuItem>
            ))}
          </FormInput>
          <Stack spacing={1.2}>
            {themePresets.map((preset) => {
              const isActive = preset.id === preferences.presetId;

              return (
                <CustomCard
                  key={preset.id}
                  onClick={() => setPreset(preset.id)}
                  sx={{
                    cursor: "pointer",
                    border: isActive
                      ? `1px solid ${preset.colors.primary}`
                      : "1px solid rgba(15,23,42,0.08)",
                    boxShadow: isActive
                      ? `0 22px 42px ${preset.colors.surfaceGlowA}`
                      : "0 14px 28px rgba(15,23,42,0.06)",
                  }}
                  contentSx={{ p: 2.1, "&:last-child": { pb: 2.1 } }}
                >
                  <Stack spacing={1.1}>
                    <Stack direction="row" justifyContent="space-between" alignItems="center">
                      <Typography variant="h4">{preset.name}</Typography>
                      {isActive ? <Chip size="small" color="primary" label="Đang dùng" /> : null}
                    </Stack>
                    <Typography color="text.secondary" sx={{ fontSize: "0.92rem" }}>
                      {preset.description}
                    </Typography>
                    <Stack direction="row" spacing={0.9}>
                      {[
                        preset.colors.primary,
                        preset.colors.secondary,
                        preset.colors.success,
                        preset.colors.paper,
                      ].map((color) => (
                        <Box
                          key={color}
                          sx={{
                            width: 30,
                            height: 30,
                            borderRadius: 999,
                            bgcolor: color,
                            border: "1px solid rgba(15,23,42,0.08)",
                          }}
                        />
                      ))}
                    </Stack>
                  </Stack>
                </CustomCard>
              );
            })}
          </Stack>
        </Stack>

        <Divider />

        <Stack spacing={1.1}>
          <Typography variant="h4">Độ bo góc</Typography>
          <Slider
            value={preferences.radius}
            min={8}
            max={22}
            step={2}
            marks={[
              { value: 8, label: "Gọn" },
              { value: 14, label: "Cân" },
              { value: 22, label: "Mềm" },
            ]}
            onChange={(_, value) => setRadius(value)}
            color="primary"
          />
        </Stack>

        <Stack spacing={1.1}>
          <Typography variant="h4">Nhịp giao diện</Typography>
          <ToggleButtonGroup
            exclusive
            fullWidth
            value={preferences.density}
            onChange={(_, value) => {
              if (value) setDensity(value);
            }}
            color="primary"
          >
            <ToggleButton value="compact">Gọn</ToggleButton>
            <ToggleButton value="cozy">Cân bằng</ToggleButton>
            <ToggleButton value="airy">Thoáng</ToggleButton>
          </ToggleButtonGroup>
        </Stack>

        <Box
          sx={{
            borderRadius: 2.5,
            p: 2,
            background:
              "linear-gradient(135deg, rgba(255,138,42,0.12) 0%, rgba(74,144,226,0.10) 100%)",
            border: "1px solid rgba(255,255,255,0.7)",
          }}
        >
          <Stack direction="row" spacing={1.2} alignItems="center">
            <AutoAwesomeRoundedIcon color="primary" />
            <Box>
              <Typography fontWeight={800}>Xem trước đang áp dụng trực tiếp</Typography>
              <Typography color="text.secondary" sx={{ fontSize: "0.9rem" }}>
                Mỗi thay đổi sẽ phản ánh ngay lên toàn bộ ứng dụng để bạn so màu dễ hơn.
              </Typography>
            </Box>
          </Stack>
        </Box>

        <Stack direction="row" spacing={1.2} justifyContent="space-between">
          <CustomButton
            type="button"
            startIcon={<RestartAltRoundedIcon />}
            onClick={resetPreferences}
            sx={{ background: "linear-gradient(135deg, #64748B 0%, #94A3B8 100%)" }}
          >
            Đặt lại mặc định
          </CustomButton>
          <CustomButton type="button" onClick={onClose}>
            Xong
          </CustomButton>
        </Stack>
      </Stack>
    </CustomModal>
  );
}

export default ThemeStudioModal;
