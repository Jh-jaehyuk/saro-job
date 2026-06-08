import { AuthCard } from "@/components/auth/auth-card";
import { RegisterForm } from "@/components/auth/register-form";

export default function RegisterPage() {
  return (
    <AuthCard
      title="가입"
      description="가입 직후 1인 워크스페이스가 자동 생성됩니다."
      footer={{ prompt: "이미 계정이 있으신가요?", href: "/login", ctaText: "로그인" }}
    >
      <RegisterForm />
    </AuthCard>
  );
}
