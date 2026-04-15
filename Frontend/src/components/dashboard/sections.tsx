import type { ReactNode } from "react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import {
  CloudConfigRegisterForm,
  SingleCloudForm,
  SingleLocalForm,
  TenantConfigIdForm,
  UploadForm,
} from "@/components/dashboard/forms";
import { CloudConfigRegisterPayload } from "@/types/api";

type SectionCardProps = {
  className: string;
  title: string;
  description: string;
  children?: ReactNode;
};

const SectionCard = ({ className, title, description, children }: SectionCardProps) => {
  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="text-slate-900">{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      {children ? <CardContent>{children}</CardContent> : null}
    </Card>
  );
};

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

type TenantCloudSectionProps = {
  currentConfigId?: string;
  isTenantCloudBatchPending: boolean;
  onConfigRegister: (payload: CloudConfigRegisterPayload) => void;
  onConfigSelect: (configId: string) => void;
  onTenantCloudUpload: (files: File[]) => void;
  onTenantCloudBatch: () => void;
  onTenantCloudOne: (value: string) => void;
};

export const CloudUploadSection = ({ onUpload }: { onUpload: (files: File[]) => void }) => {
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
};

export const CloudProcessingSection = ({
  isCloudBatchPending,
  onCloudBatch,
  onCloudOne,
}: CloudSectionProps) => {
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
};

export const LocalProcessingSection = ({
  isLocalBatchPending,
  onLocalBatch,
  onLocalOne,
}: LocalSectionProps) => {
  return (
    <SectionCard
      className="border-slate-200 bg-white shadow-sm"
      title="3) Local Storage Section"
      description="Separate local-only controls for `/process` and `/process/<filename>`."
    >
      <div className="space-y-5">
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
      </div>
    </SectionCard>
  );
};

export const TenantCloudSection = ({
  currentConfigId,
  isTenantCloudBatchPending,
  onConfigRegister,
  onConfigSelect,
  onTenantCloudUpload,
  onTenantCloudBatch,
  onTenantCloudOne,
}: TenantCloudSectionProps) => {
  return (
    <div className="space-y-5">
      <Card className="border-indigo-200 bg-white shadow-sm">
        <CardHeader>
          <CardTitle className="text-indigo-700">2) Tenant Cloud APIs</CardTitle>
          <CardDescription>
            Register user credentials once, keep the generated `config_id`, and call `/cloud/tenant/*`.
          </CardDescription>
        </CardHeader>
      </Card>

      <SectionCard
        className="border-indigo-200 bg-white shadow-sm"
        title="2.1 Register Tenant Credentials"
        description="Create a tenant config and get a `config_id` from backend."
      >
        <div className="space-y-4">
          <Alert className="border-indigo-200 bg-indigo-50">
            <AlertTitle className="text-indigo-700">Step A</AlertTitle>
            <AlertDescription className="text-slate-700">
              Upload service account/client secret and folder/spreadsheet IDs.
            </AlertDescription>
          </Alert>
          <CloudConfigRegisterForm onSubmit={onConfigRegister} />
        </div>
      </SectionCard>

      <SectionCard
        className="border-indigo-200 bg-white shadow-sm"
        title="2.2 Select Tenant Config"
        description="Use the generated `config_id` for all tenant actions below."
      >
        <div className="space-y-4">
          <TenantConfigIdForm initialConfigId={currentConfigId} onSubmit={onConfigSelect} />
        </div>
      </SectionCard>

      <SectionCard
        className="border-indigo-200 bg-white shadow-sm"
        title="2.3 Tenant Upload"
        description="Upload PDF/DOCX files into the tenant inbox folder."
      >
        <div>
          <UploadForm onSubmit={onTenantCloudUpload} />
        </div>
      </SectionCard>

      <SectionCard
        className="border-indigo-200 bg-white shadow-sm"
        title="2.4 Tenant Processing"
        description="Run full tenant pipeline or process one file by id/name."
      >
        <div className="space-y-5">
          <Button
            className="bg-indigo-600 text-white hover:bg-indigo-700"
            onClick={onTenantCloudBatch}
            disabled={isTenantCloudBatchPending || !currentConfigId}
          >
            {isTenantCloudBatchPending ? "Processing tenant cloud inbox..." : "Run Tenant Cloud Pipeline"}
          </Button>
          <Separator />
          <SingleCloudForm onSubmit={onTenantCloudOne} />
        </div>
      </SectionCard>
    </div>
  );
};
