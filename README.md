# PDF Extraction Platform (Backend + Frontend)

End-to-end biodata/profile processing platform for `.pdf` and `.docx` files.

It supports three workflows:

- **Local**: local inbox -> organized local folders -> local Excel (`data/profiles.xlsx`)
- **Cloud (env-based)**: Google Drive inbox -> Drive organization -> Google Sheets
- **Tenant Cloud (config-based)**: per-user Google credentials registered via API (`config_id`) -> tenant upload/process APIs

---

## Tech Stack

- **Backend**: Python 3.11+, Flask, OpenAI/Ollama/DeepAI integration, Google Drive + Sheets APIs
- **Frontend**: Next.js 16, React 19, TanStack Query, Formik + Yup, shadcn/ui components
- **Document parsing**: `pdfplumber`, `python-docx`
- **Spreadsheet output**: `openpyxl` (local), Google Sheets (cloud)

---

## Repository Layout

```text
.
├─ Frontend/                         # Next.js dashboard app
├─ profile_backend/
│  ├─ src/profile_backend/
│  │  ├─ api/                        # Flask routes
│  │  ├─ application/                # Use-cases and runtime cloud config model
│  │  ├─ core/                       # settings + logging
│  │  ├─ domain/                     # business model/helpers
│  │  └─ infrastructure/             # AI, file extraction, Google adapters, config store
│  └─ tests/
├─ data/
│  ├─ storage/
│  │  ├─ inbox/                      # local inbox
│  │  ├─ root/                       # organized local output
│  │  └─ google_cloud_configs/       # tenant config bundles (generated)
│  └─ profiles.xlsx
├─ run.py                            # local CLI entrypoint
├─ requirements.txt
└─ pyproject.toml
```

---

## Developer Guide: Codebase Deep Dive

This section is a practical onboarding map for developers. It explains:

- how the architecture is layered,
- what each major file/module does,
- which functions matter most,
- and how requests move through the system.

### 1) Architecture (high-level)

The backend follows a layered structure close to MVC + Clean Architecture:

- **API layer (`api/`)**  
  Flask routes (controllers) parse requests and return responses.
- **Application layer (`application/`)**  
  Orchestrates use-cases (`local_processing`, `cloud_processing`).
- **Domain layer (`domain/`)**  
  Pure business models + rules (IDs, folder naming, normalization).
- **Infrastructure layer (`infrastructure/`)**  
  External integrations (AI providers, Google Drive/Sheets, file parsing, spreadsheet I/O).
- **Core layer (`core/`)**  
  Cross-cutting runtime settings and logging.

### 2) End-to-End Request Flows

#### A) Local processing flow (`POST /process`)

1. API route in `api/app.py` receives request.
2. Calls `application/services/local_processing.py`.
3. Reads files from local inbox (`data/storage/inbox`).
4. Extracts text (`infrastructure/files/text_extract.py`).
5. Extracts structured profile fields via AI (`infrastructure/ai/extractor.py`).
6. Organizes/moves file into `root/<Year>/<Gender>/`.
7. Appends row into local Excel (`data/profiles.xlsx`).

#### B) Cloud processing flow (`POST /cloud/process`)

1. API route in `api/app.py` calls cloud service.
2. `cloud_processing.py` lists Drive inbox files.
3. Downloads file bytes in-memory (no permanent local copy).
4. Runs text extraction + AI extraction.
5. Moves/renames Drive file into `Root/Year/Gender`.
6. Creates restricted share link.
7. Appends row into Google Sheet.

#### C) Cloud upload flow (`POST /cloud/upload`)

1. API validates multipart files (max 10).
2. Uses upload credentials (OAuth client file by default).
3. Uploads incoming files to Drive inbox folder.
4. Returns uploaded IDs + names.

#### D) Tenant cloud flow (config-based multi-tenant)

This is the full tenant lifecycle used by frontend "Tenant Cloud" tab:

1. **Register tenant config** via `POST /cloud/config/register`
   - Upload tenant credential bundle (service account required; optional client/drive/sheets files).
   - Send tenant-specific folder/sheet IDs.
   - API validates and persists a config bundle under `data/storage/google_cloud_configs/<config_id>/`.
