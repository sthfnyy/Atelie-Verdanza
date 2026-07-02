const API_BASE_URL = "/api";
let csrfToken = null;

function isUnsafeMethod(method) {
  return ["POST", "PUT", "PATCH", "DELETE"].includes(method.toUpperCase());
}

async function getCsrfToken() {
  if (csrfToken) {
    return csrfToken;
  }

  const response = await fetch(`${API_BASE_URL}/auth/csrf`, {
    credentials: "include"
  });

  const data = await response.json();

  csrfToken = data.csrfToken;

  return csrfToken;
}

async function apiRequest(endpoint, options = {}) {
  const method = options.method || "GET";

  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {})
  };

  if (isUnsafeMethod(method)) {
    const token = await getCsrfToken();
    headers["X-CSRF-Token"] = token;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    credentials: "include",
    ...options,
    method,
    headers
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(
      data?.detail ||
      data?.message ||
      "Erro na requisição."
    );
  }

  return data;
}