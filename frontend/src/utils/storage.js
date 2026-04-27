export const storageKeys = {
  token: "smartfood_token",
  user: "smartfood_user",
};

const clearLegacyLocalStorage = () => {
  localStorage.removeItem(storageKeys.token);
  localStorage.removeItem(storageKeys.user);
};

export const setStoredAuth = ({ token, user }) => {
  sessionStorage.setItem(storageKeys.token, token);
  sessionStorage.setItem(storageKeys.user, JSON.stringify(user));
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
  return rawUser ? JSON.parse(rawUser) : null;
};