2. **Receive `config_id`** from response.
3. **Tenant upload** via `POST /cloud/tenant/upload?config_id=<uuid>`
   - Uploads files to that tenant’s Drive inbox using tenant upload creds.
4. **Tenant process all** via `POST /cloud/tenant/process?config_id=<uuid>`
   - Processes all files from tenant inbox and appends rows to tenant sheet.
5. **Tenant process single** via `POST /cloud/tenant/process/<fileId_or_name>?config_id=<uuid>`
   - Processes one file by ID or exact file name.
6. **Optional cleanup** via `DELETE /cloud/config/<config_id>`
   - Deletes persisted config bundle when tenant is deprovisioned.

### 3) Backend File-by-File Map

#### `profile_backend/src/profile_backend/api/`

- `app.py`  
  Main Flask app factory (`create_app`) and route definitions for health, local, cloud, tenant-cloud, and upload/process endpoints.
- `google_config_http.py`  
  Helper for tenant cloud config resolution from request (`config_id` query/header), used by tenant endpoints.
- `__init__.py`  
  Package marker.

#### `profile_backend/src/profile_backend/application/`

- `services/local_processing.py`  
  Local use-cases: `list_inbox_files()`, `process_one(path)`, `process_inbox()`, plus internal `_build_record(...)`.
- `services/cloud_processing.py`  
  Cloud use-cases: `process_cloud_inbox()`, `process_cloud_one(...)`, `upload_to_cloud_inbox(...)`, plus helper `_suffix_from_mime(...)`.
- `google_cloud_config.py`  
  Runtime config model for cloud credentials/IDs and validation helpers (`validate_cloud_config`, `validate_upload_config`).
- `services/__init__.py`, `__init__.py`  
  Package markers.

#### `profile_backend/src/profile_backend/domain/`

- `models.py`  
  `ProfileRecord` dataclass and column schema used by local/cloud outputs.
- `ids.py`  
  ID generation logic (`BIOYYYYMMDDXXXX` style).
- `organize.py`  
  Folder naming/normalization helpers (`year_folder_from_dob`, `gender_folder`, `filename_from_name`, `normalize_dob`, etc.).
- `__init__.py`  
  Package marker.

#### `profile_backend/src/profile_backend/infrastructure/`

##### `infrastructure/ai/`
- `extractor.py`  
  AI extraction adapter. Supports multiple providers (`ollama`, `deepai`, `openai`) through `extract_fields_ai_provider(text)`.
- `__init__.py`

##### `infrastructure/google/`
- `auth.py`  
  Loads Google credentials (service account or OAuth client flow + token cache).
- `drive_client.py`  
  Drive API wrapper: list inbox files, download bytes, upload files, create folders, move/rename, generate share links.
- `sheets_client.py`  
  Sheets API wrapper: append row values to configured sheet tab.
- `config_store.py`  
  Persistent tenant cloud configuration storage for dynamic per-tenant credentials.
- `__init__.py`

##### `infrastructure/files/`
- `text_extract.py`  
  Text extraction from local file path and from in-memory bytes (`pdfplumber`/`python-docx`).
- `__init__.py`

##### `infrastructure/storage/`
- `spreadsheet.py`  
  Local Excel file operations for append-only behavior.
- `__init__.py`

##### Root infra marker
- `infrastructure/__init__.py`

#### `profile_backend/src/profile_backend/core/`

- `settings.py`  
  Centralized environment-driven runtime config (`settings` singleton).
- `logging.py`  
  Logging setup (formatter/handlers) used across API and services.
- `__init__.py`

#### `profile_backend/src/profile_backend/cli/`

- `main.py`  
  CLI commands for local workflow (list/process).
- `__init__.py`

#### `profile_backend/src/profile_backend/`

- `__init__.py`  
  Package identity.

### 4) Top-level Project Files

- `run.py`  
  Convenience CLI entrypoint.
- `requirements.txt`  
  Pip runtime dependencies.
- `pyproject.toml`  
  Package metadata + dependencies for editable installs.
- `.env.example`  
  Environment variable template.
- `README.md`  
  Operational and developer documentation.
