from langchain_google_genai import ChatGoogleGenerativeAI
import getpass
import os
from PIL import Image

if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = getpass.getpass(
        "Enter your Google AI API key: ")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    # other params...
)


def load_image(image_path):
    """Load an image from the specified path."""
    try:
        return Image.open(image_path)
    except Exception as e:
        print(f"Error loading image: {e}")
        return None


# Load the initial image
current_image = Image.open("imgtest.png")
messages = [
    (
        "system",
        "You are an image AI assistant that generates text descriptions from uploaded images. your task is to answer the questions based on the image uploaded",
    )
]

# Correct format for multimodal input
content = [
    {"type": "text", "text": messages[0][1]},
    {"type": "image", "image": current_image}
]
ai_msg = llm.invoke({"content": content})
print(ai_msg.content)

print("\nImage has been uploaded. You can now ask questions about it.")

while True:
    user_input = input(
        "Enter your question about the image (or 'exit' to quit): ")

    # Check if the user wants to exit
    if user_input.lower() == 'exit':
        break

    # Send the question along with the already loaded image
    content = [
        {"type": "text", "text": user_input},
        {"type": "image", "image": current_image}
    ]
    ai_msg = llm.invoke({"content": content})
    print(ai_msg.content)
