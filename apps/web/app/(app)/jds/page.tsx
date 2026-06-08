import { CreateJdDialog } from "@/components/jds/create-jd-dialog";
import { JdList } from "@/components/jds/jd-list";

export default function JdsPage() {
  return (
    <section className="flex flex-1 flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-foreground text-2xl font-semibold tracking-tight">
          채용 공고
        </h1>
        <CreateJdDialog />
      </div>
      <JdList />
    </section>
  );
}