- `data/`  
  Runtime data (inbox/root temp output, local spreadsheet, cloud config bundles).

### 5) Tests

- `profile_backend/tests/test_api_smoke.py`  
  Basic API smoke behavior.
- `profile_backend/tests/test_domain_helpers.py`  
  Domain helper/unit-level rules.
- `profile_backend/tests/test_google_cloud_config.py`  
  Cloud config validation/persistence behavior.

### 6) Frontend Code Map

#### `Frontend/src/app/`

- `layout.tsx`  
  App shell.
- `page.tsx`  
  Main dashboard page composition.

#### `Frontend/src/components/`

- `dashboard-content.tsx`  
  Top-level dashboard composition.
- `dashboard/sections.tsx`  
  Tab/section rendering (local, cloud, tenant).
- `dashboard/use-dashboard-state.ts`  
  State orchestration + API action wiring for the dashboard.
- `dashboard/forms.tsx` and `dashboard/forms.tsx` helpers  
  Form UI/validation wiring.
- `dashboard/header.tsx`, `loading-overlay.tsx`, `result-panel.tsx`, `types.ts`  
  Reusable dashboard pieces.

#### `Frontend/src/lib/`

- `api-client.ts`  
  HTTP request wrappers to backend endpoints.
- `query-client.ts`  
  TanStack Query client setup.
- `utils.ts`  
  Shared utilities.

#### `Frontend/src/types/`

- `api.ts`  
  Frontend-side request/response type shapes.

### 7) Key Functions New Developers Should Know First

- `api/app.py:create_app()`  
  Entrypoint for all HTTP behavior.
- `application/services/local_processing.py:process_one()`  
  Local core processing pipeline.
- `application/services/cloud_processing.py:process_cloud_one()`  
  Cloud core processing pipeline.
- `infrastructure/ai/extractor.py:extract_fields_ai_provider()`  
  Central AI extraction switchboard.
- `infrastructure/google/drive_client.py:upload_file_to_folder()`  
  Cloud upload path.
- `infrastructure/google/sheets_client.py:append_row()`  
  Cloud sheet write path.
- `domain/models.py:ProfileRecord`  
  Source-of-truth row schema used by both local and cloud modes.

### 8) Example: Where to Change What

- **Add a new extracted field**  
  1) Update `domain/models.py` (`ProfileRecord`)  
  2) Update AI output mapping in `infrastructure/ai/extractor.py`  
  3) Ensure sheet append receives the new column
- **Change folder naming rule**  
  Edit `domain/organize.py` only (keep application/infrastructure untouched).
- **Add new cloud endpoint**  
  1) Add route in `api/app.py`  
  2) Add orchestration in `application/services/cloud_processing.py`  
  3) Reuse/extend infra clients.
- **Add new AI provider**  
  Implement adapter in `infrastructure/ai/extractor.py` and route by provider in `extract_fields_ai_provider`.

### 9) Working Conventions

- Keep business rules in `domain/`.
- Keep side effects/integrations in `infrastructure/`.
- Keep route handlers thin; orchestration belongs in `application/services/`.
- Add tests when changing domain rules or endpoint contracts.

---

## Quick Start

### 1) Backend setup

From repo root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Alternative install (from `pyproject.toml`):

```powershell
pip install -e .
```

### 2) Configure environment

Create `.env` from template:

```powershell
Copy-Item .env.example .env
```

Load `.env` into current shell:

```powershell
Get-Content .env | ForEach-Object {
  if ($_ -match '^\s*#' -or $_ -match '^\s*$') { return }
  $name, $value = $_ -split '=', 2
  Set-Item -Path "Env:$name" -Value $value
}
```

### 3) Run backend

API server:

```powershell
flask --app profile_backend.src.profile_backend.api.app:create_app run --host 0.0.0.0 --port 5000
```

CLI (local only):

```powershell
python run.py list
python run.py process
python run.py process --file "SomeFile.pdf"
```

Base URL: `http://127.0.0.1:5000`

### 4) Frontend setup

```powershell
cd Frontend
npm install
npm run dev
```

Frontend default URL: `http://127.0.0.1:3000`  
Optional env: `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:5000`

---

## Ollama + OpenClaw Setup (Windows)

