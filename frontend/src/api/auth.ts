import apiClient from "./client";

export async function login(username: string, password: string) {
  return apiClient.post("/auth/login", { username, password });
}

export async function register(params: {
  username: string;
  email: string;
  password: string;
  display_name?: string;
}) {
  return apiClient.post("/auth/register", params);
}

export async function refreshToken(refresh_token: string) {
  return apiClient.post("/auth/refresh", { refresh_token });
}

export async function getMe() {
  return apiClient.get("/auth/me");
}

export async function updateMe(data: { display_name?: string; email?: string }) {
  return apiClient.put("/users/me", data);
}
