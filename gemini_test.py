import google.generativeai as genai
import fitz  # PyMuPDF
import os
from PIL import Image
from dotenv import load_dotenv
import json
import glob


# Load API Key
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Google Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")  # Vision model for images


def convert_pdf_to_images(pdf_path, output_folder="pdf_images"):
    """Converts each page of a PDF into an image and saves it (without Poppler)."""
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


def load_image(image_path):
    """Loads an image from a file."""
    return Image.open(image_path)


n = 10
perf_matrix = 0.9
sid = "id12366969"


def get_image_description(image_paths):
    """Uploads multiple images and gets descriptions from Gemini API."""
    images = [load_image(img) for img in image_paths]

    prompt = f"""You are an AI assistant that extracts multiple-choice questions (MCQs) from an uploaded PDF. Your task is to analyze the content and generate {n} QUESTIONS MCQs based on the **difficulty level** defined as {perf_matrix}, Generated questions should vary in length and context, can be both simple and complex (can also be numerical questions if applicable). The output should be in the following JSON format:
{{
    "student_id": "{sid}" # this does not change,
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
- Identify key concepts and generate {n} relevant MCQs.
- Ensure **each question has exactly 4 answer options**.
- Provide the **correct answer** as one of the options.
- difficulty level is defined by the number ranging from 0 => Super easy, to 1 => Highest level and 0.5 being normal level questions.
- Assign an appropriate **topic** to each question based on the content.
- Format the response **strictly as valid JSON**.
- Do **not** include explanations or extra text outside the JSON."""

    response = model.generate_content([prompt] + images)

    # CREATING JSON FILE
    s1 = response.text.replace("```json\n", "")
    s2 = s1.replace("```", "")
    x = json.loads(s2)
    with open('output.json', 'w') as outfile:
        json.dump(x, outfile, indent=2)
    return "DUMPED"


def cleanup_images():
    img_files = glob.glob('pdf_images/*.jpg')
    for img_file in img_files:
        try:
            os.remove(img_file)
            print(f"Deleted {img_file}")
        except Exception as e:
            print(f"Error deleting {img_file}: {e}")


if __name__ == "__main__":
    pdf_file = "file3.pdf"  # Replace with your PDF file

    print("\nConverting PDF pages to images...")
    image_files = convert_pdf_to_images(pdf_file)

    if not image_files:
        print("No images generated from the PDF.")
    else:
        print(f"Processing {len(image_files)} images with Gemini API...")
        get_image_description(image_files)

    cleanup_images()
