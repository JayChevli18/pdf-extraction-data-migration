type ApiLoadingOverlayProps = {
  actionLabel: string;
};

export function ApiLoadingOverlay({ actionLabel }: ApiLoadingOverlayProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 backdrop-blur-sm">
      <div className="w-[92%] max-w-md rounded-2xl border border-blue-200 bg-white p-6 shadow-2xl">
        <div className="flex flex-col items-center gap-4 text-center">
          <div className="relative">
            <div className="h-16 w-16 rounded-full border-4 border-blue-100" />
            <div className="absolute inset-0 h-16 w-16 animate-spin rounded-full border-4 border-transparent border-t-blue-600 border-r-blue-400" />
          </div>
          <h3 className="text-lg font-semibold text-slate-900">{actionLabel}</h3>
          <p className="text-sm text-slate-600">
            Extractly AI is working on your request. This may take a few minutes, so please keep
            this page open.
          </p>
          <div className="flex items-center gap-1">
            <span className="h-2 w-2 animate-bounce rounded-full bg-blue-600 [animation-delay:-0.3s]" />
            <span className="h-2 w-2 animate-bounce rounded-full bg-blue-500 [animation-delay:-0.15s]" />
            <span className="h-2 w-2 animate-bounce rounded-full bg-blue-400" />
          </div>
        </div>
      </div>
    </div>
  );
}
