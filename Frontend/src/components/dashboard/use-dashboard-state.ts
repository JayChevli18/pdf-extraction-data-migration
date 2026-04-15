"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  deleteCloudConfig,
  getHealth,
  processCloudInbox,
  processCloudOne,
  processInbox,
  processSingle,
  processTenantCloudInbox,
  processTenantCloudOne,
  registerCloudConfig,
  uploadCloudFiles,
  uploadTenantCloudFiles,
} from "@/lib/api-client";
import type { Message } from "@/components/dashboard/types";
import type { CloudConfigRegisterPayload } from "@/types/api";

const buildMessages = (params: {
  cloudUploadData?: { uploaded: number };
  tenantCloudUploadData?: { uploaded: number };
  cloudBatchData?: { processed: number };
  tenantCloudBatchData?: { processed: number };
  cloudOneData?: { name: string; drive_link: string };
  tenantCloudOneData?: { name: string; drive_link: string };
  localBatchData?: { processed: number };
  localOneData?: { id: string; name: string };
  cloudConfigRegisterData?: { config_id: string };
  cloudConfigDeleteData?: { deleted: boolean };
  errors: Error[];
}): Message[] => {
  const messages: Message[] = [];

  if (params.cloudUploadData) {
    messages.push({
      title: "Cloud upload complete",
      body: `Uploaded ${params.cloudUploadData.uploaded} file(s) to cloud inbox.`,
    });
  }
  if (params.tenantCloudUploadData) {
    messages.push({
      title: "Tenant cloud upload complete",
      body: `Uploaded ${params.tenantCloudUploadData.uploaded} file(s) to tenant cloud inbox.`,
    });
  }
  if (params.cloudBatchData) {
    messages.push({
      title: "Cloud pipeline complete",
      body: `Processed ${params.cloudBatchData.processed} file(s) from cloud inbox.`,
    });
  }
  if (params.tenantCloudBatchData) {
    messages.push({
      title: "Tenant cloud pipeline complete",
      body: `Processed ${params.tenantCloudBatchData.processed} file(s) from tenant cloud inbox.`,
    });
  }
  if (params.cloudOneData) {
    messages.push({
      title: "Cloud single-file complete",
      body: `${params.cloudOneData.name} processed. Drive link: ${params.cloudOneData.drive_link}`,
    });
  }
  if (params.tenantCloudOneData) {
    messages.push({
      title: "Tenant cloud single-file complete",
      body: `${params.tenantCloudOneData.name} processed. Drive link: ${params.tenantCloudOneData.drive_link}`,
    });
  }
  if (params.localBatchData) {
    messages.push({
      title: "Local pipeline complete",
      body: `Processed ${params.localBatchData.processed} local file(s).`,
    });
  }
  if (params.localOneData) {
    messages.push({
      title: "Local single-file complete",
      body: `Record ${params.localOneData.id} generated for ${params.localOneData.name}.`,
    });
  }
  if (params.cloudConfigRegisterData) {
    messages.push({
      title: "Tenant config created",
      body: `Saved config_id: ${params.cloudConfigRegisterData.config_id}`,
    });
  }
  if (params.cloudConfigDeleteData?.deleted) {
    messages.push({
      title: "Tenant config deleted",
      body: "Deleted selected tenant config.",
    });
  }

  params.errors.forEach((err) => {
    messages.push({
      title: "API error",
      body: err.message,
    });
  });

  return messages;
};

