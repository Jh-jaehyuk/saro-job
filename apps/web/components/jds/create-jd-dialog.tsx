"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useCreateJdMutation } from "@/lib/queries/jds";

const schema = z.object({
  title: z.string().min(1, "공고 제목을 입력해 주세요."),
  raw_text: z.string().min(10, "요구사항 본문을 최소 10자 이상 입력해 주세요."),
});

type FormValues = z.infer<typeof schema>;

export function CreateJdDialog() {
  const [open, setOpen] = useState(false);
  const mutation = useCreateJdMutation();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { title: "", raw_text: "" },
  });

  const onSubmit = handleSubmit(async (values) => {
    try {
      await mutation.mutateAsync(values);
      toast.success("새 공고를 만들었습니다.");
      reset();
      setOpen(false);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "공고 생성에 실패했습니다.");
    }
  });

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <Button onClick={() => setOpen(true)}>새 공고</Button>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>새 채용 공고</DialogTitle>
          <DialogDescription>
            제목과 요구사항을 입력하면 이후 이력서 매칭의 기준이 됩니다.
          </DialogDescription>
        </DialogHeader>
        <form className="space-y-4" onSubmit={onSubmit} noValidate>
          <div className="space-y-1.5">
            <Label htmlFor="title">제목</Label>
            <Input id="title" {...register("title")} />
            {errors.title && (
              <p className="text-destructive text-sm">{errors.title.message}</p>
            )}
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="raw_text">요구사항 / 본문</Label>
            <textarea
              id="raw_text"
              rows={8}
              className="border-input bg-background focus-visible:ring-ring w-full rounded-md border px-3 py-2 text-sm focus-visible:ring-2 focus-visible:outline-none"
              {...register("raw_text")}
            />
            {errors.raw_text && (
              <p className="text-destructive text-sm">{errors.raw_text.message}</p>
            )}
          </div>
          <DialogFooter>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "생성 중…" : "공고 만들기"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
