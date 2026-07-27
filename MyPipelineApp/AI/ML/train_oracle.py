import os
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow import keras
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import argparse
import textwrap
import json


# ==============================================================================
#  HELPER FUNCTION (Replaces XXD)
# ==============================================================================
def convert_tflite_to_c_array(tflite_model, output_path):
    """
    Converts a TFLite model binary into a C-style header file.
    This is a pure Python replacement for the 'xxd' command.
    """
    print(f"-> [Oracle] Converting TFLite model to C header file at '{output_path}'...")

    base_name = os.path.basename(output_path).replace(".h", "")
    var_name = f"g_{base_name}"  # noqa: F841

    c_code = textwrap.dedent("""
    #ifndef {base_name.upper()}_H
    #define {base_name.upper()}_H

    // Converted from a TFLite model using a Python script.
    const unsigned char {var_name}[] = {{
    """)

    line_len = 0
    for byte in tflite_model:
        if line_len == 0:
            c_code += "    "
        c_code += f"0x{byte:02x}, "
        line_len += 1
        if line_len >= 12:
            c_code += "\n"
            line_len = 0

    c_code += textwrap.dedent("""
    }};
    const unsigned int {var_name}_len = {len(tflite_model)};

    #endif // {base_name.upper()}_H
    """)

    with open(output_path, "w") as f:
        f.write(c_code)
    print("-> [Oracle] C header file saved successfully.")


# ==============================================================================
#  MAIN TRAINING & CONVERSION LOGIC
# ==============================================================================
def main(args):
    # --- 1. DATA LOADING AND PREPARATION ---
    print("--> [1/5] Ingesting Engineered Feature Data...")
    try:
        df = pd.read_csv(args.data_file)
        df.dropna(inplace=True)
    except FileNotFoundError:
        print(f"\nFATAL ERROR: '{args.data_file}' not found.")
        exit(1)

    X = df.iloc[:, :-1].values
    y = df.iloc[:, -1].values
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)
    print(f"      Data prepared. Training set features: {X_train.shape[1]}")

    # --- 2. MODEL ARCHITECTURE & TRAINING ---
    print("--> [2/5] Designing and Training the Enhanced Oracle...")
    CLASS_NAMES = ["Normal", "Leak", "Burst", "Clog", "Drift"]
    model = keras.Sequential(
        [
            keras.layers.InputLayer(input_shape=(X_train.shape[1],), name="input"),
            keras.layers.Dense(256, activation="relu", name="hidden_layer_1"),
            keras.layers.Dropout(0.4),
            keras.layers.Dense(128, activation="relu", name="hidden_layer_2"),
            keras.layers.Dropout(0.4),
            keras.layers.Dense(64, activation="relu", name="hidden_layer_3"),
            keras.layers.Dense(len(CLASS_NAMES), activation="softmax", name="output"),
        ]
    )
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.0005),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    model.summary()
    model.fit(
        X_train, y_train, epochs=50, batch_size=128, validation_split=0.15, verbose=0
    )
    print("Training complete.")

    # --- 3. MODEL EVALUATION ---
    print("--> [3/5] Evaluating final Oracle Performance...")
    loss, accuracy = model.evaluate(X_test, y_test, verbose=0)
    print(f"\n      Final Test Accuracy: {accuracy*100:.2f}%")

    # --- 4. TFLITE CONVERSION & QUANTIZATION ---
    print("--> [4/5] Converting and quantizing the model for firmware...")

    def representative_dataset_generator():
        for i in range(500):
            yield [X_train[i].astype(np.float32).reshape(1, -1)]

    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.representative_dataset = representative_dataset_generator
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    converter.inference_input_type = tf.int8
    converter.inference_output_type = tf.int8

    try:
        tflite_model_quant = converter.convert()
        print(
            f"      Success! Quantized model created. Size: {len(tflite_model_quant)} bytes."
        )
    except Exception as e:
        print(f"\n      FATAL TFLITE CONVERSION ERROR: {e}")
        exit(1)

    # --- 5. C-ARRAY & LABELS FILE GENERATION ---
    print("--> [5/5] Generating C header and JSON labels file...")
    convert_tflite_to_c_array(tflite_model_quant, args.output_header)

    # --- AUTOMATION UPGRADE ---
    # Create the labels filename based on the header filename
    labels_filename = args.output_header.replace(".h", ".labels.json")
    with open(labels_filename, "w") as f:
        json.dump(CLASS_NAMES, f, indent=2)
    print(f"-> [Oracle] Class labels saved to '{labels_filename}'")
    # --- END UPGRADE ---

    print("\n[OK] Oracle Final Education Complete.")
    # This final print is captured by the conductor server to confirm the output path
    print(args.output_header)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Train and convert the IntelliPipe AI model."
    )
    parser.add_argument(
        "--data-file",
        type=str,
        required=True,
        help="Path to the input training CSV file.",
    )
    parser.add_argument(
        "--output-header",
        type=str,
        required=True,
        help="Path to save the final C header file (model.h).",
    )
    args = parser.parse_args()
    main(args)
