import { Form, Formik } from "formik";
import * as Yup from "yup";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { CloudConfigRegisterPayload } from "@/types/api";

type SingleValueSubmitFormProps = {
  fieldName: string;
  label: string;
  placeholder: string;
  submitLabel: string;
  validationMessage: string;
  submitClassName: string;
  inputClassName: string;
  initialValue?: string;
  onSubmit: (value: string) => void;
};

const SingleValueSubmitForm = ({
  fieldName,
  label,
  placeholder,
  submitLabel,
  validationMessage,
  submitClassName,
  inputClassName,
  initialValue = "",
  onSubmit,
}: SingleValueSubmitFormProps) => {
  const schema = Yup.object({
    [fieldName]: Yup.string().trim().required(validationMessage),
  });

  return (
    <Formik
      enableReinitialize
      initialValues={{ [fieldName]: initialValue }}
      validationSchema={schema}
      onSubmit={(values, helpers) => {
        onSubmit((values[fieldName] as string).trim());
        helpers.setSubmitting(false);
      }}
    >
      {({ values, errors, touched, handleChange, isSubmitting }) => (
        <Form className="space-y-2">
          <Label htmlFor={fieldName} className="text-slate-700">
            {label}
          </Label>
          <div className="flex flex-col gap-2 sm:flex-row">
            <Input
              id={fieldName}
              name={fieldName}
              placeholder={placeholder}
              value={(values[fieldName] as string) ?? ""}
              onChange={handleChange}
              className={inputClassName}
            />
            <Button type="submit" disabled={isSubmitting} className={submitClassName}>
              {submitLabel}
            </Button>
          </div>
          {touched[fieldName] && errors[fieldName] ? (
            <p className="text-sm text-red-600">{errors[fieldName] as string}</p>
          ) : null}
        </Form>
      )}
    </Formik>
  );
};

type JsonFileInputProps = {
  id: string;
  label: string;
  required?: boolean;
  error?: string;
  onChange: (file: File | null) => void;
};

const JsonFileInput = ({ id, label, required = false, error, onChange }: JsonFileInputProps) => {
  return (
    <div className="space-y-1">
      <Label htmlFor={id}>
        {label}
        {required ? " *" : ""}
      </Label>
      <Input
        id={id}
        name={id}
        type="file"
        accept=".json"
        onChange={(e) => onChange(e.currentTarget.files?.[0] ?? null)}
      />
      {error ? <p className="text-sm text-red-600">{error}</p> : null}
    </div>
  );
};

export const SingleLocalForm = ({ onSubmit }: { onSubmit: (filename: string) => void }) => {
  return (
    <SingleValueSubmitForm
      fieldName="filename"
      label="Local single filename"
      placeholder="filename.pdf"
      submitLabel="Run Local File"
      validationMessage="Filename is required"
      submitClassName="bg-slate-900 text-white hover:bg-slate-800"
      inputClassName="border-slate-300 focus-visible:ring-slate-400"
      onSubmit={onSubmit}
    />
  );
};

export const SingleCloudForm = ({ onSubmit }: { onSubmit: (fileIdOrName: string) => void }) => {
  return (
    <SingleValueSubmitForm
      fieldName="fileIdOrName"
      label="Cloud single filename"
      placeholder="filename.pdf"
      submitLabel="Run Cloud File"
      validationMessage="Filename is required"
      submitClassName="bg-blue-600 text-white hover:bg-blue-700"
      inputClassName="border-blue-200 focus-visible:ring-blue-400"
      onSubmit={onSubmit}
    />
  );
};

export const UploadForm = ({ onSubmit }: { onSubmit: (files: File[]) => void }) => {
  return (
    <Formik
      initialValues={{ files: [] as File[] }}
      onSubmit={(values, helpers) => {
        onSubmit(values.files);
        helpers.setSubmitting(false);
      }}
    >
      {({ setFieldValue, isSubmitting, values }) => (
        <Form className="space-y-3">
          <Label htmlFor="files" className="text-slate-700">
            Select `.pdf` or `.docx` files
          </Label>
          <Input
            id="files"
            name="files"
            type="file"
            multiple
            accept=".pdf,.docx"
            className="border-blue-200 file:mr-4 file:rounded-md file:border-0 file:bg-blue-100 file:px-3 file:py-1 file:text-blue-700"
            onChange={(event) => {
              const fileList = event.currentTarget.files;
              setFieldValue("files", fileList ? Array.from(fileList) : []);
            }}
          />
          <p className="text-xs text-slate-500">
            After upload, use the Cloud Processing section to run all or single file pipeline.
          </p>
          <Button
            type="submit"
            disabled={isSubmitting || values.files.length === 0}
            className="bg-blue-600 text-white hover:bg-blue-700"
          >
            Upload to Cloud Inbox
          </Button>
        </Form>
      )}
    </Formik>
  );
};

const tenantConfigSchema = Yup.object({
  gdriveInboxFolderId: Yup.string().trim().required("Inbox folder id is required"),
  gdriveRootFolderId: Yup.string().trim().required("Root folder id is required"),
  gsheetsSpreadsheetId: Yup.string().trim().required("Spreadsheet id is required"),
  gsheetsSheetName: Yup.string().trim(),
  gdriveShareWithEmails: Yup.string().trim(),
});

type TenantRegisterFormValues = {
  serviceAccountFile: File | null;
  clientSecretFile: File | null;
  driveCredentialsFile: File | null;
  sheetsCredentialsFile: File | null;
  gdriveInboxFolderId: string;
  gdriveRootFolderId: string;
  gsheetsSpreadsheetId: string;
  gsheetsSheetName: string;
  gdriveShareWithEmails: string;
};

