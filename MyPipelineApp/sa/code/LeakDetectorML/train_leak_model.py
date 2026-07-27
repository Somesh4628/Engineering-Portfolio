import pandas as pd
import numpy as np
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import (  # noqa: F401
    LabelEncoder,
    StandardScaler,
)  # StandardScaler optional
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt  # Optional: for visualizing history  # noqa: F401

print(f"Using TensorFlow version: {tf.__version__}")

# --- Configuration ---
INPUT_CSV = "simulated_leak_data_pipeline_params"
MODEL_SAVE_PATH = "leak_detection_model.h5"
TFLITE_SAVE_PATH = "model.tflite"
VALIDATION_SPLIT = 0.2  # Use 20% of training data for validation during training
TEST_SPLIT = 0.15  # Hold back 15% of total data for final testing

# === 1. Load and Prepare Data ===
print(f"Loading data from {INPUT_CSV}...")
df = pd.read_csv(INPUT_CSV)

# Basic check
if df.isnull().sum().sum() > 0:
    print("Warning: Missing values found. Consider imputation or dropping rows.")
    # df = df.dropna() # Example: drop rows with missing values

print("Data loaded. Calculating features...")

# === 2. Feature Engineering (MUST MATCH ESP32 get_ml_features) ===
# Calculate differences
df["Diff12"] = df["flowRate1"] - df["flowRate2"]
df["Diff23"] = df["flowRate2"] - df["flowRate3"]
df["TotalDif"] = df["flowRate1"] - df["flowRate3"]

# Calculate Rate of Change (requires looking at previous row)
# Sort by timestamp first to be sure
df = df.sort_values(by="timestamp")
# Calculate change from previous time step. Fill first value with 0.
df["TotalDiff_prev"] = df["TotalDif"].shift(1)
df["DiffChange"] = (df["TotalDif"] - df["TotalDiff_prev"]).fillna(0)

# *** Define YOUR Feature List ***
# This list MUST match the order and content of get_ml_features in C++
# and the value used for ML_FEATURE_COUNT
FEATURE_COLUMNS = [
    "flowRate1",
    "flowRate2",
    "flowRate3",
    "TotalDif",
    "DiffChange",
    # Add/remove other features: 'Diff12', 'Diff23', moving averages, std devs etc.
]
TARGET_COLUMN = "label"

print(f"Using features: {FEATURE_COLUMNS}")
X = df[FEATURE_COLUMNS].values
y_labels = df[TARGET_COLUMN].values

# Encode labels (Strings to Integers 0, 1, 2...)
label_encoder = LabelEncoder()
y = label_encoder.fit_transform(y_labels)
num_classes = len(label_encoder.classes_)
print(f"Found {num_classes} unique classes:")
# Print the mapping - CRITICAL for setting ML_CLASS_NAMES in ESP32 code
label_mapping = dict(
    zip(label_encoder.classes_, label_encoder.transform(label_encoder.classes_))
)
print(label_mapping)

# === 3. Split Data ===
# Split into Training + Validation combined, and Test set
X_train_val, X_test, y_train_val, y_test = train_test_split(
    X,
    y,
    test_size=TEST_SPLIT,
    random_state=42,
    stratify=y,  # Stratify helps keep class proportions
)
# Split Training + Validation into separate sets (used by model.fit)
# X_train, X_val, y_train, y_val = train_test_split(
#     X_train_val, y_train_val, test_size=VALIDATION_SPLIT / (1.0 - TEST_SPLIT), # Adjust split ratio
#     random_state=42, stratify=y_train_val
# )
print(f"Data split: Train+Val={len(X_train_val)}, Test={len(X_test)}")

# === 4. (Optional) Scale Features ===
# scaler = StandardScaler()
# X_train_val = scaler.fit_transform(X_train_val) # Fit only on training+val data
# X_test = scaler.transform(X_test) # Transform test data
# print("Features scaled.")
# If using scaler, you'd need to save it and potentially implement scaling on ESP32

