export type HealthResponse = {
  status: string;
};

export type ProcessInboxResponse = {
  queued: string[];
  processed: number;
  ids: string[];
};

export type ProcessSingleResponse = {
  id: string;
  name: string;
};

export type CloudProcessResponse = {
  processed: number;
  ids: string[];
};

export type CloudProcessSingleResponse = {
  id: string;
  name: string;
  drive_link: string;
};

export type CloudUploadItem = {
  id: string;
  name: string;
};

export type CloudUploadResponse = {
  uploaded: number;
  files: CloudUploadItem[];
};

export type ApiErrorShape = {
  error?: string;
};
