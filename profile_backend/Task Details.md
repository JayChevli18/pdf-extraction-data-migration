## Overview
Build a backend system that automatically processes profile documents (PDF/DOCX), extracts structured data using AI, organizes files in cloud storage, and inserts the data into a spreadsheet. This should completely replace the current manual workflow.

## Objectives
- Read documents from cloud storage
- Extract structured data using AI/NLP
- Organize files dynamically based on extracted data
- Insert extracted data into a spreadsheet
- Maintain strict logging and error handling

## Core Workflow (Strict Order)
### Step 1 — Fetch File
- Access configured cloud storage folder
- Identify next unprocessed file (PDF/DOCX)

### Step 2 — Extract Basic Metadata (Light Parse)
- Open file using cloud document viewer (no download)
- Extract:
  - Date of Birth
  - Gender
- Store temporarily

### Step 3 — Organize File
- Determine:
  - Year (from DOB)
  - Gender
- Move file into structure:  
  `Root / Year / Gender`
- Create folders if they do not exist

### Step 4 — Rename File
- Rename format: `FirstName_LastName_Profile`
  - Replace spaces with underscores
  - Do not manually handle extensions

### Step 5 — Generate Share Link
- Ensure file is accessible via link (read-only)
- Store link for later use

### Step 6 — Full AI Data Extraction
- **Fields to Extract (Final Columns):**
  - ID
  - Name
  - Gender
  - Date of Birth (DOB)
  - Birth Place
  - Birth Time
  - Height
  - Religion & Caste
  - Contact Number
  - Email
  - Address
  - Occupation / Work
  - Salary
  - Education
  - Father Name
  - Father Occupation
  - Mother Name
  - Mother Occupation
  - Hobbies
  - Preferences
  - Diet Preference
  - Brothers
  - Sisters
  - Drive Link
  - Upload Date
  - Year

- **Extraction Rules:**
  - Extract only what exists in the document
  - Do NOT guess missing values
  - Leave fields blank if not found
  - Use AI to handle different formats

### Step 7 — Generate System Fields
- ID → `BIOYYYYMMDDXXXX`
- Upload Date → Current date
- Year → From DOB

### Step 8 — Insert into Spreadsheet
- Open configured spreadsheet
- Find next empty row
- Insert all extracted values

- **Rules:**
  - Do NOT overwrite existing data
  - Maintain column order
  - Leave missing fields blank

## Data Handling Rules
- No screenshots
- No image-based extraction
- No local file downloads
- No storing sensitive data outside cloud + sheet

## Folder Structure
```
Root
 └── Year
      └── Gender
```

## Acceptance Criteria
- Fully automated processing
- Correct file organization
- Accurate data extraction
- Sheet updated correctly
- Logs available for every step
- No manual intervention
