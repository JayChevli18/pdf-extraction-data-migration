"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import {
  getHealth,
  processCloudInbox,
  processCloudOne,
  processInbox,
  processSingle,
  uploadCloudFiles,
} from "@/lib/api-client";
import { DashboardHeader } from "@/components/dashboard/header";
import { ApiLoadingOverlay } from "@/components/dashboard/loading-overlay";
import { ResultPanel } from "@/components/dashboard/result-panel";
import {
  CloudProcessingSection,
  CloudUploadSection,
  LocalProcessingSection,
} from "@/components/dashboard/sections";
import { Message } from "@/components/dashboard/types";

export function DashboardContent() {
  const health = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    refetchInterval: 15000,
  });

  const localBatch = useMutation({ mutationFn: processInbox });
  const localOne = useMutation({ mutationFn: processSingle });
  const cloudBatch = useMutation({ mutationFn: processCloudInbox });
  const cloudOne = useMutation({ mutationFn: processCloudOne });
  const cloudUpload = useMutation({ mutationFn: uploadCloudFiles });
  const isAnyApiLoading =
    localBatch.isPending ||
    localOne.isPending ||
    cloudBatch.isPending ||
    cloudOne.isPending ||
    cloudUpload.isPending;

  const activeActionLabel = cloudBatch.isPending
    ? "Running cloud pipeline"
    : cloudUpload.isPending
    ? "Uploading files to cloud inbox"
    : cloudOne.isPending
    ? "Processing single cloud file"
    : localBatch.isPending
    ? "Running local pipeline"
    : localOne.isPending
    ? "Processing single local file"
    : "Processing request";

  const messages: Message[] = [];
  if (cloudUpload.data) {
    messages.push({
      title: "Cloud upload complete",
      body: `Uploaded ${cloudUpload.data.uploaded} file(s) to cloud inbox.`,
    });
  }
  if (cloudBatch.data) {
    messages.push({
      title: "Cloud pipeline complete",
      body: `Processed ${cloudBatch.data.processed} file(s) from cloud inbox.`,
    });
  }
  if (cloudOne.data) {
    messages.push({
      title: "Cloud single-file complete",
      body: `${cloudOne.data.name} processed. Drive link: ${cloudOne.data.drive_link}`,
    });
  }
  if (localBatch.data) {
    messages.push({
      title: "Local pipeline complete",
      body: `Processed ${localBatch.data.processed} local file(s).`,
    });
  }
  if (localOne.data) {
    messages.push({
      title: "Local single-file complete",
      body: `Record ${localOne.data.id} generated for ${localOne.data.name}.`,
    });
  }

  return (
    <>
      {isAnyApiLoading ? (
        <ApiLoadingOverlay actionLabel={activeActionLabel} />
      ) : null}
      <main className="mx-auto flex w-full max-w-7xl flex-1 flex-col gap-6 bg-gradient-to-b from-blue-50 via-white to-slate-100 px-4 py-8 text-slate-900 md:px-8">
        <DashboardHeader status={health.data?.status} hasError={Boolean(health.error)} />

        <div className="grid gap-6 lg:grid-cols-[1.3fr_0.9fr]">
          <div className="space-y-6">
            <CloudUploadSection onUpload={(files) => cloudUpload.mutate(files)} />
            <CloudProcessingSection
              isCloudBatchPending={cloudBatch.isPending}
              onCloudBatch={() => cloudBatch.mutate()}
              onCloudOne={(value) => cloudOne.mutate(value)}
            />
            <LocalProcessingSection
              isLocalBatchPending={localBatch.isPending}
              onLocalBatch={() => localBatch.mutate()}
              onLocalOne={(value) => localOne.mutate(value)}
            />
          </div>

          <ResultPanel messages={messages} />
        </div>
      </main>
    </>
  );
}
