import click
import csv
import os
import time

from google import genai
from google.genai.errors import ClientError
from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_exponential, 
    retry_if_exception_type
)

# Initialize client
client = genai.Client()

def load_coding_standards(filepath="coding_standards.md"):
    """Reads the markdown file and returns it as a string."""
    if not os.path.exists(filepath):
        print(f"Warning: {filepath} not found. Proceeding with default prompt.")
        return "Follow standard Java best practices."
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

# Load the rules once when the script starts
CODING_STANDARDS = load_coding_standards()

@retry(
    retry=retry_if_exception_type(ClientError),
    wait=wait_exponential(multiplier=5, min=15, max=120),
    stop=stop_after_attempt(4)
)
def convert_logic(source_code):
    model_id = 'gemini-2.5-flash' 
    
    # We dynamically inject the loaded standards into the prompt
    system_prompt = f"""
    You are an expert migration engineer.
    Convert the provided dynamic logic into Java logic with explicit types.
    
    Adhere strictly to these coding standards and project rules:
    {CODING_STANDARDS}
    
    Output ONLY the code block.
    """
    
    try:
        response = client.models.generate_content(
            model=model_id,
            contents=source_code,
            config={"system_instruction": system_prompt, "temperature": 0.1}
        )
        return response.text.strip()
    except ClientError as e:
        click.secho(f"\nAPI Error: {e}", err=True)
        #print(f"\nDEBUG: API Error Detail: {e}")
        #raise e

def process_batch(input_file, output_file):
    print(f"--- Starting migration: {input_file} ---")
    
    # Check if files exist before starting
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    with open(input_file, mode='r', encoding='utf-8') as infile, \
         open(output_file, mode='w', encoding='utf-8', newline='') as outfile:
        
        reader = list(csv.DictReader(infile, delimiter='|'))
        if not reader:
            print("Source file is empty.")
            return

        fieldnames = list(reader[0].keys()) + ['ConvertedLogic']
        writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter='|')
        writer.writeheader()
        
        with click.progressbar(reader, label="Migrating logic", show_eta=True) as bar:
            for row in bar:
                try:
                    row['ConvertedLogic'] = convert_logic(row['SourceLogic'])
                    writer.writerow(row)
                    outfile.flush()
                except Exception:
                    #print(f"\nFAILED {row['TestName']}: {e}")
                    pass


if __name__ == "__main__":
    process_batch('source.csv', 'target.csv')