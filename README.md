# Profile Backend - Full Project Documentation

## Overview

This project is a Python backend that processes biodata/profile documents (`.pdf`, `.docx`) and converts them into structured records.

It supports two execution modes:

- Local mode: local inbox -> local folder organization -> local Excel output
- Cloud mode: Google Drive inbox -> Drive organization -> Google Sheets output

Primary capabilities:

- AI-based field extraction (`ollama`, `openai`, `deepai`)
- DOB normalization to `YYYY-MM-DD`
- Year derivation from DOB
- File organization by `Year/Gender`
- Stable row model for sheet output
- CLI + HTTP API operation

---

## Architecture

The codebase uses strict clean architecture:

```text
profile_backend/
  src/
    profile_backend/
      api/                      # Flask routes (transport layer)
      application/services/     # Use-case orchestration
      core/                     # Shared runtime config/logging
      domain/                   # Business entities and rules
      infrastructure/           # External adapters (AI, files, Google, storage)
      cli/                      # Programmatic CLI helpers
  tests/                        # Unit/smoke tests
run.py                          # Main CLI entrypoint
```

Dependency direction:

- `api` -> `application`
- `application` -> `domain`, `core`, `infrastructure`
- `domain` is business-logic focused
- `infrastructure` contains external I/O integrations

---

## Runtime Flow

### Local flow

1. Read inbox files (`.pdf`/`.docx`)
2. Extract text from file
3. Extract profile fields with AI provider
4. Normalize DOB to `YYYY-MM-DD`
5. Derive destination year/gender folders
6. Rename/move file into organized root
7. Build `ProfileRecord`
8. Append row to local Excel

### Cloud flow

1. Validate cloud env vars
2. Build Drive + Sheets clients
3. List files in Drive inbox folder
4. Download file bytes
5. Extract text from bytes
6. AI extraction + DOB normalization
7. Ensure `Year/Gender` folders in Drive
8. Move + rename file in Drive
9. Generate Drive share/view link
10. Append row to Google Sheet

---

## Setup

From repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## Environment Configuration

1) Create `.env` from template:

```powershell
Copy-Item .env.example .env
```

2) Load `.env` into current PowerShell session (required before run):

```powershell
Get-Content .env | ForEach-Object {
  if ($_ -match '^\s*#' -or $_ -match '^\s*$') { return }
  $name, $value = $_ -split '=', 2
  Set-Item -Path "Env:$name" -Value $value
}
```

Important variable groups:

- Local paths:
  - `PROFILE_STORAGE_ROOT`
  - `PROFILE_INBOX_DIR`
  - `PROFILE_ORGANIZED_ROOT`
  - `PROFILE_SPREADSHEET_PATH`
  - `PROFILE_LOG_DIR`
- AI:
  - `PROFILE_LLM_PROVIDER`, `PROFILE_LLM_MODEL`
  - `OPENAI_API_KEY`, `OPENAI_BASE_URL`
  - `DEEPAI_API_KEY`, `DEEPAI_API_URL`
  - `OLLAMA_API_URL`, `OLLAMA_MODEL`
- Google cloud:
  - `PROFILE_GOOGLE_UPLOAD_CREDS_JSON`
  - `PROFILE_GOOGLE_DRIVE_CREDS_JSON`
  - `PROFILE_GOOGLE_SHEETS_CREDS_JSON`
  - `PROFILE_GDRIVE_INBOX_FOLDER_ID`
  - `PROFILE_GDRIVE_ROOT_FOLDER_ID`
  - `PROFILE_GSHEETS_SPREADSHEET_ID`
  - `PROFILE_GSHEETS_SHEET_NAME`
  - `PROFILE_GDRIVE_SHARE_WITH_EMAILS` (optional)
- API/CORS:
  - `PROFILE_CORS_ORIGINS` (comma-separated, defaults to localhost:3000 variants)

---

## Running the Project

### CLI

```powershell
python run.py list
python run.py process
python run.py process --file "SomeFile.pdf"
```

### API

