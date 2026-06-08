"use client";

import { use } from "react";
import Link from "next/link";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useJd } from "@/lib/queries/jds";

export default function JdDetailPage({
  params,
}: {
  params: Promise<{ jdId: string }>;
}) {
  const { jdId } = use(params);
  const { data, isLoading, error } = useJd(jdId);

  if (isLoading) {
    return <p className="text-muted-foreground text-sm">불러오는 중…</p>;
  }
  if (error) {
    return (
      <div className="space-y-4">
        <p className="text-destructive text-sm">{error.message}</p>
        <Link
          href="/jds"
          className="border-border text-foreground hover:bg-accent inline-flex h-8 items-center rounded-md border px-3 text-sm"
        >
          목록으로
        </Link>
      </div>
    );
  }
  if (!data) return null;

  return (
    <section className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <Link
          href="/jds"
          className="border-border text-foreground hover:bg-accent inline-flex h-8 items-center rounded-md border px-3 text-sm"
        >
          ← 목록
        </Link>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>{data.title}</CardTitle>
          <CardDescription>
            등록: {new Date(data.created_at).toLocaleString("ko-KR")}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-foreground text-sm whitespace-pre-line">
            {data.raw_text}
          </p>
        </CardContent>
      </Card>
    </section>
  );
}
