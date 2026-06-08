import { apiFetch } from "./client";
import type { components } from "@/lib/api-types";

export type JobDescriptionRead = components["schemas"]["JobDescriptionRead"];
export type JobDescriptionCreate = components["schemas"]["JobDescriptionCreate"];

export async function listJds(): Promise<JobDescriptionRead[]> {
  return apiFetch<JobDescriptionRead[]>("/jds");
}

export async function getJd(jdId: string): Promise<JobDescriptionRead> {
  return apiFetch<JobDescriptionRead>(`/jds/${jdId}`);
}

export async function createJd(
  data: JobDescriptionCreate,
): Promise<JobDescriptionRead> {
  return apiFetch<JobDescriptionRead>("/jds", {
    method: "POST",
    body: data,
  });
}
