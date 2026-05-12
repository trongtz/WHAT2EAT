export const storageKeys = {
  token: "smartfood_token",
  user: "smartfood_user",
};

export const GUEST_AUTH_TOKEN = "guest-session";

const roleMap = {
  customer: "customer",
  owner: "owner",
  admin: "admin",
  guest: "guest",
  CUSTOMER: "customer",
  OWNER: "owner",
  ADMIN: "admin",
  GUEST: "guest",
};

const clearLegacyLocalStorage = () => {
  localStorage.removeItem(storageKeys.token);
  localStorage.removeItem(storageKeys.user);
};

export const normalizeUserRole = (role) => {
  if (typeof role !== "string") return role;
  return roleMap[role] || role.toLowerCase();
};

export const normalizeStoredUser = (user) => {
  if (!user) return null;
  return {
    ...user,
    id: user.id ?? user.user_id,
    fullName: user.fullName ?? user.full_name ?? "",
    avatarUrl: user.avatarUrl ?? user.avatar_url ?? null,
    role: normalizeUserRole(user.role),
  };
};

export const setStoredAuth = ({ token, user }) => {
  const normalizedUser = normalizeStoredUser(user);
  sessionStorage.setItem(storageKeys.token, token);
  sessionStorage.setItem(storageKeys.user, JSON.stringify(normalizedUser));
};

export const clearStoredAuth = () => {
  sessionStorage.removeItem(storageKeys.token);
  sessionStorage.removeItem(storageKeys.user);
  clearLegacyLocalStorage();
};

export const getStoredToken = () => {
  clearLegacyLocalStorage();
  return sessionStorage.getItem(storageKeys.token);
};

export const getStoredUser = () => {
  clearLegacyLocalStorage();
  const rawUser = sessionStorage.getItem(storageKeys.user);
  return rawUser ? normalizeStoredUser(JSON.parse(rawUser)) : null;
};

export const isGuestToken = (token) => token === GUEST_AUTH_TOKEN;
