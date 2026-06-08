import { apiFetch } from "./client";
import type { components } from "@/lib/api-types";

export type UserRead = components["schemas"]["UserRead"];

export interface Credentials {
  email: string;
  password: string;
}

export async function register(credentials: Credentials): Promise<UserRead> {
  return apiFetch<UserRead>("/auth/register", {
    method: "POST",
    body: credentials,
  });
}

export async function login(credentials: Credentials): Promise<void> {
  // fastapi-users는 form-urlencoded(`username`/`password`)를 받고 204를 돌려준다.
  const body = new URLSearchParams({
    username: credentials.email,
    password: credentials.password,
  });
  await apiFetch<void>("/auth/cookie/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
}

export async function logout(): Promise<void> {
  await apiFetch<void>("/auth/cookie/logout", { method: "POST" });
}

export async function getMe(): Promise<UserRead> {
  return apiFetch<UserRead>("/users/me");
}
