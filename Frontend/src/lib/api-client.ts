import {
  CloudProcessResponse,
  CloudProcessSingleResponse,
  CloudUploadResponse,
  HealthResponse,
  ProcessInboxResponse,
  ProcessSingleResponse,
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
