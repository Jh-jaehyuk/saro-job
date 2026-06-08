import type { NextConfig } from "next";

const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  // Docker 멀티스테이지 빌드에서 .next/standalone 출력만 복사해 슬림 이미지 생성.
  output: "standalone",

  // `/api/*`를 백엔드로 프록시 — same-origin을 유지해 쿠키 자동 전송, CORS 회피.
  async rewrites() {
    return [
      { source: "/api/:path*", destination: `${apiBaseUrl}/:path*` },
    ];
  },
};

export default nextConfig;
