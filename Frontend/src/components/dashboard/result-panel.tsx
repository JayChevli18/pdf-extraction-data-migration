import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Message } from "@/components/dashboard/types";

type ResultPanelProps = {
  messages: Message[];
};

export function ResultPanel({ messages }: ResultPanelProps) {
  return (
    <Card className="h-fit border-slate-300 bg-white shadow-sm">
      <CardHeader>
        <CardTitle className="text-slate-900">Live Activity</CardTitle>
        <CardDescription>Results from all triggered API actions in Extractly AI</CardDescription>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[580px] pr-4">
          <div className="space-y-3">
            {messages.length === 0 ? (
              <p className="text-sm text-slate-500">No actions yet. Run a section to see results.</p>
            ) : (
              messages.map((msg, index) => (
                <Alert key={`${msg.title}-${index}`} className="border-blue-100 bg-blue-50/60">
                  <AlertTitle className="text-slate-900">{msg.title}</AlertTitle>
                  <AlertDescription className="text-slate-700">{msg.body}</AlertDescription>
                </Alert>
              ))
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
