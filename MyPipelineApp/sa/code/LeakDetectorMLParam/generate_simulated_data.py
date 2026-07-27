import random
import csv

print("Starting enhanced data generation script with pipeline parameter simulation...")

# --- Physical Parameter Ranges (MUST TUNE THESE!) ---
PARAM_LENGTH_MIN_M = 3.0  # Min pipeline length
PARAM_LENGTH_MAX_M = 15.0  # Max pipeline length

PARAM_DIAMETER_MIN_M = 0.020  # Min pipe inner diameter (e.g., 20mm)
PARAM_DIAMETER_MAX_M = (
    0.040  # Max pipe inner diameter (e.g., 40mm) - Large changes have big effects!
)

# Representing fittings/roughness - simplified K-factor sum
PARAM_K_FACTOR_SUM_MIN = 1.0  # Represents few/smooth fittings/pipe
PARAM_K_FACTOR_SUM_MAX = 8.0  # Represents many/sharp fittings/rough pipe

# --- Flow Simulation Parameters (Base potential before resistance scaling) ---
POTENTIAL_FLOW_MIN_LPS = 0.060  # Base minimum flow if resistance was low
POTENTIAL_FLOW_MAX_LPS = 0.180  # Base maximum flow if resistance was low
# Other flow simulation params
SIM_SENSOR_NOISE_LPS = 0.003
SIM_PINHOLE_LEAK_AMOUNT_LPS = (
    0.015  # Kept constant for simplicity (relative % will change)
)
SIM_MEDIUM_LEAK_AMOUNT_LPS = 0.040
SIM_BURST_LEAK_AMOUNT_LPS = 0.100
NEAR_ZERO_FLOW_LPS = 0.001
STABLE_DRIFT_RATE_LPS = 0.0005
FLUCTUATING_DRIFT_RATE_LPS = 0.0025
NO_FLOW_TARGET_LPS = 0.0

# --- Timeline / State Change Parameters ---
NUM_CONFIGURATIONS = 25  # Simulate this many different pipeline setups
STEPS_PER_CONFIGURATION = 4000  # Simulate this many steps for each setup
# Total Samples = NUM_CONFIGURATIONS * STEPS_PER_CONFIGURATION
# (e.g., 25 * 4000 = 100,000 samples)

STATE_DURATION_RANGES = {  # Same duration ranges for states
    "No_Flow": (60, 300),
    "Normal_Stable": (120, 600),
    "Normal_Fluctuating": (90, 400),
    "Pinhole_Leak_12": (60, 240),
    "Pinhole_Leak_23": (60, 240),
    "Medium_Leak_12": (50, 180),
    "Medium_Leak_23": (50, 180),
    "Burst_Leak_12": (15, 60),
    "Burst_Leak_23": (15, 60),
    "Sensor_1_Zero": (30, 120),
    "Sensor_2_Zero": (30, 120),
    "Sensor_3_Zero": (30, 120),
}
# --- Simulation Modes ---
MODE_LABELS = [
    "No_Flow",
    "Normal_Stable",
    "Normal_Fluctuating",
    "Pinhole_Leak_12",
    "Pinhole_Leak_23",
    "Medium_Leak_12",
    "Medium_Leak_23",
    "Burst_Leak_12",
    "Burst_Leak_23",
    "Sensor_1_Zero",
    "Sensor_2_Zero",
    "Sensor_3_Zero",
]


# --- Helper Functions ---
def add_noise_py(value, noise_amplitude_lps):
    noise = random.uniform(-noise_amplitude_lps, noise_amplitude_lps)
    return max(0.0, value + noise)


def get_random_duration(state_label):
    if state_label in STATE_DURATION_RANGES:
        min_d, max_d = STATE_DURATION_RANGES[state_label]
        return random.randint(min_d, max_d)
    else:
        return random.randint(50, 150)


# ================================================================
# --- Main Data Generation Loop ---
# ================================================================
output_filename = "simulated_leak_data_pipeline_params.csv"
all_data = []
total_steps_processed = 0

print(f"Simulating {NUM_CONFIGURATIONS} pipeline configurations...")
print(
    f"({STEPS_PER_CONFIGURATION} steps per config, total approx {NUM_CONFIGURATIONS * STEPS_PER_CONFIGURATION} samples)"
)

