import random
import string
import json
import os


def load_existing_codes(storage_file='generated_codes.json'):
    """Load previously generated codes from storage file."""
    if os.path.exists(storage_file):
        try:
            with open(storage_file, 'r') as file:
                return json.load(file)
        except json.JSONDecodeError:
            return []
    return []


def save_codes(codes, storage_file='generated_codes.json'):
    """Save the list of generated codes to the storage file."""
    with open(storage_file, 'w') as file:
        json.dump(codes, file)


def generate_unique_code(generated_codes=None, storage_file='generated_codes.json'):
    """Generate a unique 9-letter code in the format xxx-xxx-xxx."""
    # Load existing codes if not provided
    if generated_codes is None:
        generated_codes = load_existing_codes(storage_file)

    # Generate a new unique code
    while True:
        # Generate three groups of 3 random letters and numbers
        chars = string.ascii_uppercase + string.digits
        group1 = ''.join(random.choice(chars) for _ in range(3))
        group2 = ''.join(random.choice(chars) for _ in range(3))
        group3 = ''.join(random.choice(chars) for _ in range(3))

        # Format the code
        code = f"{group1}-{group2}-{group3}"

        # Check if this code has been generated before
        if code not in generated_codes:
            generated_codes.append(code)
            save_codes(generated_codes, storage_file)
            return code


# Example usage
if __name__ == "__main__":
    # Load previously generated codes
    all_codes = load_existing_codes()

    # Generate a new unique code
    new_code = generate_unique_code(all_codes)
    print(f"Generated new code: {new_code}")

    # How many codes have been generated so far
    print(f"Total generated codes: {len(all_codes)}")
