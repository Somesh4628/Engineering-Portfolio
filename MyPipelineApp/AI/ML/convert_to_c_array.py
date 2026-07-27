# convert_to_c_array.py (FINAL, BEDROCK v2.0)
# This script reads a binary file (e.g., model.tflite) and converts
# it to a C-style array in a .h header file. It is a robust replacement
# for the command-line 'xxd' utility.


# --- Configuration ---
# You can change these filenames if you need to convert other files.
MODEL_TFLITE = "model.tflite"
MODEL_H = "model.h"
VAR_NAME = "g_model"
# ---------------------


def create_c_array():
    """
    Reads the binary input file and writes the C header file.
    This is the definitive, failsafe implementation.
    """
    try:
        # Read the entire binary model file.
        with open(MODEL_TFLITE, "rb") as f:
            tflite_content = f.read()
    except FileNotFoundError:
        print(f"\nFATAL ERROR: Input file '{MODEL_TFLITE}' not found.")
        print(
            "Please ensure the model has been successfully quantized and exported from your training script."
        )
        return

    model_len = len(tflite_content)
    print(f"Read '{MODEL_TFLITE}' ({model_len} bytes). Converting to C array...")

    # Start building the C code using a list of strings for absolute safety.
    c_lines = []

    # Add a header guard for professional C++ practice
    c_lines.append(f"#ifndef {VAR_NAME.upper()}_H_")
    c_lines.append(f"#define {VAR_NAME.upper()}_H_")
    c_lines.append("")

    c_lines.append("// TFLite Model, converted to a C array using a Python script.")
    c_lines.append(f"// Model Length: {model_len} bytes")

    # Define the length variable as a constant expression.
    c_lines.append(f"const unsigned int {VAR_NAME}_len = {model_len};")
    c_lines.append("")  # Add a blank line for readability

    # Define the array with alignment for performance on embedded systems.
    c_lines.append(f"const unsigned char {VAR_NAME}[] __attribute__((aligned(4))) = {{")

    # Build the hex data lines
    hex_line = "  "
    for i, byte in enumerate(tflite_content):
        # Append hex value
        hex_line += "0x{:02x}, ".format(byte)

        # Create a new line every 12 bytes for readability
        if (i + 1) % 12 == 0:
            c_lines.append(hex_line)
            hex_line = "  "

    # Add any remaining hex values from the last line
    if hex_line.strip() != "":
        # Remove the trailing comma and space from the very last value
        c_lines.append(hex_line.strip()[:-1])

    # Add the final closing brace and semicolon for the array.
    c_lines.append("};")
    c_lines.append("")
    c_lines.append(f"#endif // {VAR_NAME.upper()}_H_")

    # --- Write the final file ---
    try:
        with open(MODEL_H, "w") as f:
            f.write("\n".join(c_lines))
        print(f"\n✅ SUCCESS! C-array written to '{MODEL_H}'.")
        print("   This is the final artifact for Sub-Step 6.B.")
    except Exception as e:
        print(f"\nFATAL ERROR: Could not write to '{MODEL_H}'. Error: {e}")


if __name__ == "__main__":
    create_c_array()
