# Profile Document Processing Backend (Local Storage)

This project is a **Python backend** that automatically processes **profile documents** (`.PDF` / `.DOCX`), extracts structured fields, organizes the files into a folder structure, and appends the extracted data into an Excel spreadsheet.

It is designed to replace a manual workflow with a repeatable, logged pipeline.

---

## What this system does (high level)

You drop files into an **inbox folder**:

- `data/storage/inbox/`  ← put PDFs/DOCXs here

Then you run the pipeline (CLI or API). For each file, it:

1. **Fetch file**: picks the next unprocessed file from the inbox
2. **Light parse (fast)**: extracts **DOB** + **gender** hints
3. **Organize file**: moves file to `Root / Year / Gender`
4. **Rename file**: `FirstName_LastName_Profile` (underscores, keeps extension)
5. **Generate link**: stores a local `file://...` URI as a “drive link” placeholder
6. **Full extraction**: extracts all remaining columns (no guessing)
7. **Generate system fields**: ID, upload date, year
8. **Insert into spreadsheet**: appends a new row (never overwrites)

Outputs:

- Organized files in: `data/storage/root/<Year>/<Gender>/...`
- Spreadsheet: `data/profiles.xlsx` (created automatically)
- Logs: `logs/profile_backend.log`

---

## Folder structure (local storage)

```text
PDF-Extraction/
  profile_backend/                # Python package (all backend logic)
  data/
    storage/
      inbox/                      # Input files go here
      root/                       # Organized output goes here
    profiles.xlsx                 # Output spreadsheet (auto-created)
  logs/
    profile_backend.log           # Pipeline logs (auto-created)
  run.py                          # CLI entrypoint
  requirements.txt                # Dependencies
  pyproject.toml                  # Packaging metadata
```

---

## Libraries used (what + why)

This project intentionally uses a small set of well-known libraries:

- **`pdfplumber`**
  - **What**: Extracts text from PDFs.
  - **Why**: Good real-world PDF text extraction with page support.

- **`python-docx`**
  - **What**: Reads `.docx` documents.
  - **Why**: Standard library for extracting paragraph text from Word files.

- **`spaCy`** (with model `en_core_web_sm`)
  - **What**: NLP library that can detect entities like **person names** and **dates**.
  - **Why**: Profiles can have different formats; spaCy helps when “Key: Value” labels are missing.
  - **Important**: We still do **not** guess. If a value cannot be found, it stays blank.

- **`openpyxl`**
  - **What**: Reads/writes Excel `.xlsx`.
  - **Why**: Allows appending rows without overwriting existing content.

- **`Flask`** (optional)
  - **What**: Tiny HTTP server framework.
  - **Why**: Lets you trigger the pipeline via API calls (`POST /process`).

Python standard libraries used:

- **`pathlib`**: safer file paths than manual string concatenation
- **`shutil` / `os`**: file operations (move, create folders)
- **`logging`**: consistent logs for every step

---

## How to run (step-by-step, Windows PowerShell)

### 1) Create and install the environment (one-time)

Open **PowerShell**, then:

```powershell
cd d:\Jay\PDF-Extraction

python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\python -m spacy download en_core_web_sm
.\.venv\Scripts\pip install -e .
```

If `python` is not recognized, use:

```powershell
py -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\python -m spacy download en_core_web_sm
.\.venv\Scripts\pip install -e .
```

### 2) Put files into the inbox

Copy your `.pdf` / `.docx` files into:

```text
d:\Jay\PDF-Extraction\data\storage\inbox\
```

### 3) Run the pipeline (CLI)

Process everything currently in the inbox:

```powershell
cd d:\Jay\PDF-Extraction
.\.venv\Scripts\python run.py process
```

List inbox files:

```powershell
.\.venv\Scripts\python run.py list
```

Process one file by name (file must exist inside the inbox folder):

```powershell
.\.venv\Scripts\python run.py process --file "John_Doe_Profile.pdf"
```

---

## How to run (API server)

Start the server:

```powershell
cd d:\Jay\PDF-Extraction
.\.venv\Scripts\python -m profile_backend.app
```

Server runs on:

- `http://127.0.0.1:5000`

### API endpoints

#### Health check

```powershell
Invoke-RestMethod http://127.0.0.1:5000/health
```

Response:

```json
{"status":"ok"}
```