```powershell
flask --app profile_backend.src.profile_backend.api.app:create_app run --host 0.0.0.0 --port 5000
```

Base URL: `http://127.0.0.1:5000`

---

## API Endpoints

- `GET /health`
- `POST /process`
- `POST /process/<filename>`
- `POST /cloud/upload`
- `POST /cloud/process`
- `POST /cloud/process/<fileIdOrExactName>`

Examples:

```powershell
Invoke-RestMethod http://127.0.0.1:5000/health
Invoke-RestMethod -Method Post http://127.0.0.1:5000/process
Invoke-RestMethod -Method Post "http://127.0.0.1:5000/process/John_Doe_Profile.pdf"
Invoke-RestMethod -Method Post http://127.0.0.1:5000/cloud/process
Invoke-RestMethod -Method Post "http://127.0.0.1:5000/cloud/process/<fileId>"
```

Upload endpoint notes:

- `POST /cloud/upload` expects `multipart/form-data`
- field name: `files` (repeatable)
- max 10 files
- supports `.pdf`, `.docx`

---

## Outputs

- Organized local files: `data/storage/root/<Year>/<Gender>/...`
- Local spreadsheet: `data/profiles.xlsx`
- Cloud sheet: configured Google Sheet tab
- Logs: `logs/profile_backend.log`

Record model columns (fixed order): `ID, Name, Gender, DOB, ... , Drive Link, Upload Date, Year`.

---

## Testing

Run all tests:

```powershell
python -m unittest discover "profile_backend/tests"
```

Current tests:

- `test_api_smoke.py`: verifies `/health` response
- `test_domain_helpers.py`: validates DOB normalization/year extraction, gender mapping, and filename generation

---

## File-by-File Code Documentation

### Root

- `run.py`
  - **Purpose**: Main command-line entrypoint used by operators and developers for local processing.
  - **What it does**:
    - Parses CLI arguments (`process`, `list`, and optional `--file`).
    - Initializes centralized logging via `setup_logging()`.
    - Delegates real work to application service layer:
      - `list_inbox_files()`
      - `process_inbox()`
      - `process_one(path)`
    - Resolves single-file path against configured inbox directory from `settings`.
  - **Why it exists**: Keeps operational usage simple without exposing internal module structure.

### Package bootstrap

- `profile_backend/src/__init__.py`
  - **Purpose**: Marks `src` as importable package namespace.
  - **What it does**: No runtime logic; enables stable package discovery/import behavior.
- `profile_backend/src/profile_backend/__init__.py`
  - **Purpose**: Declares the main backend package.
  - **What it does**: Exposes package version metadata (`__version__`).

### API layer

- `profile_backend/src/profile_backend/api/__init__.py`
  - **Purpose**: Marks API folder as a package.
  - **What it does**: No runtime behavior; structural.
- `profile_backend/src/profile_backend/api/app.py`
  - **Purpose**: HTTP transport/controller layer.
  - **What it does**:
    - Creates Flask app through `create_app()`.
    - Defines all public endpoints (`/health`, `/process`, `/cloud/*`).
    - Validates request-level concerns (e.g., missing upload files, file count limits, local path safety).
    - Calls application services for business operations.
    - Converts service results/exceptions into JSON HTTP responses.
  - **Design note**: Route functions are intentionally thin; business logic remains outside API layer.

### Application layer

- `profile_backend/src/profile_backend/application/__init__.py`
  - **Purpose**: Marks application package.
  - **What it does**: Structural package declaration only.
- `profile_backend/src/profile_backend/application/services/__init__.py`
  - **Purpose**: Marks service package.
  - **What it does**: Structural package declaration only.
- `profile_backend/src/profile_backend/application/services/local_processing.py`:
  - **Purpose**: Encapsulates local processing use-cases.
  - **Core functions**:
    - `list_inbox_files()`: returns sorted supported local files (`.pdf`, `.docx`), creates inbox directory if missing.
    - `process_one(path)`: processes one local file end-to-end.
    - `process_inbox()`: batch processes all inbox files with per-file exception handling.
  - **Internal behavior**:
    - Extracts text from local file.
    - Calls AI extractor for structured fields.
    - Normalizes DOB and derives year.
    - Applies domain naming/foldering rules.
    - Moves file to organized target.
    - Builds `ProfileRecord` and appends row to Excel.
