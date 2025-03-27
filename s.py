from langchain_google_genai import ChatGoogleGenerativeAI
import os
from PIL import Image
from langchain_core.messages import HumanMessage, SystemMessage
import base64
from io import BytesIO
import fitz  # PyMuPDF
import json
import glob
import time
from dotenv import load_dotenv
# Load API Key
load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
    max_tokens=None,
    timeout=None,
    # other params...
)


def load_image(image_path):
    """Load an image from the specified path."""
    return Image.open(image_path)


def image_to_base64(image):
    """Convert a PIL Image to a base64 encoded string."""
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')


def convert_pdf_to_images(pdf_path, output_folder="pdf_images"):
    """Converts each page of a PDF into an image and saves it."""
    os.makedirs(output_folder, exist_ok=True)

    doc = fitz.open(pdf_path)
    image_paths = []

    for page_number in range(len(doc)):
        page = doc[page_number]
        pix = page.get_pixmap()  # Render page as an image

        img_path = os.path.join(output_folder, f"page_{page_number+1}.jpg")
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img.save(img_path, "JPEG")
        image_paths.append(img_path)

    return image_paths


def cleanup_images():
    """Delete temporary image files."""
    img_files = glob.glob('pdf_images/*.jpg')
    for img_file in img_files:
        os.remove(img_file)


def prepare_image_contents(image_paths):
    """Convert images to base64 format for API consumption."""
    image_contents = []
    for img_path in image_paths:
        img = load_image(img_path)
        img_base64 = image_to_base64(img)
        image_contents.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}
        })
    return image_contents


def generate_questions(image_contents, n, perf_matrix, sid="id12366969"):
    """Generate questions using preprocessed image contents."""

    # Create the prompt text
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

    # Combine text prompt with images
    content = [{"type": "text", "text": prompt_text}] + image_contents

    # Create messages for LangChain
    system_message = SystemMessage(
        content="You are an AI assistant that generates multiple-choice questions from PDF content.")
    human_message = HumanMessage(content=content)

    # Get response
    ai_msg = llm.invoke([system_message, human_message])

    # Process the response to extract JSON
    response_text = ai_msg.content
    clean_json = response_text.replace(
        "```json", "").replace("```", "").strip()

    # Parse and save JSON
    json_data = json.loads(clean_json)
    with open('output.json', 'a') as outfile:
        json.dump(json_data, outfile, indent=2)
    return json_data


if __name__ == "__main__":
    # Sample student, n, performance data
    students = [["id12366969", 10, 0.8], [
        "id12366970", 15, 0.6], ["id12366971", 20, 0.4]]

    # Get PDF file from user
    pdf_file = "file3.pdf"

    # Convert PDF to images
    image_files = convert_pdf_to_images(pdf_file)

    # Process images once
    print("Processing images...")
    image_contents = prepare_image_contents(image_files)

    init_time = time.time()
    for student in students:
        individual_time = time.time()
        sid, n, perf_matrix = student

        print(f"Generating {n} questions for student {sid}...")
        questions = generate_questions(image_contents, n, perf_matrix, sid)
        print("Questions generated successfully.")
        print(
            f"time taken for {sid}: {time.time() - individual_time:.2f} seconds")
    # Clean up temporary files
    cleanup_images()
print(f"Total time taken: {time.time() - init_time:.2f} seconds")