#### Process all inbox files

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:5000/process
```

Response example:

```json
{
  "queued": ["D:\\Jay\\PDF-Extraction\\data\\storage\\inbox\\A.pdf"],
  "processed": 1,
  "ids": ["BIO199508157384"]
}
```

#### Process one file by name (NO payload)

This endpoint does **not** take any JSON body.
You pass the file name in the URL, and the file must be present in:
`data/storage/inbox/`.

Example:

```powershell
Invoke-RestMethod -Method Post "http://127.0.0.1:5000/process/John_Doe_Profile.pdf"
```

Response example:

```json
{"id":"BIO199508151013","name":"John Doe"}
```

---

## Spreadsheet columns (output)

The system appends rows with the following columns (in this exact order):

1. ID
2. Name
3. Gender
4. Date of Birth (DOB)
5. Birth Place
6. Birth Time
7. Height
8. Religion & Caste
9. Contact Number
10. Email
11. Address
12. Occupation / Work
13. Salary
14. Education
15. Father Name
16. Father Occupation
17. Mother Name
18. Mother Occupation
19. Hobbies
20. Preferences
21. Diet Preference
22. Brothers
23. Sisters
24. Drive Link
25. Upload Date
26. Year

Rules:

- If a value is not present in the document, the column is **left blank**.
- The pipeline **never overwrites existing rows**.

---

## “Drive Link” in local mode

Cloud share links don’t exist in local mode. Instead, we store:

- `file:///D:/Jay/PDF-Extraction/data/storage/root/...`

This is a local URI pointing to the organized file.
When you switch to cloud storage later, you will replace this link generator function.

---

## Configuration (paths)

By default, paths are inside this repo under `data/` and `logs/`.

You can override with environment variables:

- `PROFILE_STORAGE_ROOT`
- `PROFILE_INBOX_DIR`
- `PROFILE_ORGANIZED_ROOT`
- `PROFILE_SPREADSHEET_PATH`
- `PROFILE_LOG_DIR`
- `PROFILE_SPACY_MODEL` (default: `en_core_web_sm`)

Example:

```powershell
$env:PROFILE_INBOX_DIR="D:\SomeOtherFolder\inbox"
.\.venv\Scripts\python run.py process
```

---

## Architecture (how the code is organized)

Think of the system as 5 layers:

1. **Entrypoints**
   - `run.py` (CLI)
   - `profile_backend/app.py` (HTTP API)

2. **Pipeline orchestrator**
   - `profile_backend/pipeline.py`
   - Controls the strict processing order

3. **Extraction**
   - `profile_backend/text_extract.py` (PDF/DOCX → plain text)
   - `profile_backend/metadata_light.py` (fast DOB/gender hints)
   - `profile_backend/extractor.py` (full field extraction)

4. **Storage + naming**
   - `profile_backend/organize.py` (folders, renaming, moving, link)

5. **Output**
   - `profile_backend/spreadsheet.py` (append to Excel)
   - `profile_backend/models.py` (row model + headers)
   - `profile_backend/ids.py` (ID generation)

Cross-cutting:

- `profile_backend/logging_setup.py` creates consistent logs across everything.
- `profile_backend/config.py` defines folder paths and environment overrides.

---

## Detailed file-by-file documentation (with key functions)

Below is a beginner-friendly guide to each file and what it contains.

### `run.py` (CLI entrypoint)

Purpose: run the pipeline from the command line.

Key function:

- `main(argv=None) -> int`
  - Parses arguments:
    - `process` (default): process all inbox files
    - `list`: list inbox files
    - `--file`: process a specific file inside inbox
  - Calls `setup_logging()` so you can see progress.
  - Calls pipeline functions from `profile_backend/pipeline.py`.

Typical usage:

```powershell
.\.venv\Scripts\python run.py process
```

---

### `profile_backend/config.py` (paths + tunables)

Purpose: define where input/output live on disk.

Important values:

- `INBOX_DIR`: folder you drop files into
- `ORGANIZED_ROOT`: where organized files are moved
- `SPREADSHEET_PATH`: Excel output
- `LOG_DIR`: log output folder
- `SPACY_MODEL`: spaCy model name

Helper:

- `_env_path(key, default) -> Path`
  - If an env var exists, uses it; otherwise uses the default path.

---

### `profile_backend/logging_setup.py` (logging)

Purpose: logs are required for debugging and auditing.

Key function:

- `setup_logging(name="profile_backend") -> logging.Logger`
  - Logs to:
    - Console (INFO level)
    - `logs/profile_backend.log` (DEBUG level, rotating)

---

### `profile_backend/text_extract.py` (PDF/DOCX → text)