export const CloudConfigRegisterForm = ({
  onSubmit,
}: {
  onSubmit: (payload: CloudConfigRegisterPayload) => void;
}) => {
  return (
    <Formik<TenantRegisterFormValues>
      initialValues={{
        serviceAccountFile: null,
        clientSecretFile: null,
        driveCredentialsFile: null,
        sheetsCredentialsFile: null,
        gdriveInboxFolderId: "",
        gdriveRootFolderId: "",
        gsheetsSpreadsheetId: "",
        gsheetsSheetName: "Sheet1",
        gdriveShareWithEmails: "",
      }}
      validationSchema={tenantConfigSchema}
      onSubmit={(values, helpers) => {
        if (!values.serviceAccountFile) {
          helpers.setFieldError("serviceAccountFile", "service_account.json is required");
          helpers.setSubmitting(false);
          return;
        }
        onSubmit({
          serviceAccountFile: values.serviceAccountFile,
          clientSecretFile: values.clientSecretFile ?? undefined,
          driveCredentialsFile: values.driveCredentialsFile ?? undefined,
          sheetsCredentialsFile: values.sheetsCredentialsFile ?? undefined,
          gdriveInboxFolderId: values.gdriveInboxFolderId,
          gdriveRootFolderId: values.gdriveRootFolderId,
          gsheetsSpreadsheetId: values.gsheetsSpreadsheetId,
          gsheetsSheetName: values.gsheetsSheetName,
          gdriveShareWithEmails: values.gdriveShareWithEmails,
        });
        helpers.setSubmitting(false);
      }}
    >
      {({ values, errors, touched, handleChange, setFieldValue, isSubmitting }) => (
        <Form className="space-y-3">
          <div className="grid gap-3 md:grid-cols-2">
            <JsonFileInput
              id="serviceAccountFile"
              label="service_account.json"
              required
              error={errors.serviceAccountFile as string | undefined}
              onChange={(file) => setFieldValue("serviceAccountFile", file)}
            />
            <JsonFileInput
              id="clientSecretFile"
              label="client_secret.json (optional)"
              onChange={(file) => setFieldValue("clientSecretFile", file)}
            />
            <JsonFileInput
              id="driveCredentialsFile"
              label="drive_credentials.json (optional)"
              onChange={(file) => setFieldValue("driveCredentialsFile", file)}
            />
            <JsonFileInput
              id="sheetsCredentialsFile"
              label="sheets_credentials.json (optional)"
              onChange={(file) => setFieldValue("sheetsCredentialsFile", file)}
            />
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            <div className="space-y-1">
              <Label htmlFor="gdriveInboxFolderId">GDrive Inbox Folder ID *</Label>
              <Input id="gdriveInboxFolderId" name="gdriveInboxFolderId" value={values.gdriveInboxFolderId} onChange={handleChange} />
              {touched.gdriveInboxFolderId && errors.gdriveInboxFolderId ? (
                <p className="text-sm text-red-600">{errors.gdriveInboxFolderId}</p>
              ) : null}
            </div>
            <div className="space-y-1">
              <Label htmlFor="gdriveRootFolderId">GDrive Root Folder ID *</Label>
              <Input id="gdriveRootFolderId" name="gdriveRootFolderId" value={values.gdriveRootFolderId} onChange={handleChange} />
              {touched.gdriveRootFolderId && errors.gdriveRootFolderId ? (
                <p className="text-sm text-red-600">{errors.gdriveRootFolderId}</p>
              ) : null}
            </div>
            <div className="space-y-1">
              <Label htmlFor="gsheetsSpreadsheetId">Google Sheets Spreadsheet ID *</Label>
              <Input
                id="gsheetsSpreadsheetId"
                name="gsheetsSpreadsheetId"
                value={values.gsheetsSpreadsheetId}
                onChange={handleChange}
              />
              {touched.gsheetsSpreadsheetId && errors.gsheetsSpreadsheetId ? (
                <p className="text-sm text-red-600">{errors.gsheetsSpreadsheetId}</p>
              ) : null}
            </div>
            <div className="space-y-1">
              <Label htmlFor="gsheetsSheetName">Sheet Name</Label>
              <Input id="gsheetsSheetName" name="gsheetsSheetName" value={values.gsheetsSheetName} onChange={handleChange} />
            </div>
          </div>

          <div className="space-y-1">
            <Label htmlFor="gdriveShareWithEmails">Share with emails (comma-separated)</Label>
            <Textarea
              id="gdriveShareWithEmails"
              name="gdriveShareWithEmails"
              value={values.gdriveShareWithEmails}
              onChange={handleChange}
              placeholder="user1@example.com,user2@example.com"
            />
          </div>

          <Button type="submit" disabled={isSubmitting} className="bg-indigo-600 text-white hover:bg-indigo-700">
            Register Tenant Config
          </Button>
        </Form>
      )}
    </Formik>
  );
};

export const TenantConfigIdForm = ({
  initialConfigId,
  onSubmit,
}: {
  initialConfigId?: string;
  onSubmit: (configId: string) => void;
}) => {
  return (
    <SingleValueSubmitForm
      fieldName="configId"
      label="Tenant Config ID"
      placeholder="uuid from /cloud/config/register"
      submitLabel="Set Config"
      validationMessage="Config id is required"
      submitClassName="bg-indigo-600 text-white hover:bg-indigo-700"
      inputClassName=""
      initialValue={initialConfigId}
      onSubmit={onSubmit}
    />
  );
};
