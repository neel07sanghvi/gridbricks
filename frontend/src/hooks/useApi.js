import { useState, useEffect, useCallback } from "react";

export function useApi(fetchFn, ...args) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const key = JSON.stringify(args);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchFn(...args);
      setData(result);
    } catch (err) {
      setError(err.message || "Failed to fetch data");
    } finally {
      setLoading(false);
    }
  }, [fetchFn, key]);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { data, loading, error, refetch };
}