Purpose: the extractor works on plain text; this module converts files into text.

Key functions:

- `extract_text(path: Path) -> str`
  - Dispatches by file extension:
    - `.pdf` → `_pdf_text()`
    - `.docx` → `_docx_text()`

- `_pdf_text(path: Path) -> str`
  - Uses `pdfplumber.open(...)`
  - Loops pages and concatenates extracted text.

- `_docx_text(path: Path) -> str`
  - Uses `python-docx` `Document(...)`
  - Joins all paragraph text.

---

### `profile_backend/nlp_utils.py` (spaCy loading)

Purpose: loading spaCy is heavy; we load it once and reuse it.

Key function:

- `get_nlp()`
  - Lazy loads `spacy.load(SPACY_MODEL)`
  - Cached so repeated files process faster.

---

### `profile_backend/metadata_light.py` (Step 2: light parse)

Purpose: quickly find **DOB** and **gender** before moving the file.

Data model:

- `LightMetadata(date_of_birth: str|None, gender: str|None)`
  - `date_of_birth` is stored in ISO format `YYYY-MM-DD` if parsed.

Key functions:

- `extract_light_metadata(text: str) -> LightMetadata`
  - Uses spaCy DATE entities + simple date regex patterns.
  - Gender is a keyword check (Male/Female).

- `_try_parse_date(s: str) -> datetime|None`
  - Converts detected date strings into a real date object when possible.

---

### `profile_backend/extractor.py` (Step 6: full extraction)

Purpose: extract all “final columns” from the document.

Important rule:

- **No guessing**. If a field isn’t present, it stays blank.

How extraction works:

1. Look for **labeled lines** like `Email: someone@example.com`
2. If still missing:
   - find email via regex
   - find phone via regex
3. If name is still missing:
   - spaCy PERSON entity as a fallback

Key functions:

- `run_full_extraction(text: str) -> (ExtractedFields, LightMetadata)`
  - Convenience helper: runs light metadata + full extraction.

- `extract_fields(text: str, light: LightMetadata|None) -> ExtractedFields`
  - Produces all extractable fields.
  - Uses `light` to pre-fill DOB/gender if found.

- `explicit_name_from_text(text: str) -> str`
  - If the document has `Name: ...`, this returns it.
  - Helps avoid spaCy false positives for renaming.

- `primary_person_name(text: str) -> str`
  - Used for renaming (Step 4).
  - Prefers `Name: ...` first; otherwise uses first spaCy PERSON.

Internal helpers:

- `_split_label_lines(text)` yields `(key, value)` from lines containing `:`
- `_match_label(key)` maps keys like “DOB” to a canonical field
- `_first_email(text)`, `_first_phone(text)` regex helpers

---

### `profile_backend/organize.py` (Steps 3–5: organize + rename + link)

Purpose: move files into `Root / Year / Gender` and rename them.

Key functions:

- `year_folder_from_dob(dob_iso: str|None) -> str`
  - Extracts `YYYY` or returns `Unknown`.

- `gender_folder(gender: str|None) -> str`
  - Normalizes to `Male`, `Female`, or `Unknown`.

- `filename_from_name(full_name: str, template: str) -> str`
  - Converts `Jane Smith` → `Jane_Smith_Profile`
  - If name is missing → `Unknown_Unknown_Profile`

- `move_to_organized(src, organized_root, year, gender, new_base_name) -> Path`
  - Creates folders if needed.
  - Moves the file, preserves extension.
  - If a file name already exists, adds `_1`, `_2`, ... to avoid overwriting.

- `file_share_link(path: Path) -> str`
  - Returns a local `file://` URI (placeholder for cloud link later).

---

### `profile_backend/models.py` (data model for spreadsheet row)

Purpose: keeps spreadsheet order stable and explicit.

Key parts:

- `SHEET_COLUMNS`: exact column names/order
- `ProfileRecord` dataclass: holds one row’s values
- `headers_for_sheet()`: returns `SHEET_COLUMNS`

---

### `profile_backend/ids.py` (system ID generation)

Purpose: create IDs of format `BIOYYYYMMDDXXXX`.

Key function:

- `generate_profile_id(dob_iso: str|None) -> str`
  - Uses DOB if parseable → `BIO<dob_ymd><random_4_digits>`
  - Otherwise uses today’s date.

---

### `profile_backend/spreadsheet.py` (append to Excel)

Purpose: write extracted data without overwriting.

Key functions:

