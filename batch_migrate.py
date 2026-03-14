import click
import csv
import os
from functools import lru_cache
from typing import Dict, Iterable, List

from google import genai
from google.genai.errors import ClientError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_STANDARDS = "Follow standard Java best practices."


def load_coding_standards(filepath: str = "coding_standards.md") -> str:
    """Reads the markdown file and returns it as a string."""
    if not os.path.exists(filepath):
        print(f"Warning: {filepath} not found. Proceeding with default prompt.")
        return DEFAULT_STANDARDS

    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


@lru_cache(maxsize=1)
def get_client() -> genai.Client:
    """Lazily initialize the API client so help/validation can run without API usage."""
    return genai.Client()

@retry(
    retry=retry_if_exception_type(ClientError),
    wait=wait_exponential(multiplier=5, min=15, max=120),
    stop=stop_after_attempt(4)
)
def convert_logic(source_code: str, coding_standards: str, model_id: str = DEFAULT_MODEL) -> str:
    # We dynamically inject the loaded standards into the prompt.
    system_prompt = f"""
    You are an expert migration engineer.
    Convert the provided dynamic logic into Java logic with explicit types.

    Adhere strictly to these coding standards and project rules:
    {coding_standards}

    Output ONLY the code block.
    """

    response = get_client().models.generate_content(
        model=model_id,
        contents=source_code,
        config={"system_instruction": system_prompt, "temperature": 0.1}
    )
    return (response.text or "").strip()


def _build_fieldnames(input_fieldnames: Iterable[str]) -> List[str]:
    fieldnames = list(input_fieldnames)
    for name in ["ConvertedLogic", "Status", "Error"]:
        if name not in fieldnames:
            fieldnames.append(name)
    return fieldnames


def process_batch(
    input_file: str,
    output_file: str,
    coding_standards: str,
    model_id: str = DEFAULT_MODEL
) -> Dict[str, int]:
    print(f"--- Starting migration: {input_file} ---")

    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    processed = 0
    succeeded = 0
    failed = 0

    with open(input_file, mode="r", encoding="utf-8") as infile, \
            open(output_file, mode="w", encoding="utf-8", newline="") as outfile:
        reader = list(csv.DictReader(infile, delimiter="|"))
        if not reader:
            raise ValueError("Source file is empty.")

        fieldnames = _build_fieldnames(reader[0].keys())
        writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter="|")
        writer.writeheader()

        with click.progressbar(reader, label="Migrating logic", show_eta=True) as bar:
            for row in bar:
                processed += 1
                source_logic = (row.get("SourceLogic") or "").strip()
                if not source_logic:
                    row["ConvertedLogic"] = ""
                    row["Status"] = "failed"
                    row["Error"] = "Missing SourceLogic"
                    failed += 1
                    writer.writerow(row)
                    continue

                try:
                    row["ConvertedLogic"] = convert_logic(source_logic, coding_standards, model_id)
                    row["Status"] = "ok"
                    row["Error"] = ""
                    succeeded += 1
                except ClientError as e:
                    row["ConvertedLogic"] = ""
                    row["Status"] = "failed"
                    row["Error"] = f"ClientError: {e}"
                    failed += 1
                    click.secho(f"\nAPI error for row {processed}: {e}", fg="yellow", err=True)
                except Exception as e:  # Keep the batch running while surfacing row-level failures.
                    row["ConvertedLogic"] = ""
                    row["Status"] = "failed"
                    row["Error"] = f"UnexpectedError: {e}"
                    failed += 1
                    click.secho(f"\nUnexpected error for row {processed}: {e}", fg="yellow", err=True)

                writer.writerow(row)
                outfile.flush()

    return {"processed": processed, "succeeded": succeeded, "failed": failed}


@click.command()
@click.option("--input", "input_file", default="source.csv", show_default=True, help="Input CSV path.")
@click.option("--output", "output_file", default="target.csv", show_default=True, help="Output CSV path.")
@click.option("--standards", "standards_file", default="coding_standards.md", show_default=True, help="Coding standards markdown path.")
@click.option("--model", "model_id", default=DEFAULT_MODEL, show_default=True, help="Gemini model ID.")
def main(input_file: str, output_file: str, standards_file: str, model_id: str) -> None:
    standards = load_coding_standards(standards_file)
    summary = process_batch(input_file, output_file, standards, model_id)
    click.echo(
        f"Completed migration. Processed: {summary['processed']}, "
        f"Succeeded: {summary['succeeded']}, Failed: {summary['failed']}."
    )


if __name__ == "__main__":
    main()