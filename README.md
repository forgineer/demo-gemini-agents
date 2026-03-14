# demo-gemini-agents

Proof of concept for batch-migrating short dynamic logic snippets into Java-style, explicitly typed logic using the Gemini API.

The script reads rows from a pipe-delimited CSV, sends each SourceLogic value to Gemini with your project coding standards, and writes a result file with conversion output and row-level status/error details.

## What this project does

- Reads input from source.csv (or a custom file)
- Loads migration rules from coding_standards.md
- Converts each row's SourceLogic with Gemini
- Writes output to target.csv (or a custom file)
- Preserves batch progress even when individual rows fail

## Requirements

- Python 3.12+
- uv
- A Google Gemini API key in GOOGLE_API_KEY

## Install with uv

1. Clone the repo and move into it.
1. Create and sync the environment:

```powershell
uv sync
```

1. Set your API key:

```powershell
$env:GOOGLE_API_KEY = "your_api_key_here"
```

For bash/zsh:

```bash
export GOOGLE_API_KEY="your_api_key_here"
```

## Run

Default run:

```powershell
uv run python batch_migrate.py
```

Custom paths/model:

```powershell
uv run python batch_migrate.py --input source.csv --output target.csv --standards coding_standards.md --model gemini-2.5-flash
```

CLI options:

- --input: input pipe-delimited CSV path
- --output: output CSV path
- --standards: markdown file used in the system prompt
- --model: Gemini model ID

## Input format

Expected delimiter: |

Minimum useful columns:

- TestName
- SourceLogic

Example:

```text
TestName|SourceLogic
Test 1|"if (myresult > 50): return 'Pass' else: return 'Fail'"
```

## Output format

The output includes original columns plus:

- ConvertedLogic: generated migrated logic
- Status: ok or failed
- Error: failure details for the row (empty on success)

## Notes

- Retries are enabled for Gemini client errors using exponential backoff.
- If coding_standards.md is missing, the script uses a default Java best-practices instruction.
- This is a PoC. Add automated tests and stricter output validation before production use.