for config_idx in range(NUM_CONFIGURATIONS):
    # --- 1. Select Parameters for this Configuration ---
    current_length_m = random.uniform(PARAM_LENGTH_MIN_M, PARAM_LENGTH_MAX_M)
    # Diameter has a large impact - maybe skew towards middle slightly? Or just uniform.
    current_diameter_m = random.uniform(PARAM_DIAMETER_MIN_M, PARAM_DIAMETER_MAX_M)
    current_k_factor_sum = random.uniform(
        PARAM_K_FACTOR_SUM_MIN, PARAM_K_FACTOR_SUM_MAX
    )

    # --- 2. Calculate Simplified Resistance & Flow Scaling ---
    # Very rough resistance proxy - combining length, diameter^power, K factors
    # Coefficients here are arbitrary, adjust magnitude if scaling is too much/little
    # Diameter has huge effect (e.g., Darcy-Weisbach uses ~D^5), Hazen ~D^4.87
    try:
        resistance_proxy = (
            current_length_m / (current_diameter_m**4.8)
        ) * 0.01 + current_k_factor_sum * 0.1
    except OverflowError:  # Handle potential extreme values if diameter is tiny
        resistance_proxy = 100.0  # Assign a high resistance if calculation fails

    # Apply a scaling factor based on resistance (e.g., inverse relationship)
    # Increase multiplier (e.g., 0.05) for resistance to have *more* effect
    # Decrease multiplier for resistance to have *less* effect
    flow_scaling_factor = 1.0 / (1.0 + resistance_proxy * 0.05)
    # Clamp the scaling factor to avoid extreme results
    flow_scaling_factor = max(
        0.15, min(flow_scaling_factor, 1.0)
    )  # Ensure flow doesn't become zero or > potential

    # Calculate the *actual* flow range for *this* configuration
    current_sim_min_lps = POTENTIAL_FLOW_MIN_LPS * flow_scaling_factor
    current_sim_max_lps = POTENTIAL_FLOW_MAX_LPS * flow_scaling_factor

    print(f"\n--- Config {config_idx+1}/{NUM_CONFIGURATIONS} ---")
    print(
        f"  Length: {current_length_m:.2f}m, Diameter: {current_diameter_m*1000:.1f}mm, K_Sum: {current_k_factor_sum:.2f}"
    )
    print(
        f"  ResistanceProxy: {resistance_proxy:.3f}, FlowScaleFactor: {flow_scaling_factor:.3f}"
    )
    print(
        f"  Scaled Flow Range (LPS): {current_sim_min_lps:.4f} - {current_sim_max_lps:.4f}"
    )

    # --- 3. Simulate Time Steps for this Configuration ---
    current_state_label = "No_Flow"
    current_state_duration = get_random_duration(current_state_label)
    steps_in_current_state = 0
    current_base_flow_LPS = NO_FLOW_TARGET_LPS + random.uniform(
        0, SIM_SENSOR_NOISE_LPS * 2
    )
    config_step = 0

    while config_step < STEPS_PER_CONFIGURATION:
        # --- Determine if State Change is Needed ---
        if steps_in_current_state >= current_state_duration:
            previous_state = current_state_label
            possible_next_states = [s for s in MODE_LABELS if s != current_state_label]
            current_state_label = random.choice(possible_next_states)
            current_state_duration = get_random_duration(current_state_label)
            steps_in_current_state = 0

        # --- Simulate Base Flow Behavior using SCALED ranges ---
        target_base_flow = current_base_flow_LPS  # Start with current flow

        if current_state_label == "No_Flow":
            diff = NO_FLOW_TARGET_LPS - current_base_flow_LPS
            current_base_flow_LPS += (diff * 0.1) + random.uniform(
                -STABLE_DRIFT_RATE_LPS / 5, STABLE_DRIFT_RATE_LPS / 5
            )
            target_base_flow = max(0.0, current_base_flow_LPS)

        elif current_state_label == "Normal_Stable":
            drift = random.uniform(-STABLE_DRIFT_RATE_LPS, STABLE_DRIFT_RATE_LPS)
            current_base_flow_LPS += drift
            # Use SCALED min/max for bounds
            current_base_flow_LPS = max(
                current_sim_min_lps * 0.8,
                min(current_base_flow_LPS, current_sim_max_lps * 1.1),
            )
            target_base_flow = current_base_flow_LPS

        elif current_state_label == "Normal_Fluctuating":
            drift = random.uniform(
                -FLUCTUATING_DRIFT_RATE_LPS, FLUCTUATING_DRIFT_RATE_LPS
            )
            current_base_flow_LPS += drift
            if random.random() < 0.05:
                # Nudge towards random point within the SCALED range
                target_nudge = random.uniform(current_sim_min_lps, current_sim_max_lps)
                current_base_flow_LPS += (target_nudge - current_base_flow_LPS) * 0.1
            # Use SCALED min/max for bounds
            current_base_flow_LPS = max(
                current_sim_min_lps * 0.8,
                min(current_base_flow_LPS, current_sim_max_lps * 1.1),
            )
            target_base_flow = current_base_flow_LPS

        elif "Leak" in current_state_label or "Sensor" in current_state_label:
            # Assume stable flow behaviour during leaks/sensor fails, constrained by SCALED bounds
            drift = random.uniform(-STABLE_DRIFT_RATE_LPS, STABLE_DRIFT_RATE_LPS)
            current_base_flow_LPS += drift
            current_base_flow_LPS = max(
                current_sim_min_lps * 0.8,
                min(current_base_flow_LPS, current_sim_max_lps * 1.1),
            )
            target_base_flow = current_base_flow_LPS

        target_base_flow = max(0.0, target_base_flow)

        # --- Calculate True (Pre-Noise, Pre-Failure) Flows for this step ---
        trueF1 = target_base_flow
        trueF2 = target_base_flow
        trueF3 = target_base_flow

        # Apply leak subtractions (using constant absolute leak amounts)
        leak_amount = 0.0
        if "Pinhole" in current_state_label:
            leak_amount = SIM_PINHOLE_LEAK_AMOUNT_LPS
        if "Medium" in current_state_label:
            leak_amount = SIM_MEDIUM_LEAK_AMOUNT_LPS
        if "Burst" in current_state_label:
            leak_amount = SIM_BURST_LEAK_AMOUNT_LPS

        if "_Leak_12" in current_state_label:
            trueF2 = max(0.0, trueF1 - leak_amount)
            trueF3 = trueF2
        elif "_Leak_23" in current_state_label:
            trueF3 = max(0.0, trueF2 - leak_amount)

        # --- Apply Sensor Failures (Force to Near-Zero) BEFORE Noise ---
        f1_in = NEAR_ZERO_FLOW_LPS if current_state_label == "Sensor_1_Zero" else trueF1
        f2_in = NEAR_ZERO_FLOW_LPS if current_state_label == "Sensor_2_Zero" else trueF2
        f3_in = NEAR_ZERO_FLOW_LPS if current_state_label == "Sensor_3_Zero" else trueF3

        # --- Apply Noise ---
        noisyF1 = add_noise_py(f1_in, SIM_SENSOR_NOISE_LPS)
        noisyF2 = add_noise_py(f2_in, SIM_SENSOR_NOISE_LPS)
        noisyF3 = add_noise_py(f3_in, SIM_SENSOR_NOISE_LPS)

        # --- Record Data including Parameters ---
        # ORDER: timestamp, flow1, flow2, flow3, LENGTH, DIAMETER, K_SUM, label
        all_data.append(
            [
                total_steps_processed,  # Global timestamp
                noisyF1,
                noisyF2,
                noisyF3,
                current_length_m,  # Parameter 1
                current_diameter_m,  # Parameter 2
                current_k_factor_sum,  # Parameter 3
                current_state_label,  # Label
            ]
        )

        # --- Advance Time ---
        config_step += 1
        steps_in_current_state += 1
        total_steps_processed += 1

    # Optional: Print progress message
    if (config_idx + 1) % 5 == 0 or (config_idx + 1) == NUM_CONFIGURATIONS:
        print(f"  ... finished simulation for configuration {config_idx + 1}.")

# --- Save to CSV ---
print(f"\nSaving {len(all_data)} data points to {output_filename}...")
with open(output_filename, "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    # Write header including new parameter columns
    writer.writerow(
        [
            "timestamp",
            "flowRate1",
            "flowRate2",
            "flowRate3",
            "pipelineLength",
            "pipeDiameter",
            "kFactorSum",  # New Columns
            "label",
        ]
    )
    writer.writerows(all_data)

print("Enhanced data generation complete.")
print(f"Total Steps Simulated: {total_steps_processed}")
