import { useState } from "react";

export const useLocalStorage = (key, initialValue) => {
  const [storedValue, setStoredValue] = useState(() => {
    const item = localStorage.getItem(key);
    return item ? JSON.parse(item) : initialValue;
  });

  const setValue = (value) => {
    const nextValue = value instanceof Function ? value(storedValue) : value;
    setStoredValue(nextValue);
    localStorage.setItem(key, JSON.stringify(nextValue));
  };

  return [storedValue, setValue];
};
