"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { TopNav } from "@/components/app/top-nav";
import { useMe } from "@/lib/queries/auth";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const me = useMe();
  const router = useRouter();

  useEffect(() => {
    if (me.error && me.error.status === 401) {
      router.replace("/login");
    }
  }, [me.error, router]);

  if (me.isLoading) {
    return (
      <main className="text-muted-foreground flex flex-1 items-center justify-center text-sm">
        불러오는 중…
      </main>
    );
  }

  if (!me.data) {
    return null;
  }

  return (
    <div className="flex flex-1 flex-col">
      <TopNav />
      <main className="flex flex-1 flex-col p-6">{children}</main>
    </div>
  );
}
