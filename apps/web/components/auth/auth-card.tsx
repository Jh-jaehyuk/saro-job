import Link from "next/link";

import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

interface AuthCardProps {
  title: string;
  description: string;
  footer: { prompt: string; href: string; ctaText: string };
  children: React.ReactNode;
}

export function AuthCard({ title, description, footer, children }: AuthCardProps) {
  return (
    <Card className="w-full max-w-sm">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>{children}</CardContent>
      <CardFooter className="text-muted-foreground flex justify-center text-sm">
        {footer.prompt}{" "}
        <Link className="ml-1 underline" href={footer.href}>
          {footer.ctaText}
        </Link>
      </CardFooter>
    </Card>
  );
}
