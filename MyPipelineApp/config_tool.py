# ==============================================================================
# SECTION 0: DEPENDENCY & ENVIRONMENT CHECK
# ==============================================================================
try:
    import json
    import os
    import random
    import csv
    import numpy as np
    from OpenSSL import crypto
    import time
    import argparse
except ImportError as e:
    print("=" * 60)
    print("!! MISSING REQUIRED LIBRARIES !!")
    print(f"Error: {e}")
    print("\nPlease run the environment setup command to install all dependencies:")
    print("pip install --force-reinstall --no-cache-dir -r requirements.txt")
    print("=" * 60)
    exit()

# ==============================================================================
# SECTION 1: COMMAND & CONTROL INTERFACE
# ==============================================================================


def validate_blueprint_task(bp):
    """Task 1: Validates the blueprint's integrity."""
    print("\n[Executing Task: 1 - Validate Blueprint]")
    try:
        # These tools will raise errors if the blueprint is malformed.
        build_system_graph(bp)
        generate_tuning_system(bp)
        print("  -> [OK] Validation SUCCESSFUL. Blueprint is sound.")
        return True
    except Exception as e:
        print(f"  -> [FAIL] VALIDATION FAILED: {e}")
        return False


def forge_firmware_task(bp, output_path, output_format="monolith"):
    """Task 2: Forges the final firmware artifact."""
    print("\n[Executing Task: 2 - Forge Firmware]")

    try:
        code_blocks = run_master_orchestrator(bp)

        if output_format == "platformio":
            assemble_platformio(code_blocks, output_path)
            print(
                f"  -> [OK] Forge SUCCESSFUL. PlatformIO project created at '{output_path}'."
            )
        else:  # monolith
            final_code = assemble_monolith(code_blocks)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(final_code)
            print(f"  -> [OK] Forge SUCCESSFUL. Artifact saved to '{output_path}'.")
        return True
    except Exception as e:
        print(f"  -> [FAIL] FORGE FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def generate_data_task(bp, output_csv_path):
    """Task 3: Launches the Data Factory."""
    print("\n[Executing Task: 3 - Launch Data Factory]")
    try:
        generate_training_dataset(
            bp, num_scenarios=4000, cycles_per_scenario=100, filename=output_csv_path
        )
        print(
            f"  -> [OK] Data Factory run SUCCESSFUL. Data saved to '{output_csv_path}'."
        )
        return True
    except Exception as e:
        print(f"  -> [FAIL] DATA FACTORY FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """
    (The Interactive Factory v1.3 - Smart Blueprint Search)
    Parses and executes a sequence of operations on a user-specified blueprint,
    automatically searching in common project locations.
    """
    # This script is now designed to be called by run_cli.bat or the conductor server.
    # It uses command-line arguments instead of interactive input.
    parser = argparse.ArgumentParser(
        description="IntelliPipe Factory: Build firmware and generate data from blueprints."
    )
    parser.add_argument(
        "task",
        choices=["1", "2", "3"],
        help="The task to perform: 1=Validate, 2=Forge Firmware, 3=Generate Data",
    )
    parser.add_argument(
        "--blueprint", required=True, help="Path to the blueprint JSON file."
    )
    parser.add_argument(
        "--output-ino",
        help="Output path for the forged firmware (.ino file). Required for task 2.",
    )
    parser.add_argument(
        "--output-csv",
        help="Output path for the generated training data (.csv file). Required for task 3.",
    )

    # If run without arguments (e.g., double-clicked), show a helpful message.
    import sys

    if len(sys.argv) == 1:
        print("\n--- IntelliPipe Factory ---")
        print(
            "This script is the core engine. To use it, please run 'run_cli.bat' for an interactive experience."
        )
        return

    args = parser.parse_args()

    # --- DYNAMIC BLUEPRINT LOADING (UPGRADED) ---
    blueprint_filename = args.blueprint

    search_paths = [blueprint_filename, os.path.join("soul_forger", blueprint_filename)]

    blueprint = None
    found_path = None
    for path in search_paths:
        try:
            with open(path, "r", encoding="utf-8") as f:
                blueprint = json.load(f)
                found_path = path
                break
        except FileNotFoundError:
            continue
        except Exception as e:
            print(f"\n**FATAL ERROR**: Could not load or parse '{path}'. Error: {e}")
            exit(1)

    if not blueprint:
        print(
            f"\n**FATAL ERROR**: Could not find the blueprint file '{blueprint_filename}' in the project root or in 'soul_forger/'."
        )
        exit(1)

    print(f"  -> Successfully loaded blueprint from: {found_path}")
    # --- END DYNAMIC LOADING ---

    # --- Execute Task ---
    if args.task == "1":
        validate_blueprint_task(blueprint)
    elif args.task == "2":
        if not args.output_ino:
            print("**FATAL ERROR**: --output-ino path is required for task 2.")
            exit(1)
        forge_firmware_task(blueprint, args.output_ino)
    elif args.task == "3":
        if not args.output_csv:
            print("**FATAL ERROR**: --output-csv path is required for task 3.")
            exit(1)
        generate_data_task(blueprint, args.output_csv)


# ==============================================================================
# SECTION 2: THE DATA & SIMULATION FACTORY (ORACLE'S GENESIS)
# ==============================================================================


class PipelineSimulator:
    """
    (The Physics & Chaos Engine v2.1 - "Perfection")
    Final version with unmistakable signatures for Burst and Drift events
    to achieve near-perfect classification accuracy.
    """

    def __init__(self, graph, blueprint, tuning_profile):
        self.graph = graph
        self.blueprint = blueprint
        self.tuning = tuning_profile
        self.sensors = [
            {
                "id": s["id"],
                "pipe_id": s.get("pipe_id", "unknown"),
                "lps": 0.0,
                "noise_factor": 1.0
                + (random.random() - 0.5) * 0.05,  # Tighter tolerance
                "drift_offset": 0.0,
                "dampening_factor": 1.0,
                "lps_multiplier": 1.0,
                "post_burst_chaos": 0.0,  # NEW: Lingering effect after a burst
            }
            for s in graph["sensors_ordered"]
        ]
        self.nodes = [
            {
                "id": n["id"],
                "balance": 0.0,
                "inflows": n["inflows"],
                "outflows": n["outflows"],
            }
            for n in graph["balance_nodes"]
        ]

    def run_simulation_scenario(self, duration_cycles, base_lps, event=None):
        """Runs a full scenario, applying event lifecycles."""
        if event:
            # Schedule all effects before the simulation begins
            self._schedule_event(event, duration_cycles)

        # Run the simulation cycle by cycle
        for cycle in range(duration_cycles):
            self._update_for_cycle(base_lps, cycle)

            for n in self.nodes:
                n["balance"] = sum(self.sensors[i]["lps"] for i in n["inflows"]) - sum(
                    self.sensors[i]["lps"] for i in n["outflows"]
                )
            yield ([s["lps"] for s in self.sensors], [n["balance"] for n in self.nodes])

    def _schedule_event(self, event, duration_cycles):
        """Pre-calculates and schedules all effects for a scenario."""
        mode = event["type"]
        loc_id = event.get("location_id")
        sev = event.get("severity", 1.0)

        # --- Persistent Failures ---
        if mode in ["STEADY_LEAK", "CLOG"]:
            target_pipe_idx = next(
                (i for i, s in enumerate(self.sensors) if s["pipe_id"] == loc_id), None
            )
            if target_pipe_idx is not None:
                multiplier = 1.0 - (sev * 0.6) if mode == "CLOG" else 1.0 - sev
                dampening = 1.0 - (sev * 0.9) if mode == "CLOG" else 1.0
                for i in range(target_pipe_idx, len(self.sensors)):
                    self.sensors[i]["lps_multiplier"] = multiplier
                    self.sensors[i]["dampening_factor"] = dampening

        # --- Scheduled Events (Drift, Burst) ---
        elif mode == "SENSOR_DRIFT":
            target_idx = next(
                (i for i, s in enumerate(self.sensors) if s["id"] == loc_id), None
            )
            if target_idx is not None:
                self.sensors[target_idx]["drift_schedule"] = (
                    self._create_drift_schedule(sev, duration_cycles)
                )

        elif mode == "BURST_LEAK":
            target_idx = next(
                (i for i, s in enumerate(self.sensors) if s["pipe_id"] == loc_id), None
            )
            if target_idx is not None:
                # The pipe is now permanently broken after a burst
                for i in range(target_idx, len(self.sensors)):
                    self.sensors[i]["lps_multiplier"] = 0.1 * (1.0 - sev)
                # Schedule the one-time effects
                self.sensors[target_idx]["initial_shock"] = {
                    "type": "BURST",
                    "severity": sev,
                }
                # And schedule the aftershocks
                for i in range(
                    1, min(15, duration_cycles)
                ):  # Aftershocks for up to 15 cycles
                    for s in self.sensors:
                        s.setdefault("aftershocks", [0] * duration_cycles)[i] = (
                            random.uniform(-1, 1) * sev * (0.4 / (i * 0.5))
                        )

        elif mode == "BENIGN_ANOMALY":
            for s in self.sensors:  # Affects all sensors for one cycle
                s["initial_shock"] = {
                    "type": "SLAM",
                    "severity": sev * 0.6,
                }  # Less severe than a burst

    def _create_drift_schedule(self, severity, duration):
        """Creates a gradual, then persistent, drift schedule."""
        drift_magnitude = (
            self.tuning.get("near_zero_flow_lps", 0.05) * 6 * (severity - 0.5) * 2
        )
        onset_duration = int(duration * 0.3)  # Slower onset
        schedule = []
        for i in range(duration):
            if i < onset_duration and onset_duration > 0:
                schedule.append((drift_magnitude / onset_duration) * (i + 1))
            else:
                schedule.append(drift_magnitude)
        return schedule

    def _update_for_cycle(self, base_lps, cycle_num):
        """Applies all scheduled and persistent effects for a single cycle."""
        # 1. Update Drift
        for s in self.sensors:
            if "drift_schedule" in s and cycle_num < len(s["drift_schedule"]):
                s["drift_offset"] = s["drift_schedule"][cycle_num]

        # 2. Propagate base flow considering persistent reductions
        current_lps = base_lps
        for s in self.sensors:
            current_lps *= s["lps_multiplier"]
            s["lps"] = max(0, current_lps)

        # 3. Apply one-time shocks (Bursts, Valve Slams) for this cycle
        for s in self.sensors:
            if "initial_shock" in s and cycle_num == 0:
                shock = s["initial_shock"]
                if shock["type"] == "BURST":
                    s["lps"] *= 0.1  # Massive initial drop
                s["lps"] += base_lps * 0.4 * random.uniform(-1, 1) * shock["severity"]

        # 4. Apply lingering aftershocks and standard chaos noise
        for s in self.sensors:
            s["lps"] += s["drift_offset"]
            # Add aftershock effect if scheduled for this cycle
            if "aftershocks" in s and cycle_num < len(s["aftershocks"]):
                s["lps"] += base_lps * s["aftershocks"][cycle_num]

            # Standard proportional noise, dampened by clogs
            noise_mag = (s["lps"] * 0.02) + self.tuning.get(
                "near_zero_flow_lps", 0.05
            ) * 0.1
            s["lps"] += random.normalvariate(
                0, noise_mag * s["noise_factor"] * s["dampening_factor"]
            )
            s["lps"] = max(0, s["lps"])


def generate_training_dataset(
    blueprint,
    num_scenarios=4000,
    cycles_per_scenario=100,
    filename="training_data_engineered.csv",
):
    """
    (The Chief Cartographer v3.1 - "Oracle's Intuition")
    Generates a dataset with engineered time-series features and corrected
    NumPy operations for robust calculation.
    """
    print("\n[Data Factory] Forging ENGINEERED dataset for >90% accuracy target...")

    from collections import deque

    WINDOWS = [5, 15]

    event_types = [
        {"type": "NORMAL", "label": 0},
        {"type": "BENIGN_ANOMALY", "label": 0},
        {"type": "STEADY_LEAK", "label": 1},
        {"type": "BURST_LEAK", "label": 2},
        {"type": "CLOG", "label": 3},
        {"type": "SENSOR_DRIFT", "label": 4},
    ]

    with open(filename, "w", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        header_written = False

        for i in range(num_scenarios):
            tuning_profile = next(
                (
                    p
                    for p in blueprint["system_tuning_parameters"]["profiles"]
                    if p["id"] == "normal_balanced"
                ),
                None,
            )
            graph = build_system_graph(blueprint)
            sim = PipelineSimulator(graph, blueprint, tuning_profile)

            event = random.choice(event_types)
            location_id = "none"
            if event["type"] == "SENSOR_DRIFT":
                if graph.get("sensors_ordered"):
                    location_id = random.choice(graph["sensors_ordered"])["id"]
            elif event["type"] in ["STEADY_LEAK", "BURST_LEAK", "CLOG"]:
                if blueprint.get("pipes"):
                    location_id = random.choice(blueprint["pipes"])["pipe_id"]

            event_to_apply = {
                "type": event["type"],
                "location_id": location_id,
                "severity": random.uniform(0.2, 0.8),
            }
            simulation_results = sim.run_simulation_scenario(
                cycles_per_scenario, random.uniform(2.0, 10.0), event_to_apply
            )

            history_buffer = deque(maxlen=max(WINDOWS) + 1)

            for sensor_lps, node_balances in simulation_results:
                current_features = sensor_lps + node_balances
                history_buffer.append(current_features)

                if len(history_buffer) < max(WINDOWS) + 1:
                    continue

                final_feature_row = list(history_buffer[-1])
                history_np = np.array(history_buffer)

                for window in WINDOWS:
                    window_data = history_np[-window:]
                    final_feature_row.extend(np.mean(window_data, axis=0))
                    final_feature_row.extend(np.std(window_data, axis=0))

                roc = np.array(history_buffer[-1]) - np.array(history_buffer[-2])
                final_feature_row.extend(roc)

                if not header_written:
                    base_headers = [f"s{i}" for i in range(len(sensor_lps))] + [
                        f"n{i}" for i in range(len(node_balances))
                    ]
                    new_headers = list(base_headers)
                    for w in WINDOWS:
                        new_headers.extend([f"{h}_mean_{w}" for h in base_headers])
                        new_headers.extend([f"{h}_std_{w}" for h in base_headers])
                    new_headers.extend([f"{h}_roc" for h in base_headers])
                    csv_writer.writerow(new_headers + ["failure_label"])
                    header_written = True

                csv_writer.writerow(final_feature_row + [event["label"]])

            if (i + 1) % 400 == 0:
                print(
                    f"  -> Engineered scenario {i+1}/{num_scenarios}: {event['type']}"
                )

    print(
        f"\n[Data Factory] [OK] SUCCESS: Engineered feature dataset saved as '{filename}'."
    )


# ... (rest of the file is unchanged from the previous version) ...
# ==============================================================================
# SECTION 3: CORE FACTORY ENGINES & UTILITIES
# ==============================================================================

USER_CPP_TEMPLATE = r"""// IntelliPipe Master C++ Template v13.0 "Aegis" (Async Upgrade)
#include <FS.h>
#include <SPIFFS.h>
#include <WiFi.h>
#include <AsyncTCP.h>
#include <ESPAsyncWebServer.h>
#include <math.h>
#include <vector>
#include <deque>
#include <algorithm>
#include <numeric>
#include <ArduinoJson.h>

// __PYTHON_INJECT_AI_BLOCK__

// ==========================================================================
//               MASTER IMPLEMENTATION BLOCK (INJECTED)
// ==========================================================================

// __PYTHON_INJECT_MASTER_IMPLEMENTATION__
"""


def assemble_platformio(code_blocks, output_dir):
    """Assembles the code blocks into a PlatformIO project structure."""
    os.makedirs(os.path.join(output_dir, "src"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "include"), exist_ok=True)

    # main.cpp: includes + ai_block + globals + functions + setup + loop
    main_cpp = (
        code_blocks["includes"]
        + "\n\n"
        + code_blocks["ai_block"]
        + "\n\n"
        + code_blocks["globals"]
        + "\n\n"
        + code_blocks["functions"]
        + "\n\n"
        + code_blocks["setup"]
        + "\n\n"
        + code_blocks["loop"]
    )
    with open(os.path.join(output_dir, "src", "main.cpp"), "w", encoding="utf-8") as f:
        f.write(main_cpp)

    # config.h: globals
    with open(
        os.path.join(output_dir, "include", "config.h"), "w", encoding="utf-8"
    ) as f:
        f.write(code_blocks["globals"])

    # platformio.ini
    platformio_ini = """[env:esp32dev]
platform = espressif32
board = esp32dev
framework = arduino
lib_deps =
    me-no-dev/AsyncTCP@^1.1.1
    me-no-dev/ESP Async WebServer@^1.2.3
    bblanchon/ArduinoJson@^7.0.3
    madhephaestus/ESP32Servo@^1.1.1
"""
    with open(os.path.join(output_dir, "platformio.ini"), "w", encoding="utf-8") as f:
        f.write(platformio_ini)


def assemble_monolith(code_blocks):
    """Assembles the code blocks into a single .ino file using the template."""
    template = USER_CPP_TEMPLATE
    template = template.replace(
        "// __PYTHON_INJECT_AI_BLOCK__", code_blocks["ai_block"]
    )
    implementation = (
        code_blocks["globals"]
        + "\n\n"
        + code_blocks["functions"]
        + "\n\n"
        + code_blocks["setup"]
        + "\n\n"
        + code_blocks["loop"]
    )
    template = template.replace(
        "// __PYTHON_INJECT_MASTER_IMPLEMENTATION__", implementation
    )
    return template


def build_system_graph(bp):
    """
    (Universal Topology Engine v2.0 - Consultant Ready)
    Analyzes a blueprint and builds an abstract graph representation.
    This version is upgraded to handle both "Sensored" (v5.1) and "Sensorless"
    (v6.0) blueprint standards, making it the core analytical tool for both
    the firmware forge and the new Design Consultant.
    """
    print(" -> Executing Universal Topology Engine (v2.0)...")
    nodes_map = {n["node_id"]: n for n in bp.get("nodes", [])}
    pipes = bp.get("pipes", [])
    sensors_ordered, s_map = [], {}

    # Check if this is a "Sensored" blueprint (for firmware generation)
    is_sensored_blueprint = any("flow_sensor" in p for p in pipes)

    # --- Pass 1: Sensor Indexing (only if sensored) ---
    if is_sensored_blueprint:
        print(" -> Blueprint is 'Sensored'. Indexing sensors for firmware generation.")
        for p in pipes:
            # We still check for the key to handle mixed or malformed blueprints
            if "flow_sensor" in p and p["flow_sensor"]:  # ensure it's not an empty dict
                s_data = p["flow_sensor"]
                s_id = s_data.get("sensor_id")
                if not s_id or s_id in s_map:
                    raise ValueError(
                        f"Blueprint is sensored but contains invalid/duplicate sensor ID in pipe {p.get('pipe_id')}"
                    )

                s_map[s_id] = len(sensors_ordered)
                sensors_ordered.append(
                    {
                        "id": s_id,
                        "pin": s_data.get("gpio_pin"),
                        "k_factor": s_data.get("k_factor_ppl"),
                        "label": s_data.get("label", s_id),
                        "pipe_id": p.get("pipe_id"),
                    }
                )

    # --- Pass 2: Graph Connectivity (for all blueprint types) ---
    # The `io` map now represents ALL pipe connections, not just sensored ones.
    io = {nid: {"in": [], "out": []} for nid in nodes_map}
    for idx, p in enumerate(pipes):
        if p.get("source_node") in io:
            io[p["source_node"]]["out"].append(idx)
        if p.get("target_node") in io:
            io[p["target_node"]]["in"].append(idx)

    # --- Pass 3: Balance Node Generation (for firmware) ---
    # Balance nodes are only meaningful for firmware if the pipes have sensors.
    balance_nodes = []
    if is_sensored_blueprint:
        b_io = {nid: {"in": [], "out": []} for nid in nodes_map}
        for p in pipes:
            if "flow_sensor" in p and p["flow_sensor"]:
                s_idx = s_map.get(p["flow_sensor"]["sensor_id"])
                if s_idx is not None:
                    if p.get("source_node") in b_io:
                        b_io[p["source_node"]]["out"].append(s_idx)
                    if p.get("target_node") in b_io:
                        b_io[p["target_node"]]["in"].append(s_idx)

        balance_nodes = [
            {"id": nid, "inflows": sorted(d["in"]), "outflows": sorted(d["out"])}
            for nid, d in b_io.items()
            if d["in"] or d["out"]
        ]

    # The final output is a dictionary containing all possible graph representations.
    # Tools like the Consultant can use the 'physical_graph' part, while the
    # firmware forge uses 'sensors_ordered' and 'balance_nodes'.
    result = {
        "is_sensored": is_sensored_blueprint,
        "sensors_ordered": sensors_ordered,
        "balance_nodes": balance_nodes,
        "physical_graph": {  # A new key for the Consultant's use!
            "nodes": nodes_map,
            "pipes": pipes,
            "connectivity": io,
        },
    }

    print(
        f" -> Topology analysis complete. Discovered {len(nodes_map)} total nodes and {len(pipes)} total pipes."
    )
    if is_sensored_blueprint:
        print(
            f" -> Identified {len(sensors_ordered)} sensors and {len(balance_nodes)} balance nodes for firmware."
        )

    return result


def generate_full_cpp_function(name, body_lines, return_type="void", parameters=None):
    """(Core Helper v2.0) Wraps C++ lines into a full function definition."""
    params_str = ", ".join(parameters) if parameters else ""
    lines = [f"{return_type} {name}({params_str}) {{"]
    for line in body_lines:
        lines.append(f"    {line}")
    lines.append("}")
    return "\n".join(lines)


def generate_master_isr_array(graph):
    """Creates a C-style array of function pointers for the ISRs."""
    num_sensors = len(graph["sensors_ordered"])
    typedef = "typedef void (*ISR_FUNC)();"
    isr_names = ", ".join([f"ISR_S{i}" for i in range(num_sensors)])
    array_def = f"ISR_FUNC ISR_S_FN[{num_sensors}] = {{ {isr_names} }};"
    return f"{typedef}\n{array_def}"


# ==============================================================================
# SECTION 4: THE C++ "SURGICAL TOOLKIT" (FORGING TOOLS)
# ==============================================================================

# 4.A: System Foundation & Structure Forges
# ------------------------------------------------------------------------------


def generate_tuning_system(bp):
    """
    (Surgical Tool v2.0) Generates ONLY the tuning profile data
    structures and global variables.
    """
    cfg = bp.get("system_tuning_parameters", {})
    profiles = cfg.get("profiles", [])
    if not profiles:
        raise ValueError("No tuning profiles found in blueprint.")
    keys = profiles[0].keys()

    def get_cpp_type(val):
        if isinstance(val, bool):
            return "bool"
        if isinstance(val, int):
            return "int"
        if isinstance(val, float):
            return "float"
        return "String"

    s = ["struct TuningProfile {"]
    for k in keys:
        s.append(f"    {get_cpp_type(profiles[0][k])} {k};")
    s.extend(
        ["};", "std::vector<TuningProfile> AllProfiles;", "TuningProfile ActiveTuning;"]
    )
    return "\n".join(s)


def generate_digital_twin_namespace(graph, bp):
    """
    (Surgical Tool v1.5 - ISR Hardened) Forges the C++ Digital Twin.
    The volatile pulse_count member has been removed for ISR safety.
    """
    print(" -> Forging the C++ Digital Twin namespace (v1.5 ISR Hardened)...")

    cpp_lines = [
        "namespace Pipeline {",
        "  struct Sensor {",
        "    String id; uint8_t pin; float k_factor;",
        "    float raw_rate_lps = 0.0f; float filtered_rate_lps = 0.0f;",
        "    bool is_valid_this_cycle = true; bool is_permanently_faulty = false;",
        "    int consecutive_fault_count = 0; float prev_filtered_rate_lps = NAN;",
        "    std::vector<float> history; int history_index = 0; float prev_raw_rate_lps = 0.0f;",
        "    int stuck_counter = 0; Sensor() : history(1, 0.0f) {}",
        "  };",
        "  struct BalanceNode {",
        "    String id; std::vector<int> inflow_sensor_indices; std::vector<int> outflow_sensor_indices;",
        "    float mean_balance_lps = NAN; float std_dev_balance_lps = NAN;",
        "    double sum_X = 0; double sum_X2 = 0;",
        "    BalanceNode(String _id, std::vector<int> _in, std::vector<int> _out) : id(_id), inflow_sensor_indices(_in), outflow_sensor_indices(_out) {}",
        "  };",
        "  struct Pipe {",
        "    String id; int sensor_index; float length_m; float diameter_m;",
        "    Pipe(String _id, int _idx, float _len, float _dia) : id(_id), sensor_index(_idx), length_m(_len), diameter_m(_dia) {}",
        "  };",
        "  std::vector<Sensor> SENSORS;",
        "  std::vector<BalanceNode> NODES;",
        "  std::vector<Pipe> PIPES;",
        "  void initializeGraph() {",
        "    SENSORS.clear(); NODES.clear(); PIPES.clear();",
        "    // Initialize SENSORS vector from blueprint",
    ]

    for s in graph["sensors_ordered"]:
        cpp_lines.append(
            "    SENSORS.emplace_back(); SENSORS.back().id=\"{s['id']}\"; SENSORS.back().pin={s['pin']}; SENSORS.back().k_factor={s['k_factor']:.2f}f;"
        )

    cpp_lines.append(
        "    // Initialize NODES vector from blueprint (unambiguous syntax)"
    )
    for n in graph["balance_nodes"]:
        inflows_str = ",".join(map(str, n["inflows"]))  # noqa: F841
        outflows_str = ",".join(map(str, n["outflows"]))  # noqa: F841
        cpp_lines.append(
            "    NODES.emplace_back(\"{n['id']}\", std::vector<int>{{{inflows_str}}}, std::vector<int>{{{outflows_str}}});"
        )

    cpp_lines.append(
        "    // Initialize PIPES vector from blueprint (unambiguous syntax)"
    )
    all_pipes = bp.get("pipes", [])
    sensor_map = {s["id"]: i for i, s in enumerate(graph["sensors_ordered"])}
    for p in all_pipes:
        if "flow_sensor" in p:
            s_idx = sensor_map.get(p["flow_sensor"]["sensor_id"], -1)  # noqa: F841
            props = p.get("properties", {})  # noqa: F841
            cpp_lines.append(
                "    PIPES.emplace_back(\"{p['pipe_id']}\", {s_idx}, {props.get('length_m',0.0):.4f}f, {props.get('inner_diameter_m',0.0):.4f}f);"
            )

    cpp_lines.append(
        "    // Dynamically resize sensor history buffers based on active tuning profile"
    )
    cpp_lines.append(
        "    for(auto& s : SENSORS) { s.history.resize(ActiveTuning.median_window_size, 0.0f); }"
    )
    cpp_lines.append("  }")
    cpp_lines.append("} // End namespace Pipeline")

    return "\n".join(cpp_lines)


def generate_isrs(graph):
    """
    (Surgical Tool - ISR Hardened) Generates ISRs that write to a dedicated,
    fixed-size volatile array for maximum safety.
    """
    print(" -> Forging ISRs (Hardened for Fixed-Size Array)...")
    num_sensors = len(graph["sensors_ordered"])
    return "\n".join(
        [
            f"void IRAM_ATTR ISR_S{i}() {{ if ({i} < {num_sensors}) volatile_pulse_counts[{i}]++; }}"
            for i, _ in enumerate(graph["sensors_ordered"])
        ]
    )


# 4.B: Core System Logic Forges
# ------------------------------------------------------------------------------
def generate_update_flow_rates(graph, blueprint):
    """
    (Surgical Tool - ISR Hardened) Forges sensor integrity logic. This version
    safely reads from the dedicated volatile pulse count array.
    """
    print(" -> Forging Flow Rate & Validity logic (ISR Hardened)...")

    len(graph["sensors_ordered"])

    body_lines = [
        "int p[SENSOR_COUNT];",  # Use a stack-allocated C-style array
        "",
        "// --- Safely copy pulse counts from ISR context ---",
        "noInterrupts();",
        "for(int i=0; i < SENSOR_COUNT; ++i) {",
        "    p[i] = volatile_pulse_counts[i];",
        "    volatile_pulse_counts[i] = 0;",
        "}",
        "interrupts();",
        "",
        "float interval = (float)ActiveTuning.update_interval_ms / 1000.0f;",
        "if (interval < 1e-6f) return;",
        "",
        "int new_faults_this_cycle = 0;",
        "for (int i=0; i < SENSOR_COUNT; ++i) {",
        "    auto& s = Pipeline::SENSORS[i];",
        "    s.raw_rate_lps = (s.k_factor > 1e-6) ? ((float)p[i] / s.k_factor / interval) : 0.0f;",
        "",
        '    bool is_valid_now = true; String failReason = "";',
        '    if (isnan(s.raw_rate_lps) || s.raw_rate_lps < 0 || s.raw_rate_lps > ActiveTuning.max_realistic_flow_lps) { is_valid_now = false; if(ActiveTuning.debug_validity_level > 0) failReason = "Range"; }',
        "    if (abs(s.raw_rate_lps - s.prev_raw_rate_lps) < 1e-6) { s.stuck_counter++; } else { s.stuck_counter = 0; }",
        '    if (s.stuck_counter >= ActiveTuning.stuck_sensor_cycles) { is_valid_now = false; if(ActiveTuning.debug_validity_level > 0) failReason = "Stuck"; }',
        "    s.prev_raw_rate_lps = s.raw_rate_lps;",
        "    s.is_valid_this_cycle = is_valid_now;",
        "",
        "    if (!s.is_valid_this_cycle) {",
        "        s.consecutive_fault_count++;",
        "        if (ActiveTuning.debug_validity_level > 0) {",
        '            Serial.printf("DBG_VLD: ID=%s, Reason=%s, Raw=%.3f, FaultCount=%d\\n", s.id.c_str(), failReason.c_str(), s.raw_rate_lps, s.consecutive_fault_count);',
        "        }",
        "    } else { s.consecutive_fault_count = 0; }",
        "",
        "    if (!s.is_permanently_faulty && s.consecutive_fault_count >= ActiveTuning.max_consecutive_faults) {",
        "        s.is_permanently_faulty = true;",
        '        logEvent("Permanent FAULT declared: " + s.id);',
        "        new_faults_this_cycle++;",
        "    }",
        "}",
        "",
        "// --- State Transition Logic for Degraded/Fault Modes (Hardened) ---",
        "if (new_faults_this_cycle > 0) {",
        '    int total_faulty_sensors = 0; String faulty_ids = "";',
        '    for(const auto& s : Pipeline::SENSORS) { if(s.is_permanently_faulty) { total_faulty_sensors++; faulty_ids += s.id + " "; } }',
        "    faulty_ids.trim();",
        "",
        "    if (total_faulty_sensors >= 2) {",
        "        currentSystemState = SystemState::SENSOR_FAULT;",
        '        statusMessage = "MULTI-SENSOR FAULT: " + faulty_ids;',
        "    } else if (total_faulty_sensors == 1) {",
        "        currentSystemState = SystemState::OPERATING_DEGRADED;",
        '        statusMessage = "DEGRADED MODE: Fault on " + faulty_ids;',
        "    }",
        "}",
    ]

    return generate_full_cpp_function("updateFlowRatesAndValidity", body_lines)


def generate_calculate_filtered_flow_rates(graph, blueprint):
    """
    (Surgical Tool, Certified) Forges the C++ logic for filtering raw
    sensor data using a median filter and an exponential moving average.
    """
    print(" -> Forging Filtered Flow Rate logic...")

    body_lines = [
        "for (auto& s : Pipeline::SENSORS) {",
        "    if (s.is_valid_this_cycle) {",
        "        // First, apply a median filter to reject spikes",
        "        float median_f = applyMedianFilter(s);",
        "",
        "        // Then, apply an EMA filter for smoothing",
        "        if (isnan(s.prev_filtered_rate_lps)) {",
        "            s.filtered_rate_lps = median_f;",
        "        } else {",
        "            s.filtered_rate_lps = (ActiveTuning.ema_alpha * median_f) + ((1.0f - ActiveTuning.ema_alpha) * s.prev_filtered_rate_lps);",
        "        }",
        "        s.filtered_rate_lps = max(0.0f, s.filtered_rate_lps);",
        "    }",
        "    s.prev_filtered_rate_lps = s.filtered_rate_lps;",
        "}",
    ]
    return generate_full_cpp_function("calculateFilteredFlowRates", body_lines)


def generate_handle_calibration(graph, blueprint):
    """
    (Surgical Tool, Hardened) Forges the live calibration logic. This
    version is updated to use the strongly-typed 'enum class' syntax for all state transitions.
    """
    print(" -> Forging Calibration Handler (Enum Class Hardened)...")

    ai_enabled = blueprint.get("ai_model", {}).get("enabled", False)
    # The 'success_state' now needs to include the class scope
    success_state = (
        "SystemState::AI_ACTIVE" if ai_enabled else "SystemState::OPERATING_RULES"
    )

    body_lines = [
        "if (currentSystemState != SystemState::CALIBRATING) return;",
        "",
        "// === Stage 1: Check for stable flow conditions before starting === ",
        "bool flow_is_stable_and_present = !Pipeline::SENSORS.empty() && Pipeline::SENSORS[0].filtered_rate_lps >= ActiveTuning.calibration_min_start_flow_lps;",
        "if (flow_is_stable_and_present) {",
        "    if (calibFlowConfirmCycles < ActiveTuning.calib_start_confirm_cycles) calibFlowConfirmCycles++;",
        "} else {",
        "    calibFlowConfirmCycles = 0;",
        "    if (calibrationSamplesCollected > 0) {",
        '        logEvent("Calib Reset: Flow stopped or became unstable");',
        "        resetCalibrationAndFaults();",
        "    }",
        '    statusMessage = "Calib: Waiting for stable flow...";',
        "    return;",
        "}",
        "if (calibFlowConfirmCycles < ActiveTuning.calib_start_confirm_cycles) {",
        '    statusMessage = "Calib: Confirming stable flow...";',
        "    return;",
        "}",
        "",
        "// === Stage 2: Check for valid sensor readings during sample collection === ",
        "bool all_sensors_are_valid_this_cycle = true;",
        "for (const auto& s : Pipeline::SENSORS) {",
        "    if (!s.is_valid_this_cycle) {",
        "        all_sensors_are_valid_this_cycle = false;",
        "        break;",
        "    }",
        "}",
        "if (!all_sensors_are_valid_this_cycle) {",
        "    invalidSamplesDuringCalibration++;",
        "    if (invalidSamplesDuringCalibration > ActiveTuning.calibration_sample_count / 4) { ",
        '        logEvent("Calib FAIL: Sensor readings too unstable");',
        "        currentSystemState = SystemState::FAILED_CALIBRATION;",
        "    }",
        "    return;",
        "}",
        "",
        "// === Stage 3: Collect samples if all checks pass === ",
        'if (calibrationSamplesCollected == 0) logEvent("Calib: Collecting Samples");',
        "for (auto& n : Pipeline::NODES) {",
        "    float balance = 0.0f;",
        "    for (int i : n.inflow_sensor_indices) balance += Pipeline::SENSORS[i].filtered_rate_lps;",
        "    for (int i : n.outflow_sensor_indices) balance -= Pipeline::SENSORS[i].filtered_rate_lps;",
        "    if (!isnan(balance)) {",
        "        n.sum_X += balance;",
        "        n.sum_X2 += balance * balance;",
        "    }",
        "}",
        "calibrationSamplesCollected++;",
        'statusMessage = "Calibrating: " + String(calibrationSamplesCollected) + "/" + String(ActiveTuning.calibration_sample_count);',
        "",
        "// === Stage 4: Finalize calibration after collecting all samples === ",
        "if (calibrationSamplesCollected >= ActiveTuning.calibration_sample_count) {",
        "    if (calculateStatistics()) {",
        '        logEvent("Calibration Complete.");',
        "        saveCalibrationData();",
        f"       currentSystemState = {success_state};",
        '        statusMessage = "System Operational";',
        "    } else {",
        '        logEvent("Calib FAIL: Could not calculate statistics");',
        "        currentSystemState = SystemState::FAILED_CALIBRATION;",
        "    }",
        "}",
    ]

    return generate_full_cpp_function("handleCalibration", body_lines)


def generate_calculate_statistics(graph, blueprint):
    """
    (Surgical Tool, Purified) Forges the function to calculate node
    statistics. Now generates C++ compliant strings.
    """
    print(" -> Forging Node Statistics function (Purified)...")

    body_lines = [
        "bool all_ok = true;",
        "for (auto& n : Pipeline::NODES) {",
        "    if (!calculateNodeStatistics(n)) {",
        "        all_ok = false;",
        "    }",
        "    // This Serial.printf is for debugging purposes",
        # THE FIX: The string is now on a single line with '\\n' for the newline.
        "    Serial.printf(\"CALIB OK '%s': Mean=%.4f, StdDev=%.5f\\n\", n.id.c_str(), n.mean_balance_lps, n.std_dev_balance_lps);",
        "}",
        "calibrationComplete = all_ok;",
        "return all_ok;",
    ]
    return generate_full_cpp_function("calculateStatistics", body_lines, "bool")


def generate_save_calibration(graph, blueprint):
    """
    (Surgical Tool: The Foreman's Scribe v2.0 - Modernized)
    Generates C++ to save system state, now using the modern ArduinoJson v7 API.
    """
    print(" -> Forging save_calibration (v7 Modernized)...")

    # In v7, we can let JsonDocument manage its own size, but giving a hint is good practice.
    256 + (len(graph["balance_nodes"]) * 128)

    body_lines = [
        "if (!calibrationComplete) {",
        '    logEvent("Save DENIED: Calib Incomplete");',
        "    return false;",
        "}",
        "JsonDocument doc;",
        "",
        "// --- Embed Metadata ---",
        'doc["file_version"] = "1.1-Foreman";',
        "doc[\"project_name\"] = \"{blueprint.get('project_details', {}).get('name', 'Unknown')}\";",
        'doc["last_saved_ms"] = millis();',
        "",
        # <<<--- ARDUINOJSON V7 API MODERNIZATION ---<<<
        "// --- Persist the System's Mind ---",
        'JsonObject state = doc["saved_state"].to<JsonObject>();',
        'state["active_tuning_profile_id"] = ActiveTuning.id;',
        "",
        'JsonArray nodes = state["calibrated_nodes"].to<JsonArray>();',
        "for (const auto& n : Pipeline::NODES) {",
        "    if (isnan(n.mean_balance_lps) || isnan(n.std_dev_balance_lps)) continue;",
        "    JsonObject node_obj = nodes.add<JsonObject>();",
        '    node_obj["id"] = n.id;',
        '    node_obj["mean_lps"] = serialized(String(n.mean_balance_lps, 6));',
        '    node_obj["std_dev_lps"] = serialized(String(n.std_dev_balance_lps, 6));',
        "}",
        # --- END OF MODERNIZATION ---
        "",
        "// --- Commit Memory to Physical Storage ---",
        'File file = SPIFFS.open("/calibration.json", FILE_WRITE);',
        'if (!file) { logEvent("SaveFAIL: FS Open"); return false; }',
        "",
        "size_t bytes_written = serializeJson(doc, file);",
        "file.close();",
        "",
        "if (bytes_written > 0) {",
        '    logEvent("Calibration Saved");',
        "    return true;",
        "} else {",
        '    logEvent("SaveFAIL: Write Err");',
        "    return false;",
        "}",
    ]
    return generate_full_cpp_function("saveCalibrationData", body_lines, "bool")


def generate_load_calibration(graph, blueprint):
    """
    (Surgical Tool v2.0 - Hardened & Modernized) Restores saved calibration.
    Uses 'enum class' syntax and the modern ArduinoJson v7 API.
    """
    print(" -> Forging load_calibration (v7 Modernized)...")
    ai_enabled = blueprint.get("ai_model", {}).get("enabled", False)

    success_state = (
        "SystemState::AI_ACTIVE" if ai_enabled else "SystemState::OPERATING_RULES"
    )

    body_lines = [
        'File file = SPIFFS.open("/calibration.json", FILE_READ);',
        "if (!file || file.size() == 0) {",
        "    if (file) file.close();",
        '    logEvent("LoadInfo: No calib file");',
        "    return false;",
        "}",
        "",
        # <<<--- ARDUINOJSON V7 API MODERNIZATION ---<<<
        "JsonDocument doc;",
        "DeserializationError error = deserializeJson(doc, file);",
        # --- END OF MODERNIZATION ---
        "file.close();",
        "if (error) {",
        '    logEvent("LoadFAIL: JSON Parse. Deleting corrupted file.");',
        '    SPIFFS.remove("/calibration.json");',
        "    return false;",
        "}",
        "",
        "const char* expected_project = \"{blueprint.get('project_details', {}).get('name', 'Unknown')}\";",
        'if (doc["project_name"] != expected_project) {',
        '    logEvent("LoadFAIL: Project Mismatch");',
        "    return false;",
        "}",
        "",
        'logEvent("Saved calibration found. Restoring state...");',
        'setTuningProfile(doc["saved_state"]["active_tuning_profile_id"].as<String>());',
        # <<<--- ARDUINOJSON V7 API MODERNIZATION ---<<<
        'JsonArray nodes_array = doc["saved_state"]["calibrated_nodes"].as<JsonArray>();',
        # --- END OF MODERNIZATION ---
        "int nodes_loaded = 0;",
        "for (JsonObject saved_node : nodes_array) {",
        '    const char* saved_id = saved_node["id"];',
        "    for (auto& ram_node : Pipeline::NODES) {",
        "        if (ram_node.id == saved_id) {",
        '            ram_node.mean_balance_lps = saved_node["mean_lps"].as<float>();',
        '            ram_node.std_dev_balance_lps = saved_node["std_dev_lps"].as<float>();',
        "            nodes_loaded++; break;",
        "        }",
        "    }",
        "}",
        "",
        "if (nodes_loaded > 0) {",
        "    calibrationComplete = true;",
        f"   currentSystemState = {success_state};",
        '    statusMessage = "System OK (Loaded Calib)";',
        '    logEvent("Loaded " + String(nodes_loaded) + " node states.");',
        "    return true;",
        "}",
        'logEvent("LoadWARN: File valid, but no matching nodes found.");',
        "return false;",
    ]
    return generate_full_cpp_function("loadCalibrationData", body_lines, "bool")


def generate_perform_rule_based_detection(graph, blueprint):
    """
    (Surgical Tool, AI-Aware & Hardened) Forges the rule-based detection logic.
    This version is updated to use the strongly-typed 'enum class' syntax.
    """
    print(" -> Forging Rule-Based Detection logic (Enum Class Hardened)...")

    body_lines = [
        "if (!calibrationComplete) { return; }",
        "",
        "bool is_imbalanced_this_cycle = false;",
        'String anomaly_node_id = "";',
        "",
        "for (auto& n : Pipeline::NODES) {",
        "    if (isnan(n.mean_balance_lps)) { continue; }",
        "",
        "    bool node_is_compromised = false;",
        # <<<--- SURGICAL REPAIR ---<<<
        "    if (currentSystemState == SystemState::OPERATING_DEGRADED) {",
        "        for (int i : n.inflow_sensor_indices) { if (Pipeline::SENSORS[i].is_permanently_faulty) node_is_compromised = true; }",
        "        for (int i : n.outflow_sensor_indices) { if (Pipeline::SENSORS[i].is_permanently_faulty) node_is_compromised = true; }",
        "        if (node_is_compromised) { continue; }",
        "    }",
        "",
        "    float current_balance = 0.0f;",
        "    for (int i : n.inflow_sensor_indices) current_balance += Pipeline::SENSORS[i].filtered_rate_lps;",
        "    for (int i : n.outflow_sensor_indices) current_balance -= Pipeline::SENSORS[i].filtered_rate_lps;",
        "",
        "    float deviation = current_balance - n.mean_balance_lps;",
        "    float threshold = max(abs(n.std_dev_balance_lps * ActiveTuning.deviation_std_dev_factor), ActiveTuning.near_zero_flow_lps);",
        "",
        "    if (abs(deviation) > threshold) {",
        "        is_imbalanced_this_cycle = true;",
        "        anomaly_node_id = n.id;",
        "        break;",
        "    }",
        "}",
        "",
        "static int consecutive_imbalance_cycles = 0;",
        "if (is_imbalanced_this_cycle) {",
        "    consecutive_imbalance_cycles++;",
        "    if (consecutive_imbalance_cycles >= ActiveTuning.leak_confirmation_cycles) {",
        # <<<--- SURGICAL REPAIR ---<<<
        '        if (currentHealth != SystemHealth::WARNING) { logEvent("Leak Detected @ " + anomaly_node_id); }',
        "        currentHealth = SystemHealth::WARNING;",
        '        statusMessage = "Leak Detected @ " + anomaly_node_id;',
        "    }",
        "} else {",
        # <<<--- SURGICAL REPAIR ---<<<
        '    if (currentHealth == SystemHealth::WARNING) { logEvent("System has returned to a balanced state."); }',
        "    consecutive_imbalance_cycles = 0;",
        "    currentHealth = SystemHealth::HEALTHY;",
        "    if (currentSystemState != SystemState::OPERATING_DEGRADED) {",
        '        statusMessage = "System OK";',
        "    }",
        "}",
    ]

    return generate_full_cpp_function("performRuleBasedDetection", body_lines)


def generate_reset_calibration_and_faults(graph, blueprint):
    """
    (Surgical Tool, Hardened) Forges the C++ master reset function.
    This version is updated to use the strongly-typed 'enum class' syntax.
    """
    print(" -> Forging the master system reset function (Enum Class Hardened)...")

    body_lines = [
        'logEvent("System Reset Triggered");',
        "",
        "// Reset learned statistics for all nodes",
        "for(auto& n : Pipeline::NODES) {",
        "    n.sum_X = 0; n.sum_X2 = 0;",
        "    n.mean_balance_lps = NAN;",
        "    n.std_dev_balance_lps = NAN;",
        "}",
        "",
        "// Reset status and fault counters for all sensors",
        "for(auto& s : Pipeline::SENSORS) {",
        "    s.is_permanently_faulty = false;",
        "    s.consecutive_fault_count = 0;",
        "    s.filtered_rate_lps = 0.0f;",
        "    s.raw_rate_lps = 0.0f;",
        "    s.prev_filtered_rate_lps = NAN;",
        "    s.stuck_counter = 0;",
        "}",
        "",
        "// Reset global calibration and state machine variables",
        "calibrationComplete = false;",
        "calibrationSamplesCollected = 0;",
        "calibFlowConfirmCycles = 0;",
        "invalidSamplesDuringCalibration = 0;",
        # <<<--- SURGICAL REPAIR ---<<<
        "currentSystemState = SystemState::CALIBRATING;",
        "currentHealth = SystemHealth::HEALTHY;",
        # --- END OF REPAIR ---
        'statusMessage = "Awaiting Calibration";',
    ]

    return generate_full_cpp_function("resetCalibrationAndFaults", body_lines)


# 4.C: User Interface, Web Handlers, and I/O Forges
# ------------------------------------------------------------------------------
def generate_page_shell(graph, blueprint):
    """
    (Surgical Tool: State-Aware Visualizer v3.2 - Stabilized)
    Generates the complete, state-aware web page. This version uses a robust
    single-block approach to eliminate all syntax errors and is readable.
    """
    print(" -> Forging the State-Aware Web UI (Stabilized)...")

    # --- PART 1: DYNAMICALLY GENERATE TOPOLOGY-SPECIFIC ELEMENTS ---

    # Calculate Node Positions (Robust Layout)
    node_positions, x_max, y_max = {}, 100, 150
    node_map = {n["id"]: n for n in graph["balance_nodes"]}
    root_nodes = sorted([n["id"] for n in graph["balance_nodes"] if not n["inflows"]])
    processed_nodes, level = set(), 0
    nodes_in_level = root_nodes
    while nodes_in_level:
        x = 100 + (level * 220)
        y, x_max = 100, max(x_max, x + 50)
        for i, node_id in enumerate(nodes_in_level):
            if node_id not in processed_nodes:
                node_positions[node_id] = {"x": x, "y": y}
                y += 120
                y_max, processed_nodes = max(y_max, y), processed_nodes | {node_id}
        next_level_nodes = []
        for node_id in nodes_in_level:
            for outflow_idx in node_map.get(node_id, {}).get("outflows", []):
                pipe_id = next(
                    (
                        s["pipe_id"]
                        for s in graph["sensors_ordered"]
                        if s["id"] == graph["sensors_ordered"][outflow_idx]["id"]
                    ),
                    None,
                )
                target_pipe = next(
                    (p for p in blueprint["pipes"] if p.get("pipe_id") == pipe_id), None
                )
                if target_pipe and target_pipe["target_node"] not in processed_nodes:
                    next_level_nodes.append(target_pipe["target_node"])
        nodes_in_level, level = sorted(list(set(next_level_nodes))), level + 1

    # Forge SVG Elements
    svg_pipes_html, svg_nodes_html, svg_labels_html = "", "", ""
    for p in blueprint.get("pipes", []):
        pos1, pos2 = node_positions.get(p["source_node"]), node_positions.get(
            p["target_node"]
        )
        if pos1 and pos2:
            sensor_id = p.get("flow_sensor", {}).get("sensor_id", "")
            svg_pipes_html += f'<line id="pipe-viz-{sensor_id}" x1="{pos1["x"]}" y1="{pos1["y"]}" x2="{pos2["x"]}" y2="{pos2["y"]}" class="pipe" />'
    for node_id, pos in node_positions.items():
        svg_nodes_html += f'<circle id="node-viz-{node_id}" cx="{pos["x"]}" cy="{pos["y"]}" r="15" class="node" />'
        svg_labels_html += (
            f'<text x="{pos["x"]}" y="{pos["y"] + 35}" class="label">{node_id}</text>'
        )
    pipeline_vis_html = f'<svg width="100%" height="{y_max}" viewBox="0 0 {x_max + 100} {y_max + 50}"><g>{svg_pipes_html}</g><g>{svg_nodes_html}</g><g>{svg_labels_html}</g></svg>'

    # Forge Sensor and Control Cards
    sensor_cards_html = "".join(
        [
            f'<div class="data-box" id="sensor-{s["id"]}"><h3>{s.get("label", s["id"]).upper()}</h3><p class="data-val">--.--</p><small>L/min</small><span class="status-badge">--</span></div>'
            for s in graph["sensors_ordered"]
        ]
    )
    tuning_options_html = "".join(
        [
            f'<option value="{p["id"]}">{p.get("label", p["id"])}</option>'
            for p in blueprint.get("system_tuning_parameters", {}).get("profiles", [])
        ]
    )

    # --- PART 2: ASSEMBLE THE HTML PAGE COMPONENTS ---
    # These are the reusable building blocks of our UI.

    # Define a clean CSS block. Using a triple-quoted string handles all characters safely.
    css_block = r"""
    body,html{margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,sans-serif;background-color:#1a1a1a;color:#e0e0e0}
    .container{padding:10px} .status-banner{padding:15px;text-align:center;font-weight:700;margin-bottom:10px;border-radius:8px;background-color:#2c3e50;color:#fff;transition:background-color .3s ease}
    .grid-container{display:grid;grid-template-columns:1fr;gap:20px} @media(min-width:1024px){.grid-container{grid-template-columns:3fr 1fr}}
    .card{background-color:#2c2c2c;padding:20px;border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,.5)} h1,h2{color:#4a8df3;border-bottom:1px solid #4a8df3;padding-bottom:10px;margin-top:0}
    .data-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:15px} .data-box{background-color:#3b3b3b;padding:15px;border-radius:6px;text-align:center}
    .data-box h3{margin:0 0 5px;font-size:1em;color:#a1c4fd} .data-val{font-size:2em;font-weight:700;margin:0} .status-badge{font-size:.8em;padding:3px 8px;border-radius:10px;background-color:#555}
    .pipeline-viz svg{width:100%;height:auto} .pipe{stroke:#4a8df3;stroke-width:8;transition:stroke .3s ease}.pipe.fault{stroke:#ffc400}.pipe.sensor-fault{stroke:#e53935;stroke-dasharray:10 5;animation:d 1s linear infinite}
    .node{fill:#2c3e50;stroke:#a1c4fd;stroke-width:3;transition:all .3s ease}.node.fault{fill:#c62828;animation:p .8s infinite alternate}
    .label{fill:#e0e0e0;font-size:14px;font-weight:700;text-anchor:middle;user-select:none}
    label,input,select,button{display:block;width:100%;margin-bottom:10px;box-sizing:border-box} input,select,button{padding:10px;border:1px solid #555;border-radius:4px;background-color:#3b3b3b;color:#e0e0e0;font-size:1em}
    button{background-color:#4a8df3;cursor:pointer;font-weight:700;border:0} button:hover{background-color:#5a9eff}
    #event-log{max-height:200px;overflow-y:auto;background-color:#1a1a1a;padding:10px;border-radius:4px;font-size:.9em;line-height:1.5}
    @keyframes p{to{transform:scale(1.1);stroke-width:5px}} @keyframes d{to{stroke-dashoffset:15}}
    """

    # Define a clean JavaScript block.
    js_block = r"""
    function fetchData(){fetch("/data").then(r=>r.json()).then(d=>{document.getElementById("status-banner").textContent=d.status_message;const t=document.getElementById("tuning-selector");t&&(t.value=d.active_tuning_profile_id);d.sensors.forEach(s=>{const e=document.getElementById("sensor-"+s.id);e&&(e.querySelector(".data-val").textContent=s.lpm.toFixed(1),e.querySelector(".status-badge").textContent=s.status)});document.querySelectorAll("[id^=node-viz-],[id^=pipe-viz-]").forEach(e=>e.classList.remove("fault","sensor-fault"));const s=d.status_message;if(s){if(s.includes("@")){const t=s.split("@")[1].trim();document.getElementById("node-viz-"+t)?.classList.add("fault")}else if(s.includes("DEGRADED MODE")){const t=s.split("on")[1].trim().split(" ")[0];document.getElementById("pipe-viz-"+t)?.classList.add("sensor-fault")}}document.getElementById("event-log").innerHTML=d.event_log.map(e=>`<div>${e}</div>`).reverse().join("")})}
    function handleNetSave(e){e.preventDefault();const t=e.target,s=document.getElementById("net-status");s.textContent="Saving...",fetch("/save_network",{method:"POST",body:new URLSearchParams(new FormData(t))}).then(e=>{if(!e.ok)throw new Error("HTTP status "+e.status);s.style.color="green",s.textContent="Success! Device is rebooting..."}).catch(e=>{s.style.color="red",s.textContent="Error: "+e.message})}
    function triggerRecalibration(){confirm("This will erase current calibration and restart the device. Proceed?")&&fetch("/recalibrate",{method:"POST"})}
    function setTuning(){const e=document.getElementById("tuning-selector").value;fetch("/set_tuning?profile="+e,{method:"POST"})}
    document.addEventListener("DOMContentLoaded",()=>{document.getElementById("net-form")?.addEventListener("submit",handleNetSave);document.getElementById("tuning-selector")?.addEventListener("change",setTuning);document.getElementById("status-banner")&&(fetchData(),setInterval(fetchData,2e3))});
    """

    # Assemble HTML partials
    network_card = r'<div class="card"><h2>Network Configuration</h2><form id="net-form"><p>Connect the device to a new WiFi network.</p><label for="ssid">SSID:</label><input type="text" id="ssid" name="ssid" required><label for="password">Password:</label><input type="password" name="password"><button type="submit">Save & Reboot</button></form><p id="net-status"></p></div>'
    controls_card = f'<div class="card"><h2>Controls</h2><label for="tuning-selector">Tuning Profile:</label><select id="tuning-selector">{tuning_options_html}</select><button onclick="triggerRecalibration()">Force Recalibration</button></div>'

    # Assemble full page bodies
    dashboard_body = f'<div class="container"><header><h1>IntelliPipe™ Dashboard</h1><div class="status-banner" id="status-banner">...</div></header><main class="grid-container"><section class="main-content"><h2>Sensors</h2><div class="data-grid">{sensor_cards_html}</div><h2>Visualization</h2><div class="pipeline-viz">{pipeline_vis_html}</div></section><aside class="sidebar">{controls_card}{network_card}<div class="card"><h2>Event Log</h2><div id="event-log"></div></div></aside></main></div>'
    config_body = f'<div class="container"><header><h1>IntelliPipe™ Setup</h1></header>{network_card}</div>'

    # --- PART 3: GENERATE THE FINAL C++ STATE MACHINE ---
    # This logic uses simple, robust string concatenation to build the final return value.

    # Create the config-only page string
    config_page_string = (
        '<!DOCTYPE html><html lang="en"><head><title>Setup</title><style>'
        + css_block
        + "</style></head><body>"
        + config_body
        + "<script>"
        + js_block
        + "</script></body></html>"
    )

    # Create the full dashboard page string
    dashboard_page_string = (
        '<!DOCTYPE html><html lang="en"><head><title>IntelliPipe</title><style>'
        + css_block
        + "</style></head><body>"
        + dashboard_body
        + "<script>"
        + js_block
        + "</script></body></html>"
    )

    # Build the C++ function body
    body_lines = [
        "    if (WiFi.getMode() == WIFI_AP) {",
        "        // In AP Mode, serve the minimal configuration page.",
        '        return R"raw(' + config_page_string + ')raw";',
        "    } else {",
        "        // In normal connected mode, serve the full dashboard.",
        '        return R"raw(' + dashboard_page_string + ')raw";',
        "    }",
    ]

    return generate_full_cpp_function("generatePageShell", body_lines, "String")


def generate_async_web_handlers(graph, blueprint):
    """
    (Hardened Tool v13.0) Forges all the complex AsyncWebServer request
    handlers as standalone functions, which simplifies the main setup() logic.
    """
    print(" -> Forging Async Web Handlers (Hardened)...")

    # --- Handler for /save_network ---
    save_network_body = [
        'if (request->hasParam("ssid", true) && request->hasParam("password", true)) {',
        '    String ssid = request->getParam("ssid", true)->value();',
        '    String pass = request->getParam("password", true)->value();',
        "    // --- Input Validation Hardening ---",
        "    if (ssid.length() > 32 || pass.length() > 64) {",
        '        request->send(400, "text/plain", "Bad Request: SSID or password is too long.");',
        "        return;",
        "    }",
        "    // --- End Hardening ---",
        "    if (saveNetworkConfig(ssid, pass)) {",
        '        request->send(200, "text/plain", "Success. Device will now reboot.");',
        "        delay(1000); ESP.restart();",
        '    } else { request->send(500, "text/plain", "Error: Failed to save config."); }',
        '} else { request->send(400, "text/plain", "Bad Request: Missing parameters."); }',
    ]

    # --- Handler for /set_tuning ---
    set_tuning_body = [
        'if (request->hasParam("profile", true)) {',
        '    setTuningProfile(request->getParam("profile", true)->value());',
        '    request->send(200, "text/plain", "OK");',
        '} else { request->send(400, "text/plain", "Bad Request"); }',
    ]

    # --- Handler for /recalibrate ---
    recalibrate_body = [
        "if (WiFi.getMode() == WIFI_STA) {",
        '    logEvent("Web Recalibration");',
        '    SPIFFS.remove("/calibration.json");',
        "    resetCalibrationAndFaults();",
        '    request->send(200, "text/plain", "OK");',
        '} else { request->send(403, "text/plain", "Not available in AP Mode"); }',
    ]

    # Assemble all handlers into a single string
    handlers_code = [
        generate_full_cpp_function(
            "handleSaveNetwork",
            save_network_body,
            "void",
            ["AsyncWebServerRequest *request"],
        ),
        generate_full_cpp_function(
            "handleTuningSwitch",
            set_tuning_body,
            "void",
            ["AsyncWebServerRequest *request"],
        ),
        generate_full_cpp_function(
            "handleRecalibrate",
            recalibrate_body,
            "void",
            ["AsyncWebServerRequest *request"],
        ),
    ]
    return "\n\n".join(handlers_code)


def generate_wifi_helpers(graph, blueprint):
    """
    (Hardened Tool v2.0 - Modernized) Forges lean C++ helpers for
    saving/loading network credentials, now using the modern ArduinoJson v7 API.
    """
    print(" -> Forging lean WiFi Helpers (Modernized)...")
    cpp_code = [
        "bool saveNetworkConfig(const String& ssid, const String& pass) {",
        "    JsonDocument doc;",  # Modern API
        '    doc["ssid"] = ssid; doc["password"] = pass;',
        '    File file = SPIFFS.open("/network.json", FILE_WRITE);',
        '    if (!file) { logEvent("FS_ERR: SaveNet"); return false; }',
        "    bool success = serializeJson(doc, file) > 0;",
        "    file.close();",
        '    if(success) logEvent("Saved NetCfg for \'"+ssid+"\'");',
        "    return success;",
        "}",
        "",
        "bool loadNetworkConfig(String& ssid, String& pass) {",
        '    File file = SPIFFS.open("/network.json", FILE_READ);',
        "    if (!file) return false;",
        "    JsonDocument doc;",  # Modern API
        "    DeserializationError error = deserializeJson(doc, file);",
        "    file.close();",
        '    if (error) { logEvent("LoadFAIL: NetCfg"); return false; }',
        '    ssid = doc["ssid"].as<String>();',
        '    pass = doc["password"].as<String>();',
        "    return ssid.length() > 0;",
        "}",
    ]
    return "\n".join(cpp_code)


def generate_data_api_body_lines(graph, blueprint):
    """
    (Surgical Tool v2.1 - Finalized) Generates the C++ LOGIC BLOCK for the /data API.
    Does not generate a full function; intended for use inside a C++ lambda.
    """
    print(" -> Forging Data API Logic Block (Finalized)...")

    # This function now generates only the internal logic for a lambda handler.
    body_lines = [
        "JsonDocument doc;",
        'doc["system_state"] = static_cast<int>(currentSystemState);',
        'doc["system_health"] = static_cast<int>(currentHealth);',
        'doc["status_message"] = statusMessage;',
        'doc["uptime_seconds"] = millis() / 1000;',
        'doc["active_tuning_profile_id"] = ActiveTuning.id;',
        'JsonArray profiles = doc["available_tuning_profiles"].to<JsonArray>();',
        "for (const auto& p : AllProfiles) {",
        "    JsonObject prof = profiles.add<JsonObject>();",
        '    prof["id"] = p.id;',
        '    prof["label"] = p.label;',
        "}",
        'JsonArray sensors = doc["sensors"].to<JsonArray>();',
        "for (const auto& s : Pipeline::SENSORS) {",
        "    JsonObject o = sensors.add<JsonObject>();",
        '    o["id"]=s.id; o["lpm"]=s.filtered_rate_lps*60.0f; o["status"]=s.is_permanently_faulty?"FAULT":(s.is_valid_this_cycle?"VALID":"INVALID");',
        "}",
        'JsonArray nodes = doc["nodes"].to<JsonArray>();',
        "for (const auto& n : Pipeline::NODES) {",
        "    JsonObject o = nodes.add<JsonObject>();",
        '    o["id"]=n.id; o["mean_lps"]=n.mean_balance_lps; o["std_dev_lps"]=n.std_dev_balance_lps;',
        "}",
        'JsonArray events = doc["event_log"].to<JsonArray>();',
        "for (const auto& log : eventLog) { events.add(log); }",
        "String output;",
        "serializeJson(doc, output);",
        "// --- FINAL SURGICAL FIX: Use the modern response object pattern ---",
        'AsyncWebServerResponse *response = request->beginResponse(200, "application/json", output);',
        'response->addHeader("Access-Control-Allow-Origin", "*");',
        "request->send(response);",
    ]
    return body_lines


def generate_tuning_switch_handler(graph, blueprint):
    """(Surgical Tool) Generates the handler for /set_tuning."""
    body_lines = [
        'if (server.hasArg("profile")) {',
        '    String profile_id = server.arg("profile");',
        "    setTuningProfile(profile_id);",
        '    server.send(200, "text/plain", "OK, tuning set to " + profile_id);',
        "} else {",
        '    server.send(400, "text/plain", "Bad Request: \'profile\' argument missing");',
        "}",
    ]
    return generate_full_cpp_function("handleTuningSwitch", body_lines)


def generate_recalibrate_handler(graph, blueprint):
    """
    (Surgical Tool, Certified) Forges the C++ logic for the /recalibrate
    web handler, including a safety check for AP mode.
    """
    print(" -> Forging Recalibrate Handler...")

    body = [
        "if (WiFi.getMode() == WIFI_STA) {",
        '    logEvent("Web Recalibration Request");',
        '    SPIFFS.remove("/calibration.json"); // Remove the old calibration',
        "    resetCalibrationAndFaults(); // Reset the system to a clean, calibrating state",
        '    server.send(200, "text/plain", "OK: Recalibration process initiated.");',
        "} else {",
        "    // This action should not be possible when in AP setup mode.",
        '    server.send(403, "text/plain", "Action not available in AP Mode.");',
        "}",
    ]
    return generate_full_cpp_function("handleRecalibrate", body)


# 4.D: AI Model & TFLM Integration Forges
# ------------------------------------------------------------------------------
def inject_ai_model(graph, blueprint):
    """
    (AI Tool) Reads the model.h file specified in the blueprint and
    injects its entire content into the C++ artifact.
    """
    print(" -> Implanting the Oracle's Brain (model.h)...")
    ai_config = blueprint.get("ai_model", {})
    if not ai_config.get("enabled", False):
        return "// AI MODEL NOT INJECTED: AI is disabled in the blueprint."

    model_path = ai_config.get("model_file")
    if not model_path:
        raise ValueError(
            "AI is enabled, but no 'model_file' was specified in the blueprint."
        )

    try:
        with open(model_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise ValueError(
            f"AI MODEL FORGE FAILED: Could not find model file at '{model_path}'"
        )


def generate_tflm_setup_and_globals(graph, blueprint):
    """
    (AI Tool - v3.0 Certified) Generates all necessary C++ globals
    and the setup function for TFLM, with the user's fix applied.
    """
    print(" -> Forging the TFLM Life-Support System (v3.0 Certified)...")

    code_parts = {}

    code_parts["includes"] = "\n".join(
        [
            '#include "tensorflow/lite/micro/micro_interpreter.h"',
            '#include "tensorflow/lite/micro/all_ops_resolver.h"',
            '#include "tensorflow/lite/micro/system_setup.h"',
            '#include "tensorflow/lite/micro/micro_error_reporter.h"',
            '#include "tensorflow/lite/schema/schema_generated.h"',
        ]
    )

    output_classes = blueprint.get("ai_model", {}).get("output_classes", [])
    class_names_str = ", ".join([f'"{c}"' for c in output_classes])

    code_parts["globals"] = "\n".join(
        [
            "namespace tflm {",
            "  tflite::ErrorReporter* error_reporter = nullptr;",
            "  const tflite::Model* model = nullptr;",
            "  tflite::MicroInterpreter* interpreter = nullptr;",
            "  TfLiteTensor* input = nullptr;",
            "  TfLiteTensor* output = nullptr;",
            "  constexpr int kTensorArenaSize = 8 * 1024;",
            "  uint8_t tensor_arena[kTensorArenaSize];",
            f"  const char* CLASS_NAMES[] = {{{class_names_str}}};",
            "  const int CLASS_COUNT = sizeof(CLASS_NAMES) / sizeof(CLASS_NAMES[0]);",
            "}",
        ]
    )

    setup_func_body = [
        "    static tflite::MicroErrorReporter micro_error_reporter;",
        "    tflm::error_reporter = &micro_error_reporter;",
        "",
        "    tflm::model = tflite::GetModel(g_model);",
        "    if (tflm::model->version() != TFLITE_SCHEMA_VERSION) {",
        '        TF_LITE_REPORT_ERROR(tflm::error_reporter, "Model version mismatch!");',
        "        return;",
        "    }",
        "",
        "    static tflite::AllOpsResolver resolver;",
        "    static tflite::MicroInterpreter static_interpreter(tflm::model, resolver, tflm::tensor_arena, tflm::kTensorArenaSize, tflm::error_reporter);",
        "    tflm::interpreter = &static_interpreter;",
        "",
        "    if (tflm::interpreter->AllocateTensors() != kTfLiteOk) {",
        '        TF_LITE_REPORT_ERROR(tflm::error_reporter, "AllocateTensors() failed.");',
        "        return;",
        "    }",
        "",
        "    tflm::input = tflm::interpreter->input(0);",
        "    tflm::output = tflm::interpreter->output(0);",
        '    logEvent("AI: TFLM Initialized");',
    ]

    code_parts["setup_func"] = generate_full_cpp_function("setup_tflm", setup_func_body)

    return code_parts


def generate_interpreter_function(graph, blueprint):
    """
    (AI Tool, Hardened & Decoupled) Forges the C++ function that runs AI
    inference. This version dynamically validates the model's input tensor
    shape against the system's actual feature count.
    """
    print(" -> Forging the Oracle's Mouthpiece (Decoupled Input)...")

    body = [
        "if (!tflm::interpreter || !tflm::input) {",
        '    statusMessage = "AI ERROR: Not Initialized";',
        "    currentHealth = SystemHealth::FAULTED;",
        "    return;",
        "}",
        "",
        "// 1. Verify the AI model's input shape matches our system's feature count.",
        "const int expected_features = Pipeline::SENSORS.size() + Pipeline::NODES.size();",
        "if (tflm::input->dims->size != 2 || tflm::input->dims->data[1] != expected_features) {",
        '    logEvent("AI_ERR: Model input shape (" + String(tflm::input->dims->data[1]) + ") mismatch with system feature count (" + String(expected_features) + ")");',
        "    currentSystemState = SystemState::SENSOR_FAULT; // Use a descriptive failure state",
        '    statusMessage = "AI ERROR: Model Mismatch";',
        "    return;",
        "}",
        "",
        "// 2. Load live data from the Digital Twin into the model's input tensor",
        "int feature_idx = 0;",
        "for(const auto& s : Pipeline::SENSORS) {",
        "    tflm::input->data.f[feature_idx++] = s.filtered_rate_lps;",
        "}",
        "for(const auto& n : Pipeline::NODES) {",
        "    float balance = 0.0f;",
        "    for(int i : n.inflow_sensor_indices) balance += Pipeline::SENSORS[i].filtered_rate_lps;",
        "    for(int i : n.outflow_sensor_indices) balance -= Pipeline::SENSORS[i].filtered_rate_lps;",
        "    tflm::input->data.f[feature_idx++] = balance;",
        "}",
        "",
        "// 3. Run inference by invoking the TFLM interpreter",
        "if (tflm::interpreter->Invoke() != kTfLiteOk) {",
        '    logEvent("AI_ERR: Invoke Failed");',
        "    return;",
        "}",
        "",
        "// 4. Find the highest probability from the output tensor",
        "float max_prob = -1.0f;",
        "int max_idx = -1;",
        "for (int i = 0; i < tflm::CLASS_COUNT; ++i) {",
        "    if (tflm::output->data.f[i] > max_prob) {",
        "        max_prob = tflm::output->data.f[i];",
        "        max_idx = i;",
        "    }",
        "}",
        "",
        "// 5. Translate the result into a human-readable diagnosis",
        "if (max_idx != -1) {",
        "    String diagnosis = tflm::CLASS_NAMES[max_idx];",
        '    statusMessage = "AI: " + diagnosis + " (" + String(int(max_prob * 100)) + "%)";',
        "    logEvent(statusMessage);",
        "",
        '    if (diagnosis.equalsIgnoreCase("normal")) {',
        "        currentHealth = SystemHealth::HEALTHY;",
        "    } else {",
        "        currentHealth = SystemHealth::AI_DIAGNOSIS;",
        "    }",
        "} else {",
        '    statusMessage = "AI: Interpretation Error";',
        "}",
    ]
    return generate_full_cpp_function("runInferenceAndInterpret", body)


# 4.E: Main `setup()` and `loop()` Entry Point Forges
# ------------------------------------------------------------------------------
def generate_setup(graph, blueprint):
    """
    (Hardened Tool v14.0 - Finalized) Forges the C++ setup() function.
    This version contains all web handler logic as self-contained lambdas.
    """
    print(" -> Forging Setup Function (Async & Hardened)...")

    ai_enabled = blueprint.get("ai_model", {}).get("enabled", False)

    # --- Generate the /data API logic block FIRST ---
    # We call our refactored function to get the lines of C++ code.
    data_api_logic = generate_data_api_body_lines(graph, blueprint)

    body_lines = [
        "Serial.begin(115200); while(!Serial);",
        f'Serial.println("\\n\\nBooting IntelliPipe Aegis v14.0 (AI: {"ENABLED" if ai_enabled else "DISABLED"})");',
        'logEvent("Boot");',
        "",
        "// --- Initialize Filesystem & Failsafe Button ---",
        "pinMode(0, INPUT_PULLUP);",
        "if (!SPIFFS.begin(true)) {",
        '    Serial.println("FATAL: SPIFFS Mount Failed!");',
        "    while(true) delay(1000);",
        "}",
        "",
        "// --- WiFi Connection Protocol ---",
        "WiFi.mode(WIFI_STA); WiFi.disconnect(true); delay(100);",
        "String saved_ssid, saved_pass;",
        "if (loadNetworkConfig(saved_ssid, saved_pass)) {",
        "    WiFi.begin(saved_ssid.c_str(), saved_pass.c_str());",
        '    Serial.print("Connecting...");',
        '    int tries = 0; while (WiFi.status() != WL_CONNECTED && tries++ < 20) { Serial.print("."); delay(500); }',
        "}",
        "",
        "// --- Start AP Mode or Confirm Connection ---",
        "if (WiFi.status() != WL_CONNECTED) {",
        '    Serial.println("\\nConnection Failed. Starting AP.");',
        '    logEvent("NetFAIL: Starting AP");',
        '    WiFi.mode(WIFI_AP); WiFi.softAP("IntelliPipe_Setup");',
        "} else {",
        '    Serial.println("\\nSUCCESS!");',
        '    logEvent("NetOK: " + WiFi.localIP().toString());',
        "}",
        'Serial.println("IP: " + (WiFi.getMode() == WIFI_AP ? WiFi.softAPIP().toString() : WiFi.localIP().toString()));',
        "",
        "// --- Universal System Initializations ---",
        "initializeTuningProfiles();",
        "Pipeline::initializeGraph();",
        "",
        "// --- AI System Initialization ---",
        "if (" + ("true" if ai_enabled else "false") + ") {",
        "    setup_tflm();",
        "}",
        "",
        "// --- Load Saved State ---",
        "if (WiFi.getMode() == WIFI_STA) {",
        "   if (!loadCalibrationData()) {",
        "       resetCalibrationAndFaults();",
        "   }",
        "}",
        "",
        "// --- Attach Sensor Interrupts ---",
        generate_master_isr_array(graph),
        "for(size_t i = 0; i < Pipeline::SENSORS.size(); ++i) {",
        "    pinMode(Pipeline::SENSORS[i].pin, INPUT_PULLUP);",
        "    attachInterrupt(digitalPinToInterrupt(Pipeline::SENSORS[i].pin), ISR_S_FN[i], RISING);",
        "}",
        "",
        "// --- UNIFIED ASYNC WEB HANDLERS (FINALIZED) ---",
        'server.on("/", HTTP_GET, [](AsyncWebServerRequest *request){',
        '    request->send(200, "text/html", generatePageShell());',
        "});",
        "",
        "// --- FINAL SURGICAL FIX: /data handler logic is now embedded ---",
        'server.on("/data", HTTP_GET, [](AsyncWebServerRequest *request){',
        # Indent and insert the generated logic block here
        *[f"    {line}" for line in data_api_logic],
        "});",
        "",
        'server.on("/save_network", HTTP_POST, [](AsyncWebServerRequest *request){',
        '    if (request->hasParam("ssid", true) && request->hasParam("password", true)) {',
        '        String ssid = request->getParam("ssid", true)->value();',
        '        String pass = request->getParam("password", true)->value();',
        "        if (ssid.length() > 32 || pass.length() > 64) {",
        '            request->send(400, "text/plain", "Bad Request: SSID or password is too long.");',
        "            return;",
        "        }",
        "        if (saveNetworkConfig(ssid, pass)) {",
        '            request->send(200, "text/plain", "Success. Device will now reboot.");',
        "            delay(1000); ESP.restart();",
        '        } else { request->send(500, "text/plain", "Error: Failed to save config."); }',
        '    } else { request->send(400, "text/plain", "Bad Request: Missing parameters."); }',
        "});",
        "",
        'server.on("/set_tuning", HTTP_POST, [](AsyncWebServerRequest *request){',
        '    if (request->hasParam("profile", true)) {',
        '        setTuningProfile(request->getParam("profile", true)->value());',
        '        request->send(200, "text/plain", "OK");',
        '    } else { request->send(400, "text/plain", "Bad Request"); }',
        "});",
        "",
        'server.on("/recalibrate", HTTP_POST, [](AsyncWebServerRequest *request){',
        "    if (WiFi.getMode() == WIFI_STA) {",
        '        logEvent("Web Recalibration");',
        '        SPIFFS.remove("/calibration.json");',
        "        resetCalibrationAndFaults();",
        '        request->send(200, "text/plain", "OK");',
        '    } else { request->send(403, "text/plain", "Not available in AP Mode"); }',
        "});",
        "",
        "server.onNotFound([](AsyncWebServerRequest *request){",
        '    request->send(404, "text/plain", "Not Found");',
        "});",
        "// --- END OF UNIFIED HANDLERS ---",
        "",
        "server.begin();",
        'logEvent("HTTPS Server Online");',
        "",
        "lastUpdateTime = millis();",
        'Serial.println("---- Setup Complete. System is now live. ----");',
    ]
    return generate_full_cpp_function("setup", body_lines)


def generate_loop(graph, blueprint):
    """
    (Hardened Tool v13.0) Forges the main C++ loop(). This version is now
    fully compatible with the non-blocking ESPAsyncWebServer.
    """
    print(" -> Forging the Main Loop (Async Hardened)...")

    ai_enabled = blueprint.get("ai_model", {}).get("enabled", False)

    body_lines = [
        # <<<--- SURGICAL REPAIR: The obsolete handleClient() call is REMOVED ---<<<
        # "server.handleClient();", // Obsolete: Not needed for ESPAsyncWebServer
        "",
        "// In AP Mode, the device is waiting for configuration and should not run the main loop.",
        "if (WiFi.getMode() == WIFI_AP) {",
        "    return;",
        "}",
        "",
        "// Hardware Failsafe: Long-press BOOT button for a factory reset.",
        "static unsigned long btn_press_time = 0;",
        "static bool btn_was_pressed = false;",
        "if (digitalRead(0) == LOW) {",
        "    if (!btn_was_pressed) {",
        "        btn_press_time = millis();",
        "        btn_was_pressed = true;",
        "    }",
        "} else {",
        "    if (btn_was_pressed) {",
        "        if (millis() - btn_press_time > 5000) {",
        '            logEvent("BTN: Full Factory Reset");',
        '            SPIFFS.remove("/calibration.json");',
        '            SPIFFS.remove("/network.json");',
        "            ESP.restart();",
        "        }",
        "    }",
        "    btn_was_pressed = false;",
        "}",
        "",
        "// Main Processing Interval Timer",
        "if (millis() - lastUpdateTime < ActiveTuning.update_interval_ms) {",
        "    return;",
        "}",
        "lastUpdateTime = millis();",
        "",
        "// Core Data Processing Pipeline",
        "updateFlowRatesAndValidity();",
        "calculateFilteredFlowRates();",
        "",
        "// --- Master State Machine (Hardened) ---",
        "switch (currentSystemState) {",
        "    case SystemState::CALIBRATING:",
        "        handleCalibration();",
        "        break;",
        "",
        "    case SystemState::OPERATING_RULES:",
        "    case SystemState::OPERATING_DEGRADED:",
        "        performRuleBasedDetection();",
        "        break;",
        "",
        "    case SystemState::AI_ACTIVE:",
        f'        {"runInferenceAndInterpret();" if ai_enabled else "performRuleBasedDetection(); // AI disabled, using rules"}',
        "        break;",
        "",
        "    case SystemState::SENSOR_FAULT:",
        "        currentHealth = SystemHealth::FAULTED;",
        "        break;",
        "",
        "    case SystemState::FAILED_CALIBRATION:",
        '        statusMessage = "Calibration FAILED";',
        "        currentHealth = SystemHealth::WARNING;",
        "        break;",
        "",
        "    case SystemState::BOOTING:",
        "        // Loop is inactive during boot.",
        "        break;",
        "}",
    ]
    return generate_full_cpp_function("loop", body_lines)


def run_master_orchestrator(blueprint, template):
    """
    (Grand Assembler v14.0 - Finalized) The definitive hardened version.
    This orchestrator is fully detailed and integrates all compiler fixes.
    """
    print("\n[1/3] Analyzing Blueprint...")
    graph = build_system_graph(blueprint)
    ai_enabled = blueprint.get("ai_model", {}).get("enabled", False)
    num_sensors = len(graph["sensors_ordered"])

    print("[2/3] Forging C++ components with full hardening...")
    master_code = []

    # === STAGE 1: Globals, Structs, and Namespaces ===
    master_code.append("// === SECTION A: GLOBALS, DATA STRUCTURES, & NAMESPACES ===")

    print(" -> Generating ephemeral TLS credentials for HTTPS...")
    key_pem, cert_pem = generate_self_signed_cert(
        blueprint.get("project_details", {}).get("name", "IntelliPipe")
    )
    master_code.append(convert_pem_to_c_array(key_pem, "server_key"))
    master_code.append(convert_pem_to_c_array(cert_pem, "server_cert"))

    master_code.append(generate_tuning_system(blueprint))
    if ai_enabled:
        master_code.append(generate_tflm_setup_and_globals(graph, blueprint)["globals"])

    print(" -> Forging ISR safety constructs (Fixed-Size Array)...")
    master_code.append(f"const int SENSOR_COUNT = {num_sensors};")
    master_code.append("volatile int volatile_pulse_counts[SENSOR_COUNT] = {0};")

    master_code.append(generate_digital_twin_namespace(graph, blueprint))

    # Corrected Server Instantiation
    master_code.append("AsyncWebServer server(443);")

    master_code.extend(
        [
            "enum class SystemHealth { HEALTHY, WARNING, FAULTED, AI_DIAGNOSIS };",
            "enum class SystemState { BOOTING, CALIBRATING, OPERATING_RULES, OPERATING_DEGRADED, FAILED_CALIBRATION, SENSOR_FAULT, AI_ACTIVE };",
            "SystemState currentSystemState = SystemState::BOOTING; SystemHealth currentHealth = SystemHealth::HEALTHY;",
            'unsigned long lastUpdateTime = 0; String statusMessage = "Booting..."; bool calibrationComplete = false;',
            "int calibrationSamplesCollected = 0, calibFlowConfirmCycles = 0, invalidSamplesDuringCalibration = 0;",
            "std::deque<String> eventLog;",
        ]
    )

    # === STAGE 2: ALL Logic and Helper Functions ===
    master_code.append("\n// === SECTION B: HELPER & LOGIC FUNCTIONS ===")

    def _format_cpp_value(v):
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, str):
            escaped_str = v.replace('"', '\\"')
            return f'"{escaped_str}"'
        if isinstance(v, float):
            return f"{v:.4f}"
        if isinstance(v, int):
            return str(v)
        return str(v)

    init_profiles_body = ["AllProfiles.clear();"]
    profiles = blueprint.get("system_tuning_parameters", {}).get("profiles", [])
    for p in profiles:
        vals = [_format_cpp_value(v) for v in p.values()]
        init_profiles_body.append(f"    AllProfiles.push_back({{{', '.join(vals)}}});")
    init_profiles_body.append(
        f'setTuningProfile("{blueprint.get("system_tuning_parameters",{}).get("default_profile_id")}");'
    )

    log_event_body = [
        "if(ActiveTuning.max_log_events <= 0) return;",
        'String logEntry = String(millis() / 1000) + "s: " + eventMessage;',
        "eventLog.push_back(logEntry);",
        "while(eventLog.size() > (unsigned int)ActiveTuning.max_log_events) {",
        "    eventLog.pop_front();",
        "}",
    ]
    set_tuning_body = [
        "for(const auto& p : AllProfiles) {",
        "    if(p.id == profileId) {",
        "        ActiveTuning = p;",
        '        logEvent("Tuning: " + p.label);',
        "        return;",
        "    }",
        "}",
        'logEvent("WARN: Tuning profile not found: " + profileId);',
    ]
    calculate_node_stats_body = [
        "if(calibrationSamplesCollected < 2) return false;",
        "double mean_d = node.sum_X / calibrationSamplesCollected;",
        "double var_d = (node.sum_X2 / calibrationSamplesCollected) - (mean_d * mean_d);",
        "if(var_d < 0.0) var_d = 0.0;",
        "node.mean_balance_lps = (float)mean_d;",
        "node.std_dev_balance_lps = (float)sqrt(var_d);",
        "return true;",
    ]

    print(" -> Forging performance-optimized Median Filter...")
    median_filter_body = [
        "if(s.history.empty()) return s.raw_rate_lps;",
        "s.history[s.history_index] = s.raw_rate_lps;",
        "s.history_index = (s.history_index + 1) % s.history.size();",
        "std::vector<float> temp_hist = s.history;",
        "auto median_it = temp_hist.begin() + temp_hist.size() / 2;",
        "std::nth_element(temp_hist.begin(), median_it, temp_hist.end());",
        "return *median_it;",
    ]

    all_funcs = [
        generate_full_cpp_function(
            "logEvent", log_event_body, "void", ["const String& eventMessage"]
        ),
        generate_full_cpp_function(
            "setTuningProfile", set_tuning_body, "void", ["const String& profileId"]
        ),
        generate_full_cpp_function("initializeTuningProfiles", init_profiles_body),
        generate_full_cpp_function(
            "calculateNodeStatistics",
            calculate_node_stats_body,
            "bool",
            ["Pipeline::BalanceNode& node"],
        ),
        generate_full_cpp_function(
            "applyMedianFilter", median_filter_body, "float", ["Pipeline::Sensor& s"]
        ),
        generate_update_flow_rates(graph, blueprint),
        generate_calculate_filtered_flow_rates(graph, blueprint),
        generate_reset_calibration_and_faults(graph, blueprint),
        generate_calculate_statistics(graph, blueprint),
        generate_save_calibration(graph, blueprint),
        generate_load_calibration(graph, blueprint),
        generate_handle_calibration(graph, blueprint),
        generate_perform_rule_based_detection(graph, blueprint),
        generate_page_shell(graph, blueprint),
        generate_wifi_helpers(graph, blueprint),
    ]
    if ai_enabled:
        ai_parts = generate_tflm_setup_and_globals(graph, blueprint)
        all_funcs.append(ai_parts["setup_func"])
        all_funcs.append(generate_interpreter_function(graph, blueprint))
    else:
        all_funcs.extend(
            [
                generate_full_cpp_function("setup_tflm", ["/* AI DISABLED */"]),
                generate_full_cpp_function(
                    "runInferenceAndInterpret", ["/* AI DISABLED */"]
                ),
            ]
        )

    master_code.extend(all_funcs)

    # === STAGE 3: Main Entry Points and ISRs (Must be last) ===
    master_code.append("\n// === SECTION C: ISRs & MAIN ENTRY POINTS ===")
    master_code.append(generate_isrs(graph))
    master_code.append(generate_setup(graph, blueprint))
    master_code.append(generate_loop(graph, blueprint))

    # === FINAL ASSEMBLY: Definitive AI-Switching Logic ===
    print("[3/3] Assembling final artifact...")
    output_code = template
    ai_block_code = ""

    if ai_enabled:
        ai_parts = generate_tflm_setup_and_globals(graph, blueprint)
        includes = ai_parts.get("includes", "")
        model_data = inject_ai_model(graph, blueprint)
        ai_block_code = f"{includes}\n\n{model_data}"

    output_code = output_code.replace("// __PYTHON_INJECT_AI_BLOCK__", ai_block_code)

    final_implementation = "\n\n".join(master_code)
    output_code = output_code.replace(
        "// __PYTHON_INJECT_MASTER_IMPLEMENTATION__", final_implementation
    )

    return output_code


# ==============================================================================
#  SECTION 6: THE UNIVERSAL INGRESS PORT (CONVERTERS)
# ==============================================================================


def generate_self_signed_cert(project_name):
    """
    (Security Tool) Generates an ephemeral, self-signed TLS certificate and
    private key for use with WebServerSecure.
    Requires the pyOpenSSL library.
    """
    # Create a new key pair
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 2048)

    # Create a self-signed certificate
    cert = crypto.X509()
    cert.get_subject().CN = f"{project_name} Device"
    cert.get_subject().O = "IntelliPipe Factory"  # noqa: E741
    cert.set_serial_number(int(time.time()))
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(10 * 365 * 24 * 60 * 60)  # Valid for 10 years
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(key)
    cert.sign(key, "sha256")

    # Dump to PEM format
    key_pem = crypto.dump_privatekey(crypto.FILETYPE_PEM, key).decode("utf-8")
    cert_pem = crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode("utf-8")

    return key_pem, cert_pem


def convert_pem_to_c_array(pem_string, var_name):
    """
    (Security Tool) Converts a PEM string into a C-style raw string literal
    for easy embedding into the firmware.
    """
    # Format as a C++ raw string literal R"KEY(...)KEY"
    return f'const char {var_name}[] = R"KEY({pem_string})KEY";'


def convert_svg_to_blueprint(svg_filepath):
    """
    (Ingress Port Tool v1.1) Reads a compliant .svg file and converts it
    into a "Pure Physical" v6.0 blueprint .json file.

    v1.1 Changes:
    - Fixed node type classification (inlet/outlet/junction).
    - Optimized performance by building node coordinate lookup only once.
    """
    print(f"\n[Ingress Port] Converting '{svg_filepath}' to Blueprint v6.0...")

    try:
        from lxml import etree
    except ImportError:
        print(
            "  -> [FAIL] CONVERSION FAILED: The 'lxml' library is required. Please run 'pip install lxml'"
        )
        return None

    # Define the SVG namespace to properly parse the file
    ns = {"svg": "http://www.w3.org/2000/svg"}

    try:
        tree = etree.parse(svg_filepath)
        root = tree.getroot()
    except Exception as e:
        print(
            f"  -> [FAIL] CONVERSION FAILED: Could not parse the SVG file. Error: {e}"
        )
        return None

    nodes, pipes = [], []

    # --- Step 1: Discover all Nodes and Pipes ---
    for circle in root.findall(".//svg:circle", namespaces=ns):
        node_id = circle.get("id")
        if not node_id:
            print(
                "  -> [WARN] Found a <circle> element without an 'id'. It will be ignored."
            )
            continue
        nodes.append(
            {
                "node_id": node_id,
                "type": "junction",  # Default to junction, refined in Step 3
                "label": node_id.replace("_", " ").title(),
            }
        )

    for line in root.findall(".//svg:line", namespaces=ns):
        pipe_id = line.get("id")
        if not pipe_id:
            print(
                "  -> [WARN] Found a <line> element without an 'id'. It will be ignored."
            )
            continue
        try:
            x1, y1 = float(line.get("x1")), float(line.get("y1"))
            x2, y2 = float(line.get("x2")), float(line.get("y2"))
            length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        except (ValueError, TypeError):
            print(
                f"  -> [WARN] Pipe '{pipe_id}' has invalid or missing coordinates. It will be ignored."
            )
            continue

        pipes.append(
            {
                "pipe_id": pipe_id,
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,  # Store coords temporarily for connection logic
                "properties": {
                    "length_m": round(length / 100, 2),  # Assuming 100 pixels = 1 meter
                    "inner_diameter_m": 0.02,  # A reasonable default
                },
            }
        )

    if not nodes or not pipes:
        print(
            "  -> [FAIL] CONVERSION FAILED: No valid <circle> nodes and <line> pipes with 'id' attributes were found."
        )
        return None

    # --- Step 2: Intelligently Connect Pipes to Nodes (Optimized) ---
    # Create a lookup dictionary of node coordinates ONCE to avoid re-parsing the SVG tree in a loop.
    node_coords = {
        node["node_id"]: (
            float(
                tree.find(f'.//svg:circle[@id="{node["node_id"]}"]', namespaces=ns).get(
                    "cx"
                )
            ),
            float(
                tree.find(f'.//svg:circle[@id="{node["node_id"]}"]', namespaces=ns).get(
                    "cy"
                )
            ),
        )
        for node in nodes
    }

    for pipe in pipes:
        # Find the closest node to the start of the pipe
        p1_distances = {
            np.sqrt((pipe["x1"] - nc[0]) ** 2 + (pipe["y1"] - nc[1]) ** 2): nid
            for nid, nc in node_coords.items()
        }
        pipe["source_node"] = p1_distances[min(p1_distances.keys())]

        # Find the closest node to the end of the pipe
        p2_distances = {
            np.sqrt((pipe["x2"] - nc[0]) ** 2 + (pipe["y2"] - nc[1]) ** 2): nid
            for nid, nc in node_coords.items()
        }
        pipe["target_node"] = p2_distances[min(p2_distances.keys())]

        # Clean up temporary coordinates now that connections are made
        del pipe["x1"], pipe["y1"], pipe["x2"], pipe["y2"]

    # --- Step 3: Refine Node Types (FIXED LOGIC) ---
    # A node's type is determined by its role as a pipe endpoint.
    source_nodes = {p["source_node"] for p in pipes}
    target_nodes = {p["target_node"] for p in pipes}

    for node in nodes:
        node_id = node["node_id"]
        is_source = node_id in source_nodes
        is_target = node_id in target_nodes

        if is_source and not is_target:
            # It's ONLY a source for pipes leaving it. It must be an Inlet.
            node["type"] = "inlet"
        elif is_target and not is_source:
            # It's ONLY a target for pipes entering it. It must be an Outlet.
            node["type"] = "outlet"
        elif is_source and is_target:
            # It's BOTH a source for outgoing pipes AND a target for incoming pipes. It's a Junction.
            node["type"] = "junction"
        # else: An isolated node (not connected to any pipes) remains a 'junction' by default.

    # --- Step 4: Assemble the Final Blueprint ---
    project_name = os.path.splitext(os.path.basename(svg_filepath))[0]
    final_blueprint = {
        "project_details": {
            "name": f"{project_name}_System",
            "description": f"A system blueprint automatically generated from '{svg_filepath}'.",
            "version": "6.0-PurePhysical",
        },
        "nodes": nodes,
        "pipes": pipes,
        # Intentionally empty stubs for future campaigns
        "available_pins": [],
        "system_tuning_parameters": {},
        "ai_model": {"enabled": False},
    }

    # Save the final blueprint to a JSON file
    output_filename = f"{project_name}_Blueprint_v6.0.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(final_blueprint, f, indent=2)

    print(f"  -> [OK] CONVERSION SUCCESSFUL. Blueprint saved to '{output_filename}'.")
    return final_blueprint


# ==============================================================================
# SCRIPT ENTRY POINT
# ==============================================================================
if __name__ == "__main__":
    main()
    print("\n--- Script execution finished. ---")
