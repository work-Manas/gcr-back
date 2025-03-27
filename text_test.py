n = 1
perf_matrix = 0.5
prompt = f"""You are an AI assistant that extracts multiple-choice questions (MCQs) from an uploaded PDF. Your task is to analyze the content and generate {n} QUESTIONS MCQs based on the **difficulty level** defined by {perf_matrix}, Generated questions should vary in length and context, can be both simple and complex (can also be numerical questions if applicable). The output should be in the following JSON format:
{{
    "student_id": "<student_id>",
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

### **Instructions:**
- Analyze the content of the provided PDF.
- Identify key concepts and generate `N` relevant MCQs.
- Ensure **each question has exactly 4 answer options**.
- Provide the **correct answer** as one of the options.
- difficulty level is defined by the number ranging from 0 => Super easy, to 1 => Highest level and 0.5 being normal level questions.
- Assign an appropriate **topic** to each question based on the content.
- Format the response **strictly as valid JSON**.
- Do **not** include explanations or extra text outside the JSON."""

print(prompt)
