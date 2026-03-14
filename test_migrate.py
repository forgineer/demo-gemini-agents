from google import genai
from google.genai import types
import os

# 1. Initialize the client
# Make sure your API key is set in your environment: 
# export GOOGLE_API_KEY='your_key_here'
client = genai.Client()

def convert_logic(source_code):
    system_prompt = (
        "You are an expert migration engineer. Convert the provided dynamic "
        "logic into the target statically-typed language (e.g., Java-like syntax). "
        "You must enforce explicit type declarations. Output ONLY the converted code."
    )
    
    # 2. Call the Gemini API
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=source_code,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.1 # Low temperature for more consistent/deterministic code
        )
    )
    return response.text

# 3. Test with your snippet
if __name__ == "__main__":
    source_snippet = """
    input = myresult
    if ( myresult > 50):
        return "Pass"
    else:
        return "Fail"
    """
    
    print("--- Starting Conversion ---")
    result = convert_logic(source_snippet)
    print(result)