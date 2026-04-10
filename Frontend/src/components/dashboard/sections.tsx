import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { SingleCloudForm, SingleLocalForm, UploadForm } from "@/components/dashboard/forms";

type CloudSectionProps = {
  isCloudBatchPending: boolean;
  onCloudBatch: () => void;
  onCloudOne: (value: string) => void;
};

type LocalSectionProps = {
  isLocalBatchPending: boolean;
  onLocalBatch: () => void;
  onLocalOne: (value: string) => void;
};

export function CloudUploadSection({ onUpload }: { onUpload: (files: File[]) => void }) {
  return (
    <Card className="border-blue-200 bg-white shadow-sm">
      <CardHeader>
        <CardTitle className="text-blue-700">1) Upload to Cloud Inbox</CardTitle>
        <CardDescription>Upload files first. Then run pipeline for all cloud inbox files.</CardDescription>
      </CardHeader>
      <CardContent>
        <UploadForm onSubmit={onUpload} />
      </CardContent>
    </Card>
  );
}

export function CloudProcessingSection({
  isCloudBatchPending,
  onCloudBatch,
  onCloudOne,
}: CloudSectionProps) {
  return (
    <Card className="border-blue-200 bg-white shadow-sm">
      <CardHeader>
        <CardTitle className="text-slate-900">2) Cloud Processing</CardTitle>
        <CardDescription>Full pipeline and single file processing for cloud storage APIs.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        <Alert className="border-blue-200 bg-blue-50">
          <AlertTitle className="text-blue-700">Run full cloud pipeline</AlertTitle>
          <AlertDescription className="text-slate-700">
            Click this to process every PDF/DOCX currently present in cloud inbox.
          </AlertDescription>
        </Alert>
        <Button
          className="bg-blue-600 text-white hover:bg-blue-700"
          onClick={onCloudBatch}
          disabled={isCloudBatchPending}
        >
          {isCloudBatchPending ? "Processing cloud inbox..." : "Run Cloud Pipeline"}
        </Button>
        <Separator />
        <SingleCloudForm onSubmit={onCloudOne} />
      </CardContent>
    </Card>
  );
}

export function LocalProcessingSection({
  isLocalBatchPending,
  onLocalBatch,
  onLocalOne,
}: LocalSectionProps) {
  return (
    <Card className="border-slate-200 bg-white shadow-sm">
      <CardHeader>
        <CardTitle className="text-slate-900">3) Local Storage Section</CardTitle>
        <CardDescription>
          Separate local-only controls for `/process` and `/process/&lt;filename&gt;`.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        <Alert className="border-slate-300 bg-slate-100">
          <AlertTitle className="text-slate-800">Local batch message</AlertTitle>
          <AlertDescription className="text-slate-700">
            Clicking local pipeline will process all supported files in local inbox.
          </AlertDescription>
        </Alert>
        <Button
          className="bg-slate-900 text-white hover:bg-slate-800"
          onClick={onLocalBatch}
          disabled={isLocalBatchPending}
        >
          {isLocalBatchPending ? "Processing local inbox..." : "Run Local Pipeline"}
        </Button>
        <Separator />
        <SingleLocalForm onSubmit={onLocalOne} />
      </CardContent>
    </Card>
  );
}
