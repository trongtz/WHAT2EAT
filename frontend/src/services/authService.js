import apiClient from "./apiClient";

const normalizeAuthUser = (user) => {
  if (!user) return user;
  const status = typeof user.status === "string" ? user.status.toLowerCase() : user.status;

  return {
    ...user,
    id: user.id ?? user.user_id,
    fullName: user.fullName ?? user.full_name,
    avatarUrl: user.avatarUrl ?? user.avatar_url ?? null,
    status,
  };
};

const normalizeAuthResponse = (data) => {
  if (!data) return data;

  return {
    ...data,
    user: normalizeAuthUser(data.user),
  };
};

const toRegisterPayload = (payload) => ({
  full_name: payload.fullName?.trim(),
  email: payload.email?.trim(),
  password: payload.password,
  role: typeof payload.role === "string" ? payload.role.toUpperCase() : payload.role,
});

export const authService = {
  login: async (payload) => {
    const response = await apiClient.post("/auth/login", payload);
    return normalizeAuthResponse(response.data);
  },
  register: async (payload) => {
    const response = await apiClient.post("/auth/register", toRegisterPayload(payload));
    return normalizeAuthResponse(response.data);
  },
  updateProfile: async (payload) => {
    const response = await apiClient.put("/profile/me", {
      full_name: payload.fullName?.trim(),
      email: payload.email?.trim(),
      avatar_url: payload.avatarUrl ?? payload.avatar_url,
    });
    return normalizeAuthUser(response.data);
  },
};
