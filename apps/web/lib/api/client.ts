/**
 * 백엔드 API fetch wrapper.
 *
 * - same-origin `/api/*` 경로 사용 → Next.js rewrites가 `NEXT_PUBLIC_API_BASE_URL`로
 *   프록시한다. 쿠키는 자동 전송(`credentials: "include"`).
 * - 백엔드의 `AppError` envelope `{error:{code,message}}`를 `ApiError`로 정규화.
 */

export class ApiError extends Error {
  readonly code: string;
  readonly status: number;

  constructor(code: string, message: string, status: number) {
    super(message);
    this.code = code;
    this.status = status;
  }
}

type FetchInit = Omit<RequestInit, "body"> & {
  body?: BodyInit | object;
};

function isPlainObject(value: unknown): value is Record<string, unknown> {
  if (value === null || typeof value !== "object") return false;
  if (value instanceof FormData) return false;
  if (value instanceof URLSearchParams) return false;
  if (value instanceof Blob) return false;
  if (value instanceof ArrayBuffer) return false;
  if (value instanceof ReadableStream) return false;
  return true;
}

export async function apiFetch<T>(
  path: string,
  init: FetchInit = {},
): Promise<T> {
  const { body, headers, ...rest } = init;
  const isJsonBody = body !== undefined && isPlainObject(body);

  const response = await fetch(`/api${path}`, {
    ...rest,
    credentials: "include",
    headers: {
      Accept: "application/json",
      ...(isJsonBody ? { "Content-Type": "application/json" } : {}),
      ...headers,
    },
    body: isJsonBody
      ? JSON.stringify(body)
      : (body as BodyInit | undefined),
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const code =
      (data?.error?.code as string | undefined) ??
      (typeof data?.detail === "string" ? data.detail : "INTERNAL_ERROR");
    const message =
      (data?.error?.message as string | undefined) ??
      (typeof data?.detail === "string" ? data.detail : "요청을 처리하지 못했습니다.");
    throw new ApiError(code, message, response.status);
  }

  return data as T;
}