This project can use `PROFILE_LLM_PROVIDER=ollama`.  
If you are using OpenClaw through Ollama, use the flow below.

### 1) Install Ollama

- Install Ollama for Windows from the official installer.
- Verify installation:

```powershell
ollama --version
```

### 2) Start Ollama/OpenClaw from terminal UI (launcher flow)

Run:

```powershell
ollama
```

In the interactive launcher menu:

- Choose **Launch OpenClaw (llama3.1:8b)**.
- Wait until you see logs similar to:
  - `OpenClaw is running`
  - web UI URL on `http://localhost:18789/...`
  - TUI connected to `ws://127.0.0.1:18789`

This matches the startup sequence shown in the attached screenshots.

### 3) Keep services running

- Keep this terminal open while backend extraction is running.
- In `.env`, keep:
  - `PROFILE_LLM_PROVIDER=ollama`
  - `OLLAMA_API_URL=http://127.0.0.1:11434/api/chat`
  - `OLLAMA_MODEL=llama3.1:8b` (or your installed model)

### 4) Optional: start plain Ollama service directly

If you are not using the OpenClaw launcher and want raw Ollama only:

```powershell
ollama serve
```

Then ensure your model exists/pulled (example):

```powershell
ollama pull llama3.1:8b
```

### 5) Common issues

- **Timeout errors** (`timed out`, `surface_error reason=timeout`):
  - Model/server is busy or not ready yet.
  - Wait for OpenClaw/Ollama to fully initialize.
  - Try a smaller/faster model.
  - Retry processing single-file first (`/cloud/process/<file>` or tenant single-file endpoint).
- **Backend cannot reach Ollama**:
  - Confirm Ollama/OpenClaw process is still running.
  - Confirm `OLLAMA_API_URL` is reachable from backend machine/session.

---

## Environment Variables (`.env.example`)

### Local storage

- `PROFILE_STORAGE_ROOT`
- `PROFILE_INBOX_DIR`
- `PROFILE_ORGANIZED_ROOT`
- `PROFILE_SPREADSHEET_PATH`
- `PROFILE_LOG_DIR`

### AI provider

- `PROFILE_LLM_PROVIDER` (`ollama`, `openai`, `deepai`)
- `PROFILE_LLM_MODEL`
- `OPENAI_API_KEY`, `OPENAI_BASE_URL`
- `DEEPAI_API_KEY`, `DEEPAI_API_URL`
- `OLLAMA_API_URL`, `OLLAMA_MODEL`

### NLP

- `PROFILE_SPACY_MODEL`

### Google cloud (env-based flow)

- `PROFILE_GOOGLE_CREDS_JSON`
- `PROFILE_GOOGLE_PROCESS_CREDS_JSON`
- `PROFILE_GOOGLE_UPLOAD_CREDS_JSON`
- `PROFILE_GOOGLE_DRIVE_CREDS_JSON`
- `PROFILE_GOOGLE_SHEETS_CREDS_JSON`
- `PROFILE_GDRIVE_INBOX_FOLDER_ID`
- `PROFILE_GDRIVE_ROOT_FOLDER_ID`
- `PROFILE_GSHEETS_SPREADSHEET_ID`
- `PROFILE_GSHEETS_SHEET_NAME`
- `PROFILE_GDRIVE_SHARE_WITH_EMAILS`

### API / CORS

- `PROFILE_CORS_ORIGINS` (comma-separated)

---

## Google Cloud Credential Setup (Step-by-Step)

This section explains how to create and configure all Google credentials used by this project:

- `service-account.json` (recommended for **cloud process** APIs)
- `client-secret.json` (recommended for **cloud upload** APIs, uses user Drive quota)

It also covers IAM sharing and exactly which env variables to set.

### 1) Create a Google Cloud Project

