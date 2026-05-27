import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Docker 멀티스테이지 빌드에서 .next/standalone 출력만 복사해 슬림 이미지 생성.
  output: "standalone",
};

export default nextConfig;
