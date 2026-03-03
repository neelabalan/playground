import useAuth from "./useAuth";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8080";

export const useFetchPrivate = () => {
  const { auth } = useAuth();

  return async ({
    method = "GET",
    endpoint,
    headers = {},
    body = null,
    timeout = 10000,
  }) => {
    const options = {
      method,
      headers: {
        "Content-Type": "application/json",
        ...(auth?.accessToken && {
          Authorization: `Bearer ${auth.accessToken}`,
        }),
        ...headers,
      },
      ...(body && { body: JSON.stringify(body) }),
    };

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    let response;
    let data;

    try {
      response = await fetch(BASE_URL + endpoint, {
        ...options,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      const isJson = response.headers
        .get("content-type")
        ?.includes("application/json");
      data = isJson ? await response.json() : null;

      if (!response.ok) {
        return {
          status: response.status,
          message: "API error",
          data,
        };
      }

      return {
        status: response.status,
        data,
      };
    } catch (error) {
      clearTimeout(timeoutId);
      if (error.name === "AbortError") {
        return {
          status: 408,
          message: "Request timeout",
        };
      }
      return {
        status: 500,
        message: "Network error",
        error: error.message,
      };
    }
  };
};

export default useFetchPrivate;
