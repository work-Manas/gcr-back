import json
import time
from google import genai
from google.genai import types
import pathlib

# Initialize the GenAI client
client = genai.Client()


def generate_questions(file_content,  n, perf_matrix, sid):
    """
    Generates questions based on the provided file content.
    """
    # Define the prompt for generating questions
    prompt_text = f"""Using the following context from the PDF, generate {n} multiple-choice questions (MCQs) with a difficulty level of {perf_matrix}, where difficulty is rated from 0 to 1, with 0 being super easy and 1 being the highest level of difficulty.
The questions should vary in length and context, and can be both simple and complex, including numerical questions if applicable.

The output should be in the following JSON format:
{{
    "student_id": "{sid}",
    "questions": [
        {{
            "question": "<Question text>",
            "options": ["<Option 1>", "<Option 2>", "<Option 3>", "<Option 4>"],
            "answer": "<Correct Answer>",
            "topic": "<Relevant Topic>"
        }},
        ...
    ]
}}

### Instructions:
- Each question should only contain the question part: no additional information like For student <student_id>.
- Ensure each question has exactly 4 answer options.
- Provide the correct answer as one of the options.
- Difficulty level: 0 => Super easy, 1 => Highest level.
- Assign an appropriate topic to each question based on the content.
- Format the response strictly as valid JSON.
- Do not include explanations or extra text outside the JSON."""

    # Call the model to generate questions
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            types.Part.from_bytes(
                data=file_content.getvalue(),
                mime_type='application/pdf',
            ),
            prompt_text
        ]
    )
# Extract JSON from response
    s1 = response.text.replace("```json\n", "")
    s2 = s1.replace("```", "")
    x = json.loads(s2)
    # with open('output.json', 'a') as outfile:
    #    json.dump(x, outfile, indent=2)
    return x
