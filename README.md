# API DB Extract (ETL Pipeline)

This is a Python-based ETL pipeline designed to extract blacklist/sanction data from various sources (Inaproc and World Bank) and load it into a centralized database (Erica API).

## Setup Instructions

1. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -e .[dev]
   ```

3. **Configure the Environment variables:**
   Copy the example environment file and fill in your credentials.
   ```bash
   cp .env.example .env
   ```
   Open `.env` and fill out your `TARGET_API_BASE_URL`, `TARGET_API_ACCOUNT_UID`, `TARGET_API_DATASET_UID_*`, and `TARGET_API_TOKEN`.

## Usage

The pipeline supports extracting data from `inaproc` and `worldbank`.

### 1. Dry Run Mode
To test the extraction process without actually sending any data to the Target API, append `--dry-run`:
```bash
python -m src.main --source inaproc --mode full-refresh --dry-run
```
The output payload will be safely dumped into the `outputs/` folder.

### 2. Full Refresh Mode
This mode ignores any previous checkpoints and fetches all data from page 1 to the end. Recommended for the first time setup.
```bash
python -m src.main --source inaproc --mode full-refresh
```

### 3. Incremental Mode
This mode resumes from the last successfully saved checkpoint. Recommended for daily scheduled runs (cron jobs).
```bash
python -m src.main --source inaproc --mode incremental
```

## Output & Logs

- **Checkpoints**: Saved automatically per source to keep track of the last successfully processed page.
- **Dead Letters**: Any records that fail validation, mapping, or are rejected by the Target API will be saved in `outputs/dead_letter_<source>_<run_id>.jsonl`. You can inspect these files to troubleshoot faulty data.
- **Reports**: A summary JSON report is generated after every run in the `outputs/` directory.
