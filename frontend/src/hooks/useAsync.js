import { useCallback, useState } from "react";

export const useAsync = (asyncFunction) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const execute = useCallback(
    async (...args) => {
      try {
        setLoading(true);
        setError("");
        return await asyncFunction(...args);
      } catch (err) {
        setError(err.message || "Đã xảy ra lỗi");
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [asyncFunction]
  );

  return { execute, loading, error, setError };
};
