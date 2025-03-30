from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import base64
from PIL import Image, ImageOps

client = genai.Client()
# Change this to the desired subject


# GRADIENT BANNER
# contents = (f"""Generate a modern, minimalistic, and clutter-free, banner for {subject}. Use a muted, eye-soothing color palette with soft gradients or subtle textures to create a calming and professional aesthetic. Avoid bright or overly vibrant colors.
# Incorporate small, hand-drawn doodles (outline-style illustrations) related to {subject}, scattered evenly across the banner. These doodles should be arranged in a structured yet natural way, ensuring a balanced composition with ample negative space for a clean look.
# The final design should be well-organized, visually harmonious, and should not include any text or logos. Maintain a wide, rectangular aspect ratio suitable for use as a website or digital banner""")

# HAND-DRAWN DOODLE BANNER


def generate_banner(subject):
    light_img = None
    Dark_img = None
    light = (f"""Generate a 1000x250 pixel banner for {subject}, featuring a cartoony, hand-drawn doodle style. Use a muted, pastel-based color palette for a soft, inviting look. Avoid overly bright or saturated colors to maintain a soothing and visually pleasing design.

 The background should include scattered, hand-drawn doodles related to {subject}, evenly distributed across the banner. These doodles should have a sketch-like, freehand style—simple outlines with slight variations to give a natural, artistic feel. Maintain a clean and uncluttered composition with balanced negative space.

 Prominently display the subject name "{subject}" in a playful, hand-drawn or slightly rounded font that complements the doodle style. Ensure the text is clear, well-integrated into the design, and does not overpower the background elements.

 The final design should follow a 1000x250 aspect ratio, making it suitable for use as a digital or website banner.""")

# HAND-DRAWN DOODLE BANNER (dark mode)
    dark = (f"""Generate a 1024x256 pixel dark mode banner for {subject}, featuring a cartoony, hand-drawn doodle style. The background should be a dark, muted shade (such as deep gray, navy, or black) with subtle gradients or textures for depth.

Use light, pastel, or neon-like doodles and accents to contrast against the dark background while maintaining a soft, eye-soothing look. The doodles should be outline-style, scattered evenly across the banner, and related to {subject}. Ensure they follow a freehand, sketch-like aesthetic for a fun yet minimal appearance.

Prominently display the subject name "{subject}" in a complementary light color that stands out against the dark background. The font should be playful, slightly rounded, or hand-drawn to match the doodle style.

The final design should be visually balanced, with negative space to avoid clutter, and must not include any logos.""")

    response = client.models.generate_content(
        model="gemini-2.0-flash-exp-image-generation",
        contents=light,
        config=types.GenerateContentConfig(
            response_modalities=['Text', 'Image']
        )
    )

    for part in response.candidates[0].content.parts:
        if part.text is not None:
            print(part.text)
        elif part.inline_data is not None:
            image = Image.open(BytesIO((part.inline_data.data)))

            target_size = (1024, 256)
            resized_image = ImageOps.fit(
                image, target_size, method=Image.LANCZOS)

        # LIGHT IMAGE GENERATION
            light_img = resized_image

    response = client.models.generate_content(
        model="gemini-2.0-flash-exp-image-generation",
        contents=dark,
        config=types.GenerateContentConfig(
            response_modalities=['Text', 'Image']
        )
    )

    for part in response.candidates[0].content.parts:
        if part.text is not None:
            print(part.text)
        elif part.inline_data is not None:
            image = Image.open(BytesIO((part.inline_data.data)))

            target_size = (1024, 256)
            resized_image = ImageOps.fit(
                image, target_size, method=Image.LANCZOS)
            subject = subject.replace(" ", "-")

            Dark_img = resized_image
    return (light_img, Dark_img)


if __name__ == "__main__":
    subject = "Physics"
    x = generate_banner(subject)
