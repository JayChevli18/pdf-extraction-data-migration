import { Badge } from "@/components/ui/badge";

type DashboardHeaderProps = {
  status?: string;
  hasError: boolean;
};

export function DashboardHeader({ status, hasError }: DashboardHeaderProps) {
  return (
    <section className="rounded-2xl border border-blue-100 bg-white p-6 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="space-y-2">
          <h1 className="text-3xl font-semibold tracking-tight">Extractly AI Dashboard</h1>
          <p className="max-w-2xl text-sm text-slate-600">
            One clean workspace for cloud and local profile processing with clear actions and
            feedback.
          </p>
        </div>
        <Badge className="bg-blue-600 text-white hover:bg-blue-600" variant={status === "ok" ? "default" : "secondary"}>
          Backend: {status ?? "checking"}
        </Badge>
      </div>
      {hasError ? (
        <p className="mt-3 text-sm text-red-600">
          Cannot reach backend service. Verify Flask server and frontend API base URL.
        </p>
      ) : null}
    </section>
  );
}
