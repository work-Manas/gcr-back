import base64
from io import BytesIO
import fitz  # PyMuPDF
import json
import glob
import time
import google.generativeai as genai
import os
from dotenv import load_dotenv
from PIL import Image
import concurrent.futures

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")


def convert_pdf_to_images(pdf_path, output_folder="pdf_images", dpi=72, use_threading=False, max_workers=4):
    """
    Converts each page of a PDF into an image and saves it.

    Args:
        pdf_path: Path to the PDF file
        output_folder: Directory to save images
        dpi: Resolution for the images (higher = better quality but larger files)
        use_threading: Whether to use multi-threading for faster processing
        max_workers: Maximum number of worker threads

    Returns:
        List of paths to the created images
    """
    os.makedirs(output_folder, exist_ok=True)

    doc = fitz.open(pdf_path)
    image_paths = []

    # Calculate zoom factor based on DPI (72 is the base DPI)
    zoom = dpi / 72

    def process_page(page_number):
        page = doc[page_number]
        # Get transformation matrix for better quality
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        img_path = os.path.join(output_folder, f"page_{page_number+1}.jpg")
        # Use PyMuPDF's built-in saving function instead of PIL
        pix.save(img_path)
        return img_path

    # Use threading if enabled and if there are multiple pages
    if use_threading and len(doc) > 1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Process pages in parallel
            future_to_page = {executor.submit(process_page, page_num): page_num
                              for page_num in range(len(doc))}

            # Collect results in order
            for future in concurrent.futures.as_completed(future_to_page):
                image_paths.append(future.result())

        # Sort paths by page number to maintain order
        image_paths.sort(key=lambda x: int(x.split('_')[-1].split('.')[0]))
    else:
        # Process pages sequentially
        for page_number in range(len(doc)):
            image_paths.append(process_page(page_number))

    return image_paths


def load_image(image_path):
    """Loads an image from a file."""
    return Image.open(image_path)


def cleanup_images():
    """Delete temporary image files."""
    img_files = glob.glob('pdf_images/*.jpg')
    for img_file in img_files:
        os.remove(img_file)


def generate_questions(n, perf_matrix, sid):
    images = [load_image(img) for img in image_files]

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

    response = model.generate_content([prompt_text] + images)

    # Extract JSON from response
    s1 = response.text.replace("```json\n", "")
    s2 = s1.replace("```", "")
    x = json.loads(s2)
    with open('output.json', 'a') as outfile:
        json.dump(x, outfile, indent=2)
    return "DUMPED"


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
    image_files = convert_pdf_to_images(pdf_file)
    init_time = time.time()
    for student in students:
        individual_time = time.time()
        sid, n, perf_matrix = student

        print(f"Generating {n} questions for student {sid}...")
        questions = generate_questions(n, perf_matrix, sid)
        print("Questions generated successfully.")
        print(
            f"time taken for {sid}: {time.time() - individual_time:.2f} seconds")
    # Clean up temporary files
    cleanup_images()
print(f"Total time taken: {time.time() - init_time:.2f} seconds")
