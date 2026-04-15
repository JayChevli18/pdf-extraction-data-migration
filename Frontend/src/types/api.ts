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

export type CloudConfigRegisterResponse = {
  config_id: string;
};

export type CloudConfigDeleteResponse = {
  deleted: boolean;
};

export type TenantCloudFilePayload = {
  fileIdOrName: string;
  configId: string;
};

export type TenantCloudFilesPayload = {
  files: File[];
  configId: string;
};

export type CloudConfigRegisterPayload = {
  serviceAccountFile: File;
  clientSecretFile?: File;
  driveCredentialsFile?: File;
  sheetsCredentialsFile?: File;
  gdriveInboxFolderId: string;
  gdriveRootFolderId: string;
  gsheetsSpreadsheetId: string;
  gsheetsSheetName?: string;
  gdriveShareWithEmails?: string;
};

export type ApiErrorShape = {
  error?: string;
};
