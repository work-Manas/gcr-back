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


def get_image_description(image_paths):
    """Uploads multiple images and gets descriptions from Gemini API."""
    images = [load_image(img) for img in image_paths]

    prompt = """Please analyze the uploaded PDF and perform the following tasks:

1.  **Summarize the content** and provide headings that accurately reflect the key topics and subtopics discussed in the document.

2.  **Generate 50 questions** based on the content of the PDF. These questions should cover a range of difficulty and focus on key concepts, definitions, procedures, and comparisons presented in the document.

3.  **Provide the output in JSON format.** The JSON structure should adhere to the following schema:

```json
{
  "summary": [
    {
      "heading": "Heading 1",
      "content": "Summary of Heading 1"
    },
    {
      "heading": "Heading 2",
      "content": "Summary of Heading 2"
    },
    // ... more headings
  ],
  "questions": [
    {
      "question": "Question 1"
    },
    {
      "question": "Question 2"
    },
    // ... 50 questions
  ]
}"""

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
    pdf_file = "file.pdf"  # Replace with your PDF file

    print("\nConverting PDF pages to images...")
    image_files = convert_pdf_to_images(pdf_file)

    if not image_files:
        print("No images generated from the PDF.")
    else:
        print(f"Processing {len(image_files)} images with Gemini API...")
        summary = get_image_description(image_files)
        print("\n--- PDF Summary ---\n")
        print(summary)

    cleanup_images()
