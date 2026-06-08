import { redirect } from "next/navigation";

// 루트 진입은 항상 보호된 영역으로 보낸다. (app) 레이아웃이 인증을 검증해
// 미인증 시 /login으로 다시 리다이렉트한다.
export default function Home(): never {
  redirect("/jds");
}