- `ensure_workbook(path: Path)`
  - Creates `data/profiles.xlsx` if missing
  - Writes the header row once

- `append_record(path: Path, record: ProfileRecord) -> int`
  - Appends a new row at the end.
  - Returns the row number written.

---

### `profile_backend/pipeline.py` (the strict workflow)

Purpose: orchestrate the processing steps in order.

Key functions:

- `list_inbox_files() -> list[Path]`
  - Returns supported `.pdf`/`.docx` files from inbox sorted by name.

- `process_one(path: Path) -> ProfileRecord`
  - Core “one file” workflow:
    - Extract text
    - Light parse DOB/gender (Step 2)
    - Organize + rename (Steps 3–4)
    - Full extraction (Step 6)
    - Build system fields (Step 7)
    - Append to sheet (Step 8)

- `process_inbox() -> list[ProfileRecord]`
  - Calls `process_one()` for every file.
  - Logs errors per file and continues.

Private helper:

- `_build_record(...) -> ProfileRecord`
  - Combines extracted fields + system fields into the row structure.

---

### `profile_backend/app.py` (Flask API)

Purpose: run the pipeline via HTTP.

Key functions:

- `create_app() -> Flask`
  - Registers routes:
    - `GET /health`
    - `POST /process`
    - `POST /process/<name>`

- `main()`
  - Starts the server on port 5000.

Important: `POST /process/<name>` takes **no payload**.

---

## Examples (what to expect)

### Example 1 — input

If you have:

```text
data/storage/inbox/John_Doe_Profile.pdf
```

And the document contains:

```text
Name: John Doe
Gender: Male
Date of Birth: 12/01/2001
Email: john@example.com
```

Then after processing you should see:

- File moved to:
  - `data/storage/root/2001/Male/John_Doe_Profile.pdf`
- A new row appended in:
  - `data/profiles.xlsx`
- Log lines in:
  - `logs/profile_backend.log`

---

## Troubleshooting

### “spaCy model not found”

Run:

```powershell
.\.venv\Scripts\python -m spacy download en_core_web_sm
```

### “Nothing processed”

Check:

- Files are in `data/storage/inbox/`
- Extension is `.pdf` or `.docx`

### “Unknown/Unknown folder”

This means DOB/gender was not found by the light parse.
The pipeline will still process and append a sheet row, but organization uses `Unknown`.

---

## Next upgrades (when you move to cloud)

When you later switch from local storage to cloud storage:

- Replace `file_share_link()` in `profile_backend/organize.py` with the cloud provider share-link logic
- Replace `list_inbox_files()` / moving logic with cloud folder listing + move operations

---

## AI-only extraction mode (current)

The pipeline now supports an AI-only path through `profile_backend/ai_extractor.py`:

- No manual label dictionary is required in the runtime flow.
- One LLM call extracts all profile fields from raw document text.
- Multilingual labels (Hindi/Gujarati/English mixed formats) are handled by the model.
- Missing values are returned as empty strings (no guessing).

Choose your provider with `PROFILE_LLM_PROVIDER`:

- `ollama` (default, local LLM)
- `textrazor`
- `openai`
- `deepai`

### Ollama setup (recommended for true AI mapping without paid API)

Install Ollama, pull a model, and run locally:

```powershell
ollama pull qwen2.5:7b
```

Then set:

```powershell
$env:PROFILE_LLM_PROVIDER="ollama"
$env:OLLAMA_API_URL="http://127.0.0.1:11434/api/chat"
$env:OLLAMA_MODEL="qwen2.5:7b"
```

### OpenAI setup

```powershell
$env:PROFILE_LLM_PROVIDER="openai"
$env:OPENAI_API_KEY="your_openai_key"
# Optional:
$env:PROFILE_LLM_MODEL="gpt-4o-mini"
$env:OPENAI_BASE_URL=""
```

### DeepAI setup

```powershell
$env:PROFILE_LLM_PROVIDER="deepai"
$env:DEEPAI_API_KEY="your_deepai_key"
# Optional override (defaults to DeepAI text endpoint):
$env:DEEPAI_API_URL="https://api.deepai.org/api/text-generator"
```

### TextRazor setup

```powershell
$env:PROFILE_LLM_PROVIDER="textrazor"
$env:TEXTRAZOR_API_KEY="your_textrazor_key"
# Optional override:
$env:TEXTRAZOR_API_URL="https://api.textrazor.com/"
```

Then run:

```powershell
.\.venv\Scripts\python run.py process
```

