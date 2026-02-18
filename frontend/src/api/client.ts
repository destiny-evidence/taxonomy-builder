import { API_BASE } from "../config";
import { getToken } from "./auth";
import { clearAuth } from "../state/auth";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  skipAuth?: boolean;
  isFormData?: boolean;
}

async function request<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { method = "GET", body, skipAuth = false, isFormData = false } = options;

  const headers: Record<string, string> = {};

  // Don't set Content-Type for FormData - browser sets it with boundary
  if (!isFormData) {
    headers["Content-Type"] = "application/json";
  }

  // Add Authorization header with token from Keycloak
  if (!skipAuth) {
    const token = await getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    method,
    headers,
    body: isFormData ? (body as FormData) : body ? JSON.stringify(body) : undefined,
  });

  // Handle 401 Unauthorized
  if (response.status === 401) {
    clearAuth();
    throw new ApiError(401, "Session expired. Please log in again.");
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new ApiError(
      response.status,
      error.detail || `Request failed: ${response.status}`
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

export const api = {
  get: <T>(endpoint: string) => request<T>(endpoint),
  post: <T>(endpoint: string, body: unknown) =>
    request<T>(endpoint, { method: "POST", body }),
  postForm: <T>(endpoint: string, formData: FormData) =>
    request<T>(endpoint, { method: "POST", body: formData, isFormData: true }),
  put: <T>(endpoint: string, body: unknown) =>
    request<T>(endpoint, { method: "PUT", body }),
  patch: <T>(endpoint: string, body: unknown) =>
    request<T>(endpoint, { method: "PATCH", body }),
  delete: (endpoint: string) => request<void>(endpoint, { method: "DELETE" }),
};
