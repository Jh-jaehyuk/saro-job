import { AuthCard } from "@/components/auth/auth-card";
import { LoginForm } from "@/components/auth/login-form";

export default function LoginPage() {
  return (
    <AuthCard
      title="로그인"
      description="채용 담당자 계정으로 들어오세요."
      footer={{ prompt: "계정이 없으신가요?", href: "/register", ctaText: "가입하기" }}
    >
      <LoginForm />
    </AuthCard>
  );
}
