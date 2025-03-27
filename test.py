import os
import google.generativeai as genai  # Ensure you have this installed

# Replace with your actual Gemini API key
GOOGLE_API_KEY = "AIzaSyDnXj-PvUdpZwQ-FGueg_xB-_IcJTBGr40"
genai.configure(api_key=GOOGLE_API_KEY)

# Set up the model
# Or use 'gemini-pro-vision' if you need image input
model = genai.GenerativeModel('gemini-2.0-flash')


def chat_with_gemini(prompt):
    """Sends a prompt to the Gemini model and prints the response."""
    try:
        response = model.generate_content(prompt)
        print(response.text)
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Main loop for the terminal chatbot."""
    print("Welcome to the Gemini Terminal Chatbot!")
    print("Type 'exit' to quit.")

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        chat_with_gemini(user_input)


if __name__ == "__main__":
    main()