export const useDashboardState = () => {
  const [tenantConfigId, setTenantConfigId] = useState("");

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
  const cloudConfigRegister = useMutation({ mutationFn: registerCloudConfig });
  const tenantCloudBatch = useMutation({ mutationFn: processTenantCloudInbox });
  const tenantCloudOne = useMutation({ mutationFn: processTenantCloudOne });
  const tenantCloudUpload = useMutation({ mutationFn: uploadTenantCloudFiles });
  const cloudConfigDelete = useMutation({ mutationFn: deleteCloudConfig });

  const isAnyApiLoading =
    localBatch.isPending ||
    localOne.isPending ||
    cloudBatch.isPending ||
    cloudOne.isPending ||
    cloudUpload.isPending ||
    tenantCloudBatch.isPending ||
    tenantCloudOne.isPending ||
    tenantCloudUpload.isPending ||
    cloudConfigRegister.isPending ||
    cloudConfigDelete.isPending;

  const activeActionLabel = cloudBatch.isPending
    ? "Running cloud pipeline"
    : tenantCloudBatch.isPending
    ? "Running tenant cloud pipeline"
    : cloudUpload.isPending
    ? "Uploading files to cloud inbox"
    : tenantCloudUpload.isPending
    ? "Uploading files to tenant cloud inbox"
    : cloudConfigRegister.isPending
    ? "Registering tenant cloud config"
    : cloudConfigDelete.isPending
    ? "Deleting tenant cloud config"
    : cloudOne.isPending
    ? "Processing single cloud file"
    : tenantCloudOne.isPending
    ? "Processing single tenant cloud file"
    : localBatch.isPending
    ? "Running local pipeline"
    : localOne.isPending
    ? "Processing single local file"
    : "Processing request";

  const errors = useMemo(
    () =>
      [
        cloudUpload.error,
        cloudBatch.error,
        cloudOne.error,
        localBatch.error,
        localOne.error,
        tenantCloudBatch.error,
        tenantCloudOne.error,
        tenantCloudUpload.error,
        cloudConfigRegister.error,
        cloudConfigDelete.error,
      ].filter(Boolean) as Error[],
    [
      cloudBatch.error,
      cloudConfigDelete.error,
      cloudConfigRegister.error,
      cloudOne.error,
      cloudUpload.error,
      localBatch.error,
      localOne.error,
      tenantCloudBatch.error,
      tenantCloudOne.error,
      tenantCloudUpload.error,
    ]
  );

  const messages = useMemo(
    () =>
      buildMessages({
        cloudUploadData: cloudUpload.data,
        tenantCloudUploadData: tenantCloudUpload.data,
        cloudBatchData: cloudBatch.data,
        tenantCloudBatchData: tenantCloudBatch.data,
        cloudOneData: cloudOne.data,
        tenantCloudOneData: tenantCloudOne.data,
        localBatchData: localBatch.data,
        localOneData: localOne.data,
        cloudConfigRegisterData: cloudConfigRegister.data,
        cloudConfigDeleteData: cloudConfigDelete.data,
        errors,
      }),
    [
      cloudBatch.data,
      cloudConfigDelete.data,
      cloudConfigRegister.data,
      cloudOne.data,
      cloudUpload.data,
      errors,
      localBatch.data,
      localOne.data,
      tenantCloudBatch.data,
      tenantCloudOne.data,
      tenantCloudUpload.data,
    ]
  );

  const handleRegisterConfig = (payload: CloudConfigRegisterPayload) => {
    cloudConfigRegister.mutate(payload, {
      onSuccess: (data) => setTenantConfigId(data.config_id),
    });
  };

  const handleTenantUpload = (files: File[]) => {
    if (!tenantConfigId.trim()) {
      return;
    }
    tenantCloudUpload.mutate({ files, configId: tenantConfigId });
  };

  return {
    healthStatus: health.data?.status,
    healthError: Boolean(health.error),
    isAnyApiLoading,
    activeActionLabel,
    messages,
    tenantConfigId,
    setTenantConfigId,
    cloudBatchPending: cloudBatch.isPending,
    localBatchPending: localBatch.isPending,
    tenantCloudBatchPending: tenantCloudBatch.isPending,
    runCloudUpload: (files: File[]) => cloudUpload.mutate(files),
    runCloudBatch: () => cloudBatch.mutate(),
    runCloudOne: (value: string) => cloudOne.mutate(value),
    runLocalBatch: () => localBatch.mutate(),
    runLocalOne: (value: string) => localOne.mutate(value),
    handleRegisterConfig,
    handleTenantUpload,
    runTenantCloudBatch: () => tenantCloudBatch.mutate(tenantConfigId),
    runTenantCloudOne: (value: string) =>
      tenantCloudOne.mutate({ fileIdOrName: value, configId: tenantConfigId }),
  };
};
