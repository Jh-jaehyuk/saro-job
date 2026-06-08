"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ApiError } from "@/lib/api/client";
import {
  type Credentials,
  type UserRead,
  getMe,
  login,
  logout,
  register,
} from "@/lib/api/auth";

export const ME_QUERY_KEY = ["auth", "me"] as const;

export function useMe() {
  return useQuery<UserRead, ApiError>({
    queryKey: ME_QUERY_KEY,
    queryFn: getMe,
    retry: false,
    staleTime: 30_000,
  });
}

export function useRegisterMutation() {
  return useMutation<UserRead, ApiError, Credentials>({
    mutationFn: register,
  });
}

export function useLoginMutation() {
  const qc = useQueryClient();
  return useMutation<void, ApiError, Credentials>({
    mutationFn: login,
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ME_QUERY_KEY });
    },
  });
}

export function useLogoutMutation() {
  const qc = useQueryClient();
  return useMutation<void, ApiError, void>({
    mutationFn: logout,
    onSuccess: () => {
      qc.clear();
    },
  });
}
