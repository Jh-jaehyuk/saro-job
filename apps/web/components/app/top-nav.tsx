"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { useLogoutMutation, useMe } from "@/lib/queries/auth";

export function TopNav() {
  const me = useMe();
  const router = useRouter();
  const logout = useLogoutMutation();

  const onLogout = async () => {
    try {
      await logout.mutateAsync();
      router.push("/login");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "로그아웃에 실패했습니다.");
    }
  };

  return (
    <header className="border-border flex items-center justify-between border-b px-6 py-3">
      <Link href="/jds" className="text-foreground text-sm font-semibold">
        saro-job
      </Link>
      <div className="text-muted-foreground flex items-center gap-3 text-sm">
        {me.data && <span>{me.data.email}</span>}
        <Button variant="outline" size="sm" onClick={onLogout} disabled={logout.isPending}>
          로그아웃
        </Button>
      </div>
    </header>
  );
}
