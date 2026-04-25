export const storageKeys = {
  token: "smartfood_token",
  user: "smartfood_user",
};

export const getStoredToken = () => localStorage.getItem(storageKeys.token);

export const setStoredAuth = ({ token, user }) => {
  localStorage.setItem(storageKeys.token, token);
  localStorage.setItem(storageKeys.user, JSON.stringify(user));
};

export const clearStoredAuth = () => {
  localStorage.removeItem(storageKeys.token);
  localStorage.removeItem(storageKeys.user);
};

export const getStoredUser = () => {
  const rawUser = localStorage.getItem(storageKeys.user);
  return rawUser ? JSON.parse(rawUser) : null;
};