# === 5. Build the Keras Model ===
print("Building Keras model...")
model = tf.keras.models.Sequential(
    [
        tf.keras.layers.InputLayer(
            input_shape=(len(FEATURE_COLUMNS),)
        ),  # Input layer matching feature count
        tf.keras.layers.Dense(16, activation="relu"),  # Hidden layer 1 (tune neurons)
        tf.keras.layers.Dense(8, activation="relu"),  # Hidden layer 2 (tune neurons)
        # tf.keras.layers.Dropout(0.2), # Optional: helps prevent overfitting
        tf.keras.layers.Dense(
            num_classes, activation="softmax"
        ),  # Output layer: Neurons = classes, softmax for classification
    ]
)

model.compile(
    optimizer="adam",
    loss="sparse_categorical_crossentropy",  # Use this loss for integer labels
    metrics=["accuracy"],
)

model.summary()

# === 6. Train the Model ===
print("Training model...")
EPOCHS = 50  # Adjust as needed
BATCH_SIZE = 32  # Adjust as needed

# Using validation_split argument within fit is often easier than manual split
history = model.fit(
    X_train_val,
    y_train_val,
    epochs=EPOCHS,
    batch_size=BATCH_SIZE,
    validation_split=VALIDATION_SPLIT,  # Use built-in split based on X_train_val
    callbacks=[
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=10, restore_best_weights=True
        )  # Stop if validation loss doesn't improve
    ],
    verbose=2,
)  # Set to 1 for progress bar, 0 for silent

print("Training complete.")

# === 7. Evaluate the Model ===
print("Evaluating model on test data...")
test_loss, test_acc = model.evaluate(X_test, y_test, verbose=0)
print(f"\nTest accuracy: {test_acc*100:.2f}%")
print(f"Test loss: {test_loss:.4f}")

# Detailed report
print("\nClassification Report:")
y_pred_probabilities = model.predict(X_test)
y_pred = np.argmax(
    y_pred_probabilities, axis=1
)  # Get class index with highest probability
print(classification_report(y_test, y_pred, target_names=label_encoder.classes_))

print("\nConfusion Matrix:")
print(
    pd.DataFrame(
        confusion_matrix(y_test, y_pred),
        index=label_encoder.classes_,
        columns=label_encoder.classes_,
    )
)

# === 8. Convert to TensorFlow Lite ===
print(f"\nConverting model to TFLite format ({TFLITE_SAVE_PATH})...")
converter = tf.lite.TFLiteConverter.from_keras_model(model)
# --- Optional: Add optimizations for TFLite ---
# converter.optimizations = [tf.lite.Optimize.DEFAULT]
# converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS] # Or include SELECT_TF_OPS if needed
# Potentially add quantization (reduces size but can impact accuracy)
# converter.representative_dataset = lambda: representative_data_generator(X_train) # Need a generator function
# converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
# converter.inference_input_type = tf.int8  # or tf.uint8
# converter.inference_output_type = tf.int8 # or tf.uint8
# --- End Optimizations ---

tflite_model = converter.convert()

# Save the TFLite model file
with open(TFLITE_SAVE_PATH, "wb") as f:
    f.write(tflite_model)
print(
    f"TFLite model saved successfully to {TFLITE_SAVE_PATH} ({len(tflite_model)} bytes)"
)

print("\nNEXT STEPS:")
print(
    f"1. Use 'xxd -i {TFLITE_SAVE_PATH} > model_data.cc' (or similar tool) to create the C array."
)
print("2. Copy the array into your ESP32 code, replacing the placeholder.")
print(
    f"3. Update ML_FEATURE_COUNT ({len(FEATURE_COLUMNS)}), ML_OUTPUT_CLASSES ({num_classes}), and ML_CLASS_NAMES in ESP32 code based on the label mapping printed above."
)
print(
    "4. Ensure ESP32's get_ml_features() calculates features in the *exact same order*."
)
print("5. Adjust kTensorArenaSize in ESP32 code if needed.")
print("6. Test thoroughly!")

# Optional: Plot training history
# plt.figure()
# plt.plot(history.history['accuracy'], label='accuracy')
# plt.plot(history.history['val_accuracy'], label = 'val_accuracy')
# plt.xlabel('Epoch')
# plt.ylabel('Accuracy')
# plt.ylim([0, 1])
# plt.legend(loc='lower right')
# plt.show()
