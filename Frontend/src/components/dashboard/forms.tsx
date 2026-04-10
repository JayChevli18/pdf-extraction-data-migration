import { Form, Formik } from "formik";
import * as Yup from "yup";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const singleLocalSchema = Yup.object({
  filename: Yup.string().trim().required("Filename is required"),
});

const singleCloudSchema = Yup.object({
  fileIdOrName: Yup.string().trim().required("Filename is required"),
});

export function SingleLocalForm({ onSubmit }: { onSubmit: (filename: string) => void }) {
  return (
    <Formik
      initialValues={{ filename: "" }}
      validationSchema={singleLocalSchema}
      onSubmit={(values, helpers) => {
        onSubmit(values.filename);
        helpers.setSubmitting(false);
      }}
    >
      {({ values, errors, touched, handleChange, isSubmitting }) => (
        <Form className="space-y-2">
          <Label htmlFor="filename" className="text-slate-700">
            Local single filename
          </Label>
          <div className="flex flex-col gap-2 sm:flex-row">
            <Input
              id="filename"
              name="filename"
              placeholder="filename.pdf"
              value={values.filename}
              onChange={handleChange}
              className="border-slate-300 focus-visible:ring-slate-400"
            />
            <Button
              type="submit"
              disabled={isSubmitting}
              className="bg-slate-900 text-white hover:bg-slate-800"
            >
              Run Local File
            </Button>
          </div>
          {touched.filename && errors.filename ? (
            <p className="text-sm text-red-600">{errors.filename}</p>
          ) : null}
        </Form>
      )}
    </Formik>
  );
}

export function SingleCloudForm({ onSubmit }: { onSubmit: (fileIdOrName: string) => void }) {
  return (
    <Formik
      initialValues={{ fileIdOrName: "" }}
      validationSchema={singleCloudSchema}
      onSubmit={(values, helpers) => {
        onSubmit(values.fileIdOrName);
        helpers.setSubmitting(false);
      }}
    >
      {({ values, errors, touched, handleChange, isSubmitting }) => (
        <Form className="space-y-2">
          <Label htmlFor="fileIdOrName" className="text-slate-700">
            Cloud single filename
          </Label>
          <div className="flex flex-col gap-2 sm:flex-row">
            <Input
              id="fileIdOrName"
              name="fileIdOrName"
              placeholder="filename.pdf"
              value={values.fileIdOrName}
              onChange={handleChange}
              className="border-blue-200 focus-visible:ring-blue-400"
            />
            <Button
              type="submit"
              disabled={isSubmitting}
              className="bg-blue-600 text-white hover:bg-blue-700"
            >
              Run Cloud File
            </Button>
          </div>
          {touched.fileIdOrName && errors.fileIdOrName ? (
            <p className="text-sm text-red-600">{errors.fileIdOrName}</p>
          ) : null}
        </Form>
      )}
    </Formik>
  );
}

export function UploadForm({ onSubmit }: { onSubmit: (files: File[]) => void }) {
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
}
