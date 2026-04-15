import {
  CloudConfigDeleteResponse,
  CloudConfigRegisterPayload,
  CloudConfigRegisterResponse,
  CloudProcessResponse,
  CloudProcessSingleResponse,
  CloudUploadResponse,
  HealthResponse,
  ProcessInboxResponse,
  ProcessSingleResponse,
  TenantCloudFilePayload,
  TenantCloudFilesPayload,
} from "@/types/api";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/+$/, "") ?? "http://127.0.0.1:5000";

async function parseJson<T>(response: Response): Promise<T> {
  const payload = (await response.json()) as { error?: string };
  if (!response.ok) {
    throw new Error(payload.error ?? `Request failed with status ${response.status}`);
  }
  return payload as T;
}

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`);
  return parseJson<HealthResponse>(response);
}

export async function processInbox(): Promise<ProcessInboxResponse> {
  const response = await fetch(`${API_BASE_URL}/process`, { method: "POST" });
  return parseJson<ProcessInboxResponse>(response);
}

export async function processSingle(filename: string): Promise<ProcessSingleResponse> {
  const safe = encodeURIComponent(filename.trim());
  const response = await fetch(`${API_BASE_URL}/process/${safe}`, { method: "POST" });
  return parseJson<ProcessSingleResponse>(response);
}

export async function processCloudInbox(): Promise<CloudProcessResponse> {
  const response = await fetch(`${API_BASE_URL}/cloud/process`, { method: "POST" });
  return parseJson<CloudProcessResponse>(response);
}

export async function processCloudOne(fileIdOrName: string): Promise<CloudProcessSingleResponse> {
  const safe = encodeURIComponent(fileIdOrName.trim());
  const response = await fetch(`${API_BASE_URL}/cloud/process/${safe}`, { method: "POST" });
  return parseJson<CloudProcessSingleResponse>(response);
}

export async function uploadCloudFiles(files: File[]): Promise<CloudUploadResponse> {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));
  const response = await fetch(`${API_BASE_URL}/cloud/upload`, {
    method: "POST",
    body: formData,
  });
  return parseJson<CloudUploadResponse>(response);
}

export async function registerCloudConfig(
  payload: CloudConfigRegisterPayload
): Promise<CloudConfigRegisterResponse> {
  const formData = new FormData();
  formData.append("service_account", payload.serviceAccountFile);
  if (payload.clientSecretFile) formData.append("client_secret", payload.clientSecretFile);
  if (payload.driveCredentialsFile) formData.append("drive_credentials", payload.driveCredentialsFile);
  if (payload.sheetsCredentialsFile) formData.append("sheets_credentials", payload.sheetsCredentialsFile);
  formData.append("gdrive_inbox_folder_id", payload.gdriveInboxFolderId);
  formData.append("gdrive_root_folder_id", payload.gdriveRootFolderId);
  formData.append("gsheets_spreadsheet_id", payload.gsheetsSpreadsheetId);
  if (payload.gsheetsSheetName?.trim()) formData.append("gsheets_sheet_name", payload.gsheetsSheetName.trim());
  if (payload.gdriveShareWithEmails?.trim()) {
    formData.append("gdrive_share_with_emails", payload.gdriveShareWithEmails.trim());
  }
  const response = await fetch(`${API_BASE_URL}/cloud/config/register`, {
    method: "POST",
    body: formData,
  });
  return parseJson<CloudConfigRegisterResponse>(response);
}

export async function deleteCloudConfig(configId: string): Promise<CloudConfigDeleteResponse> {
  const response = await fetch(`${API_BASE_URL}/cloud/config/${encodeURIComponent(configId.trim())}`, {
    method: "DELETE",
  });
  return parseJson<CloudConfigDeleteResponse>(response);
}

export async function processTenantCloudInbox(configId: string): Promise<CloudProcessResponse> {
  const safe = encodeURIComponent(configId.trim());
  const response = await fetch(`${API_BASE_URL}/cloud/tenant/process?config_id=${safe}`, { method: "POST" });
  return parseJson<CloudProcessResponse>(response);
}

export async function processTenantCloudOne(
  payload: TenantCloudFilePayload
): Promise<CloudProcessSingleResponse> {
  const safeName = encodeURIComponent(payload.fileIdOrName.trim());
  const safeCfg = encodeURIComponent(payload.configId.trim());
  const response = await fetch(`${API_BASE_URL}/cloud/tenant/process/${safeName}?config_id=${safeCfg}`, {
    method: "POST",
  });
  return parseJson<CloudProcessSingleResponse>(response);
}

export async function uploadTenantCloudFiles(
  payload: TenantCloudFilesPayload
): Promise<CloudUploadResponse> {
  const formData = new FormData();
  payload.files.forEach((file) => formData.append("files", file));
  const safeCfg = encodeURIComponent(payload.configId.trim());
  const response = await fetch(`${API_BASE_URL}/cloud/tenant/upload?config_id=${safeCfg}`, {
    method: "POST",
    body: formData,
  });
  return parseJson<CloudUploadResponse>(response);
}
