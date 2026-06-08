"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ApiError } from "@/lib/api/client";
import {
  type JobDescriptionCreate,
  type JobDescriptionRead,
  createJd,
  getJd,
  listJds,
} from "@/lib/api/jds";

export const JD_LIST_KEY = ["jds"] as const;
export const jdDetailKey = (id: string) => ["jds", id] as const;

export function useJds() {
  return useQuery<JobDescriptionRead[], ApiError>({
    queryKey: JD_LIST_KEY,
    queryFn: listJds,
  });
}

export function useJd(id: string) {
  return useQuery<JobDescriptionRead, ApiError>({
    queryKey: jdDetailKey(id),
    queryFn: () => getJd(id),
    enabled: id.length > 0,
  });
}

export function useCreateJdMutation() {
  const qc = useQueryClient();
  return useMutation<JobDescriptionRead, ApiError, JobDescriptionCreate>({
    mutationFn: createJd,
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: JD_LIST_KEY });
    },
  });
}