- `profile_backend/src/profile_backend/application/services/cloud_processing.py`:
  - **Purpose**: Encapsulates cloud processing use-cases.
  - **Core functions**:
    - `_validate_cloud_config()`: guards execution with required env vars.
    - `process_cloud_inbox()`: batch processing for Drive inbox.
    - `process_cloud_one(...)`: one-file cloud pipeline.
    - `upload_to_cloud_inbox(uploaded_files)`: multipart upload helper for `/cloud/upload`.
  - **Internal behavior**:
    - Builds Drive/Sheets clients.
    - Reads file bytes from Drive and extracts text.
    - Performs AI extraction and DOB normalization.
    - Creates/ensures destination folder hierarchy in Drive.
    - Moves/renames file in Drive.
    - Generates share link and appends output row to Google Sheets.

### Core layer

- `profile_backend/src/profile_backend/core/__init__.py`
  - **Purpose**: Core package marker.
  - **What it does**: Structural package declaration only.
- `profile_backend/src/profile_backend/core/settings.py`:
  - **Purpose**: Single source of truth for runtime configuration.
  - **Main constructs**:
    - `Settings` (frozen dataclass) containing local, AI, and cloud config fields.
    - `_env_path()` for env-driven path override handling.
    - `load_settings()` to assemble config from environment/defaults.
    - global `settings` singleton used across layers.
  - **Important behavior**:
    - Resolves project-relative defaults when env vars are not provided.
    - Separates Drive-processing credentials vs upload credentials.
- `profile_backend/src/profile_backend/core/logging.py`:
  - **Purpose**: Centralized logging bootstrap.
  - **What it does**:
    - Creates log directory.
    - Registers rotating file handler (`logs/profile_backend.log`) and console handler.
    - Uses consistent message format and levels.
    - Prevents duplicate handlers on repeated setup calls.

### Domain layer

- `profile_backend/src/profile_backend/domain/__init__.py`
  - **Purpose**: Domain package marker.
  - **What it does**: Structural package declaration only.
- `profile_backend/src/profile_backend/domain/models.py`:
  - **Purpose**: Defines canonical output model and column contract.
  - **What it does**:
    - Declares `SHEET_COLUMNS` with final fixed order.
    - Defines `ProfileRecord` dataclass for one output row.
    - Provides `to_row_list()` and `headers_for_sheet()` helpers.
  - **Why important**: Guarantees stable schema for both Excel and Google Sheets outputs.
- `profile_backend/src/profile_backend/domain/ids.py`:
  - **Purpose**: Generates system-level record IDs.
  - **What it does**:
    - Builds ID format `BIOYYYYMMDDXXXX`.
    - Uses DOB date portion when parseable, else current date fallback.
    - Appends random 4-digit suffix.
- `profile_backend/src/profile_backend/domain/organize.py`:
  - **Purpose**: Domain rules for naming, folders, and normalization.
  - **Core functions**:
    - `normalize_dob()` converts common human date formats into ISO.
    - `year_folder_from_dob()` derives year folder from normalized DOB.
    - `gender_folder()` normalizes to `Male`/`Female`/`Unknown`.
    - `filename_from_name()` maps names to template-friendly file base name.
    - `move_to_organized()` handles destination folder creation and collision-safe rename.
    - `file_share_link()` returns local `file://` URI.
  - **Why important**: Central place for business rules reused by both modes.

### Infrastructure layer

- `profile_backend/src/profile_backend/infrastructure/__init__.py`
  - **Purpose**: Infrastructure package marker.
  - **What it does**: Structural package declaration only.

AI adapters:

- `profile_backend/src/profile_backend/infrastructure/ai/__init__.py`
  - **Purpose**: AI adapter package marker.
