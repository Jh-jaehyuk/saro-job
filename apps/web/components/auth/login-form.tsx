"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useLoginMutation } from "@/lib/queries/auth";

const schema = z.object({
  email: z.string().email("이메일 형식이 올바르지 않습니다."),
  password: z.string().min(8, "비밀번호는 최소 8자 이상이어야 합니다."),
});

type FormValues = z.infer<typeof schema>;

const googleEnabled =
  process.env.NEXT_PUBLIC_GOOGLE_OAUTH_ENABLED === "true";

export function LoginForm() {
  const router = useRouter();
  const mutation = useLoginMutation();
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { email: "", password: "" },
  });

  const onSubmit = handleSubmit(async (values) => {
    try {
      await mutation.mutateAsync(values);
      router.push("/jds");
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "로그인에 실패했습니다.";
      toast.error(message);
    }
  });

  return (
    <form className="space-y-4" onSubmit={onSubmit} noValidate>
      <div className="space-y-1.5">
        <Label htmlFor="email">이메일</Label>
        <Input id="email" type="email" autoComplete="email" {...register("email")} />
        {errors.email && (
          <p className="text-destructive text-sm">{errors.email.message}</p>
        )}
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="password">비밀번호</Label>
        <Input
          id="password"
          type="password"
          autoComplete="current-password"
          {...register("password")}
        />
        {errors.password && (
          <p className="text-destructive text-sm">{errors.password.message}</p>
        )}
      </div>
      <Button type="submit" className="w-full" disabled={isSubmitting}>
        {isSubmitting ? "로그인 중…" : "로그인"}
      </Button>
      {googleEnabled && (
        <a
          className="text-muted-foreground block text-center text-sm underline"
          href="/api/auth/google/authorize"
        >
          Google로 계속하기
        </a>
      )}
    </form>
  );
}
