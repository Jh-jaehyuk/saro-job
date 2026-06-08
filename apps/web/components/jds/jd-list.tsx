"use client";

import Link from "next/link";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useJds } from "@/lib/queries/jds";

export function JdList() {
  const { data, isLoading, error } = useJds();

  if (isLoading) {
    return <p className="text-muted-foreground text-sm">불러오는 중…</p>;
  }
  if (error) {
    return <p className="text-destructive text-sm">{error.message}</p>;
  }
  if (!data || data.length === 0) {
    return (
      <p className="text-muted-foreground text-sm">
        아직 등록된 공고가 없습니다. 새 공고를 만들어 시작하세요.
      </p>
    );
  }

  return (
    <ul className="grid gap-3 sm:grid-cols-2">
      {data.map((jd) => (
        <li key={jd.id}>
          <Link href={`/jds/${jd.id}`} className="block">
            <Card className="hover:bg-accent/40 transition-colors">
              <CardHeader>
                <CardTitle className="truncate">{jd.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground line-clamp-3 text-sm whitespace-pre-line">
                  {jd.raw_text}
                </p>
                <p className="text-muted-foreground/70 mt-3 text-xs">
                  {new Date(jd.created_at).toLocaleString("ko-KR")}
                </p>
              </CardContent>
            </Card>
          </Link>
        </li>
      ))}
    </ul>
  );
}