- `profile_backend/src/profile_backend/infrastructure/ai/extractor.py`:
  - **Purpose**: Provider abstraction for field extraction from raw text.
  - **Main constructs**:
    - `AIExtractedFields` dataclass schema.
    - Provider implementations: `_extract_openai`, `_extract_ollama`, `_extract_deepai`.
    - Dispatcher: `extract_fields_ai_provider(text)`.
  - **Behavior details**:
    - Sanitizes returned values.
    - Normalizes DOB centrally before passing fields upward.
    - Enforces JSON-shaped response interpretation and error handling.

File adapters:

- `profile_backend/src/profile_backend/infrastructure/files/__init__.py`
  - **Purpose**: File adapter package marker.
- `profile_backend/src/profile_backend/infrastructure/files/text_extract.py`:
  - **Purpose**: Text extraction from documents.
  - **Core functions**:
    - `extract_text(path)` for local files.
    - `extract_text_bytes(suffix, data)` for cloud byte streams.
  - **Supported types**: `.pdf`, `.docx`.
  - **Libraries**: `pdfplumber`, `python-docx`.

Google adapters:

- `profile_backend/src/profile_backend/infrastructure/google/__init__.py`
  - **Purpose**: Google adapter package marker.
- `profile_backend/src/profile_backend/infrastructure/google/auth.py`:
  - **Purpose**: Credential loading for Google APIs.
  - **What it does**:
    - Supports service-account JSON directly.
    - Supports OAuth client secrets with token caching (`token.json`).
    - Refreshes expired OAuth tokens when possible.
- `profile_backend/src/profile_backend/infrastructure/google/drive_client.py`:
  - **Purpose**: Encapsulates all Drive API calls used by cloud services.
  - **Main capabilities**:
    - Build Drive client.
    - List inbox files with MIME filtering.
    - Download bytes.
    - Upload file to target folder.
    - Ensure folder existence.
    - Move + rename Drive file.
    - Create/retrieve restricted share link.
  - **Data model**: `DriveFile` dataclass for typed file metadata.
- `profile_backend/src/profile_backend/infrastructure/google/sheets_client.py`:
  - **Purpose**: Encapsulates Sheets API operations.
  - **Main capabilities**:
    - Build Sheets client.
    - Append a row to a configured sheet range (`A:Z`).

Storage adapters:

- `profile_backend/src/profile_backend/infrastructure/storage/__init__.py`
  - **Purpose**: Storage adapter package marker.
- `profile_backend/src/profile_backend/infrastructure/storage/spreadsheet.py`:
  - **Purpose**: Local Excel persistence adapter.
  - **Core functions**:
    - `ensure_workbook(path)` creates workbook and writes header row when file is missing.
    - `append_record(path, record)` appends one structured row and saves workbook.
  - **Why important**: Keeps Excel-specific I/O out of business logic.

### CLI helper package

- `profile_backend/src/profile_backend/cli/__init__.py`
  - **Purpose**: CLI package marker.
- `profile_backend/src/profile_backend/cli/main.py`
  - **Purpose**: Programmatic CLI helpers.
  - **What it does**:
    - `run_local()` initializes logging and runs local batch process.
    - `run_cloud()` initializes logging and runs cloud batch process.
  - **Usage**: Useful for future alternate entrypoints or scheduler integration.

### Tests

- `profile_backend/tests/test_api_smoke.py`
  - **Purpose**: Smoke test for API boot + health endpoint.
  - **What it validates**: app factory works, `/health` contract is stable.
- `profile_backend/tests/test_domain_helpers.py`
  - **Purpose**: Unit tests for domain normalization and naming rules.
  - **What it validates**:
    - DOB normalization (`15-01-1990` -> `1990-01-15`)
    - Year extraction from ISO/non-ISO input
    - Gender mapping
    - Filename template behavior for known/unknown names

---

## Operational Notes

- Keep `__init__.py` files (required for package imports).
- `__pycache__` folders are auto-generated and safe to ignore/delete.
- If env values are updated, restart process/server after reloading `.env`.
