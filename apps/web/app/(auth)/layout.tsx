export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <main className="flex flex-1 items-center justify-center p-6">
      <div className="flex w-full flex-col items-center gap-6">
        <span className="text-foreground text-lg font-semibold tracking-tight">
          saro-job
        </span>
        {children}
      </div>
    </main>
  );
}