1. Open [Google Cloud Console](https://console.cloud.google.com/).
2. Project selector (top bar) -> **New Project**.
3. Enter project name (example: `document-processing`) and create it.
4. Keep this project selected for all steps below.

### 2) Enable Required APIs

Go to **APIs & Services -> Library** and enable:

- **Google Drive API**
- **Google Sheets API**

### 3) Configure OAuth Consent Screen

1. Go to **APIs & Services -> OAuth consent screen**.
2. Choose **External** (or Internal for Workspace org).
3. Fill app details (name, support email, developer email).
4. Save and continue.
5. If app is in **Testing**:
   - Add your account in **Test users**.
   - Otherwise OAuth login will fail with `access_denied`.

### 4) Create OAuth Desktop Client (`client-secret.json`)

Use this for `/cloud/upload`.

1. **APIs & Services -> Credentials**.
2. **Create Credentials -> OAuth client ID**.
3. Application type: **Desktop app**.
4. Create and download JSON.
5. Save it as `client-secret.json` (repo root or any secure path).

Notes:
- Desktop app avoids most `redirect_uri_mismatch` issues.
- On first use, browser consent opens and app creates `token.json`.

### 5) Create Service Account (`service-account.json`)

Use this for `/cloud/process`.

1. Go to **IAM & Admin -> Service Accounts**.
2. **Create Service Account** (example: `profile-backend-sa`).
3. Open service account -> **Keys** tab.
4. **Add Key -> Create new key -> JSON**.
5. Download and save as `service-account.json`.

### 6) IAM / Resource Sharing Setup

Even with valid JSON, APIs fail unless resources are shared correctly.

#### Drive folders

Create/select:
- Inbox folder (input)
- Root folder (organized output)

Share both with:
- `client_email` from `service-account.json`
- Permission: **Editor**

#### Google Sheet

Share target sheet with the same service account email:
- Permission: **Editor**

### 7) Collect IDs for Env Vars

#### Drive folder IDs

From URL:
`https://drive.google.com/drive/folders/<FOLDER_ID>`

Use:
- `PROFILE_GDRIVE_INBOX_FOLDER_ID=<FOLDER_ID>`
- `PROFILE_GDRIVE_ROOT_FOLDER_ID=<FOLDER_ID>`

#### Spreadsheet ID

From URL:
`https://docs.google.com/spreadsheets/d/<SPREADSHEET_ID>/edit`

Use:
- `PROFILE_GSHEETS_SPREADSHEET_ID=<SPREADSHEET_ID>`
- `PROFILE_GSHEETS_SHEET_NAME=<TAB_NAME>` (example: `Sheet1`)

### 8) Set Env Variables (recommended split)

```powershell
$env:PROFILE_GOOGLE_UPLOAD_CREDS_JSON="D:\Jay\PDF-Extraction\client-secret.json"
$env:PROFILE_GOOGLE_PROCESS_CREDS_JSON="D:\Jay\PDF-Extraction\service-account.json"
$env:PROFILE_GDRIVE_INBOX_FOLDER_ID="<your_inbox_folder_id>"
$env:PROFILE_GDRIVE_ROOT_FOLDER_ID="<your_root_folder_id>"
$env:PROFILE_GSHEETS_SPREADSHEET_ID="<your_spreadsheet_id>"
$env:PROFILE_GSHEETS_SHEET_NAME="Sheet1"
```

Optional restricted sharing (no public links):

```powershell
$env:PROFILE_GDRIVE_SHARE_WITH_EMAILS="user1@example.com,user2@example.com"
```

### 9) Restart Backend After Env Updates

```powershell
flask --app profile_backend.src.profile_backend.api.app:create_app run --host 0.0.0.0 --port 5000
```

### 10) Validation Checklist

1. `POST /cloud/upload` succeeds (OAuth flow first time only).
2. `POST /cloud/process` succeeds (service account can read/move and write sheet).
3. Files land under `Root/Year/Gender`.
4. Sheet gets appended rows.

### Common Errors

- `redirect_uri_mismatch`
  - OAuth client type mismatch; use Desktop app client.
- `access_denied`
  - Add account to OAuth test users.
- `Service Accounts do not have storage quota`
  - Service account upload to My Drive blocked; use OAuth upload or Shared Drive.
- `missing fields client_email, token_uri`
  - Wrong credential file type for flow.

---

## API Endpoints

### Health

- `GET /health`

### Local processing

- `POST /process`
- `POST /process/<path:name>`

### Cloud (env-based, unchanged)

- `POST /cloud/upload` (multipart, field: `files`, max 10)
- `POST /cloud/process`
- `POST /cloud/process/<path:file_id_or_name>`

### Tenant Cloud (config-based)

- `POST /cloud/config/register`
- `DELETE /cloud/config/<config_id>`
- `POST /cloud/tenant/upload?config_id=<uuid>`
- `POST /cloud/tenant/process?config_id=<uuid>`
- `POST /cloud/tenant/process/<path:file_id_or_name>?config_id=<uuid>`

---

## Tenant Cloud Workflow

1. Register tenant configuration using `POST /cloud/config/register`:
   - required multipart file: `service_account`
   - optional files: `client_secret`, `drive_credentials`, `sheets_credentials`
   - required form fields: `gdrive_inbox_folder_id`, `gdrive_root_folder_id`, `gsheets_spreadsheet_id`
2. Save returned `config_id`.
3. Call tenant upload/process endpoints with `config_id` (query param or `X-Profile-Google-Config` header).
4. Optional cleanup with `DELETE /cloud/config/<config_id>`.

Registered bundles are persisted under:

- `data/storage/google_cloud_configs/<config_id>/`

---

## Frontend Dashboard

The dashboard is split into three tabs:

- **Cloud**: env-based upload + process controls
- **Tenant Cloud**: config register/select/upload/process controls
- **Local**: local batch + single-file processing

Recent UX updates include:

- clearer active tab styling
- pointer cursor on tabs
- tenant flow split into dedicated cards (register, select config, upload, process)

---

## Notes on Uploads and Timeouts

- Upload MIME type for `.pdf` / `.docx` is enforced server-side to prevent corrupted Drive preview/type issues.
- Single-file cloud processing endpoints return:
  - `504` for timeout-related runtime failures (including Ollama timeout scenarios)
  - `502` for other upstream/runtime failures

---

## Outputs

- Local organized files: `data/storage/root/<Year>/<Gender>/...`
- Local spreadsheet: `data/profiles.xlsx`
- Cloud output rows: configured Google Sheet tab
- Logs: `logs/profile_backend.log`

---

## Testing

Run backend tests:

```powershell
python -m unittest discover -s profile_backend/tests -v
```

Frontend lint:

```powershell
cd Frontend
npm run lint
```

---

## Dependencies Reference

- `requirements.txt` contains direct install dependencies for backend runtime.
- `pyproject.toml` defines package metadata (`profile-backend`) and dependency list for packaging/editable installs.

---

## Packages & Tools Reference (Purpose + Example)

This section lists the major packages/tools used in this project and explains:

- what each one does,
- where it is used,
- and a quick example.

### Backend Python Packages

- **Flask**
  - **Purpose**: HTTP API framework for local/cloud/tenant endpoints.
  - **Used in**: `profile_backend/src/profile_backend/api/app.py`
  - **Example**: `@app.post("/cloud/process")`

- **flask-cors**
  - **Purpose**: Enables frontend apps (different origin) to call backend APIs.
  - **Used in**: `api/app.py`
  - **Example**: `CORS(app, resources={r"/*": {"origins": origins}})`

- **pdfplumber**
  - **Purpose**: Extract text from PDF files.
  - **Used in**: `infrastructure/files/text_extract.py`
  - **Example**: `with pdfplumber.open(path) as pdf: ...`

- **python-docx**
  - **Purpose**: Extract text from DOCX documents.
  - **Used in**: `infrastructure/files/text_extract.py`
  - **Example**: `doc = Document(path_or_bytes_io)`

- **openpyxl**
  - **Purpose**: Local Excel writing (`data/profiles.xlsx`) for local flow.
  - **Used in**: `infrastructure/storage/spreadsheet.py`
  - **Example**: append one row to next empty Excel row.

- **openai**
  - **Purpose**: OpenAI-compatible LLM extraction provider.
  - **Used in**: `infrastructure/ai/extractor.py`
  - **Example**: `client.chat.completions.create(...)`

- **google-api-python-client**
  - **Purpose**: Google Drive + Sheets API calls.
  - **Used in**: `infrastructure/google/drive_client.py`, `sheets_client.py`
  - **Example**: `build("drive", "v3", credentials=creds)`

- **google-auth**
  - **Purpose**: Google credential objects, token refresh, auth plumbing.
  - **Used in**: `infrastructure/google/auth.py`
  - **Example**: `Credentials.from_service_account_file(...)`

- **google-auth-httplib2**
  - **Purpose**: HTTP transport integration used by Google client stack.
  - **Used in**: transitive auth/runtime for Google APIs.
  - **Example**: leveraged when Drive/Sheets client executes requests.

- **google-auth-oauthlib**
  - **Purpose**: OAuth desktop/web flow for `client-secret.json` auth.
  - **Used in**: `infrastructure/google/auth.py`
  - **Example**: `InstalledAppFlow.from_client_secrets_file(...).run_local_server(...)`

### AI Providers / External Services

- **Ollama**
  - **Purpose**: Local LLM provider (default) for extraction without cloud key dependency.
  - **Config**: `PROFILE_LLM_PROVIDER=ollama`, `OLLAMA_API_URL`, `OLLAMA_MODEL`
  - **Example**: `POST http://127.0.0.1:11434/api/chat`

- **OpenAI API**
  - **Purpose**: Cloud LLM extraction provider.
  - **Config**: `OPENAI_API_KEY`, optional `OPENAI_BASE_URL`
  - **Example**: structured JSON extraction from profile text.

- **DeepAI API**
  - **Purpose**: Alternate cloud extraction provider.
  - **Config**: `DEEPAI_API_KEY`, `DEEPAI_API_URL`
  - **Example**: prompt-based extraction fallback path.

- **Google Drive API**
  - **Purpose**: Cloud inbox listing, upload, download, move/rename, share link.
  - **Used in**: `drive_client.py` + `cloud_processing.py`
  - **Example**: `POST /cloud/upload` uploads up to 10 files to Drive inbox.

- **Google Sheets API**
  - **Purpose**: Append extracted rows into configured cloud sheet.
  - **Used in**: `sheets_client.py` + `cloud_processing.py`
  - **Example**: `append_row(..., sheet_name="Sheet1", row_values=[...])`

### Frontend Packages / Tooling (Next.js app)

- **Next.js**
  - **Purpose**: App framework and routing for dashboard UI.
  - **Used in**: `Frontend/src/app/*`
  - **Example**: `page.tsx` renders dashboard entry.

- **React**
  - **Purpose**: Component/state model for dashboard interactions.
  - **Used in**: `Frontend/src/components/*`
  - **Example**: tabs + forms for local/cloud/tenant actions.

- **TanStack Query**
  - **Purpose**: API mutation/query state management (loading/error/cache).
  - **Used in**: frontend dashboard state hooks.
  - **Example**: execute upload/process actions with consistent async UX.

- **Formik + Yup**
  - **Purpose**: Form state + validation for structured user inputs.
  - **Used in**: dashboard form components.
  - **Example**: validate required tenant fields before register call.

- **shadcn/ui**
  - **Purpose**: UI primitives (cards, tabs, inputs, alerts, badges).
  - **Used in**: `Frontend/src/components/ui/*`
  - **Example**: consistent admin/dashboard styling and interaction.

### Core Runtime Tools / Utilities

- **Python virtual environment (`venv`)**
  - **Purpose**: Isolate backend dependencies.
  - **Example**: `python -m venv .venv`

- **npm**
  - **Purpose**: Frontend dependency and script runner.
  - **Example**: `npm install`, `npm run dev`

- **Environment variables (`.env`)**
  - **Purpose**: Control credentials, folder IDs, models, and behavior by environment.
  - **Example**: set `PROFILE_GOOGLE_UPLOAD_CREDS_JSON` vs `PROFILE_GOOGLE_PROCESS_CREDS_JSON`

- **Service Account JSON / OAuth Client Secret JSON**
  - **Purpose**: Google authentication modes for server-to-server and user-auth flows.
  - **Example**:
    - process: `service-account.json`
    - upload: `client-secret.json`

---

## Troubleshooting

- If env values change, reload `.env` in shell and restart backend.
- For tenant APIs, ensure valid JSON credentials and all required folder/sheet IDs.
- If using Ollama, confirm service is running and selected model is available.
