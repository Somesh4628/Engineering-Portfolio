# Location: soul_engine.py (Complete Replacement)

from __future__ import annotations
import json
from pydantic import BaseModel, Field, field_validator
from typing import List, Literal, Optional
from collections import Counter
import uuid

import networkx as nx

# --- Heuristic Constants ---
CRITICAL_PIPE_LENGTH_M = 10.0  # A pipe longer than this requires a sensor.
CHOKE_POINT_DIAMETER_RATIO = 2.0  # Ratio at which a diameter reduction is flagged.
MIN_VALVE_SENSOR_DISTANCE_M = 0.15  # Minimum distance between a valve and a sensor.

# --- Core Building Blocks ---


class ProjectDetails(BaseModel):
    blueprint_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str = Field(..., description="The unique name of the system design.")
    description: Optional[str] = None
    version: str = Field(..., description="Version of the system blueprint.")


# --- CAMPAIGN 3, PHASE 3.2 UPGRADE ---
class PrescriptiveAction(BaseModel):
    """Defines a recommended action for a specific fault class."""

    fault_class: str  # The 'output_class' from the AiModel this action corresponds to.
    recommendation: str  # The human-readable recommended action.
    target_node_id: Optional[str] = (
        None  # Optional target for the action (e.g., a valve to close).
    )


class AiModel(BaseModel):
    enabled: bool
    model_file: str = Field(..., pattern=r".*\.h$")
    output_classes: List[str]
    prescriptive_actions: Optional[List[PrescriptiveAction]] = (
        None  # List of recommended actions.
    )


class NetworkInfo(BaseModel):
    ssid: str
    password: str
    telemetry_endpoint: Optional[str] = None


class Node(BaseModel):
    node_id: str
    type: Literal["inlet", "junction", "outlet"]
    component_type: Literal[
        "Default",
        "Tee-Junction",
        "90-Degree-Elbow",
        "Tap",
        "Cross-Junction",
        "Wye-Split",
        "U-Bend",
        "Straight-Coupling",
        "Ball-Valve",
        "Gate-Valve",
        "Check-Valve",
        "Solenoid-Valve",
    ]
    label: str
    orientation: Optional[Literal[0, 90, 180, 270]] = 0
    is_critical: Optional[bool] = False


class FlowSensor(BaseModel):
    sensor_id: str
    label: str
    gpio_pin: int = Field(..., ge=-1)
    k_factor_ppl: float = Field(..., gt=0)


class PipeProperties(BaseModel):
    length_m: float = Field(..., gt=0)
    inner_diameter_m: float = Field(..., gt=0)


class Pipe(BaseModel):
    pipe_id: str
    source_node: str
    target_node: str
    flow_sensor: Optional[FlowSensor] = None
    properties: PipeProperties


# --- System Tuning and Profiles ---


class TuningProfile(BaseModel):
    id: str
    label: str
    update_interval_ms: int
    median_window_size: int
    ema_alpha: float
    calibration_sample_count: int
    deviation_std_dev_factor: float
    calibration_min_start_flow_lps: float
    calib_start_confirm_cycles: int
    leak_confirmation_cycles: int
    drift_confirmation_cycles: int
    max_consecutive_faults: int
    near_zero_flow_lps: float
    max_realistic_flow_lps: float
    stuck_sensor_cycles: int
    max_log_events: int
    debug_validity_level: int


class SystemTuning(BaseModel):
    default_profile_id: str
    profiles: List[TuningProfile]

    @field_validator("default_profile_id")
    @classmethod
    def default_profile_must_exist(cls, v, info):
        if "profiles" in info.data:
            profile_ids = {profile.id for profile in info.data["profiles"]}
            if v not in profile_ids:
                raise ValueError(
                    f"Default profile ID '{v}' not found in defined profiles."
                )
        return v


# --- The Master Blueprint Class ---


class SystemBlueprint(BaseModel):
    project_details: ProjectDetails
    ai_model: AiModel
    network_info: Optional[NetworkInfo] = None
    nodes: List[Node]
    pipes: List[Pipe]
    system_tuning_parameters: SystemTuning
    available_pins: Optional[List[int]] = None
    optimization_report: List[str] = []

    # --- High-Level System-Wide Validators ---
    @field_validator("pipes")
    @classmethod
    def pipe_node_ids_must_exist_in_nodes(cls, v, info):
        if "nodes" not in info.data:
            return v
        node_ids = {node.node_id for node in info.data["nodes"]}
        for pipe in v:
            if pipe.source_node not in node_ids:
                raise ValueError(
                    f"Pipe '{pipe.pipe_id}' has an invalid source_node '{pipe.source_node}'."
                )
            if pipe.target_node not in node_ids:
                raise ValueError(
                    f"Pipe '{pipe.pipe_id}' has an invalid target_node '{pipe.target_node}'."
                )
        return v

    @field_validator("pipes", mode="after")
    @classmethod
    def system_must_be_a_single_connected_component(cls, v, info):
        nodes, pipes = info.data.get("nodes", []), v
        if not nodes or not pipes:
            return v
        graph = nx.Graph()
        for node in nodes:
            graph.add_node(node.node_id)
        for pipe in pipes:
            graph.add_edge(pipe.source_node, pipe.target_node)
        if not nx.is_connected(graph):
            components = list(nx.connected_components(graph))
            largest_component = max(components, key=len)
            all_node_ids = {node.node_id for node in nodes}
            orphan_nodes_example = list(all_node_ids - largest_component)
            raise ValueError(
                f"The system topology is not a single connected graph. For example, the section with node(s) {orphan_nodes_example[:3]} is disconnected."
            )
        return v

    @field_validator("nodes", mode="after")
    @classmethod
    def components_must_have_correct_pipe_counts(cls, v, info):
        pipes, nodes = info.data.get("pipes", []), v
        if not pipes or not nodes:
            return v
        connection_counts = {node.node_id: 0 for node in nodes}
        for pipe in pipes:
            if pipe.source_node in connection_counts:
                connection_counts[pipe.source_node] += 1
            if pipe.target_node in connection_counts:
                connection_counts[pipe.target_node] += 1
        for node in nodes:
            component, degree = node.component_type, connection_counts.get(
                node.node_id, 0
            )
            if component == "Tee-Junction" and degree != 3:
                raise ValueError(
                    f"Component Error at '{node.node_id}': T-Junctions must have exactly 3 connected pipes, but has {degree}."
                )
            two_port_components = [
                "90-Degree-Elbow",
                "Ball-Valve",
                "Tap",
                "Gate-Valve",
                "Check-Valve",
                "Solenoid-Valve",
            ]
            if component in two_port_components and degree != 2:
                raise ValueError(
                    f"Component Error at '{node.node_id}': A '{component}' must have exactly 2 connected pipes, but has {degree}."
                )
        return v

    @field_validator("pipes", mode="after")
    @classmethod
    def valve_sensor_spacing_is_adequate(cls, v, info):
        nodes = info.data.get("nodes", [])
        if not nodes or not v:
            return v
        node_map = {node.node_id: node for node in nodes}
        valve_types = {
            "Ball-Valve",
            "Gate-Valve",
            "Solenoid-Valve",
            "Check-Valve",
            "Tap",
        }
        for pipe in v:
            if pipe.flow_sensor:
                source_node = node_map.get(pipe.source_node)
                target_node = node_map.get(pipe.target_node)
                source_is_valve = (
                    source_node and source_node.component_type in valve_types
                )
                target_is_valve = (
                    target_node and target_node.component_type in valve_types
                )
                if (
                    source_is_valve or target_is_valve
                ) and pipe.properties.length_m < MIN_VALVE_SENSOR_DISTANCE_M:
                    valve_node_id = (
                        source_node.node_id if source_is_valve else target_node.node_id
                    )
                    raise ValueError(
                        f"Physical Design Flaw: Sensor '{pipe.flow_sensor.sensor_id}' on pipe '{pipe.pipe_id}' is too close to valve '{valve_node_id}'. Minimum distance is {MIN_VALVE_SENSOR_DISTANCE_M * 100:.0f}cm, but pipe length is only {pipe.properties.length_m * 100:.0f}cm."
                    )
        return v

    # --- CAMPAIGN 2: INTELLIGENT ENGINEER METHODS ---

    def complete_and_optimize(self):
        """The master function that runs all optimization and completion routines."""
        self.optimization_report = []
        self._optimize_observability()
        self._optimize_long_pipes()
        self._optimize_ambiguous_junctions()
        self._optimize_critical_nodes()
        self._analyze_choke_points()
        self._generate_bill_of_materials()

    def _optimize_observability(self):
        """Phase 2.1-A: Enforces the 'Bookend Rule' on all paths."""
        graph = nx.DiGraph()
        for pipe in self.pipes:
            graph.add_edge(pipe.source_node, pipe.target_node, pipe_id=pipe.pipe_id)
        inlets = {node.node_id for node in self.nodes if node.type == "inlet"}
        outlets = {node.node_id for node in self.nodes if node.type == "outlet"}
        pipe_map = {pipe.pipe_id: pipe for pipe in self.pipes}
        for inlet_node in inlets:
            for outlet_node in outlets:
                for path in nx.all_simple_paths(
                    graph, source=inlet_node, target=outlet_node
                ):
                    if len(path) < 2:
                        continue
                    first_pipe_id = graph[path[0]][path[1]]["pipe_id"]
                    if not pipe_map[first_pipe_id].flow_sensor:
                        self._add_sensor_to_pipe(
                            pipe_map[first_pipe_id], "Bookend Rule (Start)"
                        )
                    last_pipe_id = graph[path[-2]][path[-1]]["pipe_id"]
                    if not pipe_map[last_pipe_id].flow_sensor:
                        self._add_sensor_to_pipe(
                            pipe_map[last_pipe_id], "Bookend Rule (End)"
                        )

    def _optimize_long_pipes(self):
        """Phase 2.1-B: Adds sensors to long pipes that lack them."""
        for pipe in self.pipes:
            if (
                pipe.properties.length_m > CRITICAL_PIPE_LENGTH_M
                and not pipe.flow_sensor
            ):
                self._add_sensor_to_pipe(pipe, "Long Pipe Rule")

    def _optimize_ambiguous_junctions(self):
        """Phase 2.1-C: Enforces 100% sensor coverage on complex junctions."""
        connection_counts = {node.node_id: 0 for node in self.nodes}
        for pipe in self.pipes:
            connection_counts[pipe.source_node] += 1
            connection_counts[pipe.target_node] += 1
        for node in self.nodes:
            if node.type == "junction" and connection_counts.get(node.node_id, 0) > 3:
                for pipe in self.pipes:
                    if (
                        pipe.source_node == node.node_id
                        or pipe.target_node == node.node_id
                    ):
                        if not pipe.flow_sensor:
                            self._add_sensor_to_pipe(pipe, "Ambiguous Junction Rule")

    def _optimize_critical_nodes(self):
        """Phase 2.2: Enforces sensor coverage on all pipes feeding a critical node."""
        critical_node_ids = {node.node_id for node in self.nodes if node.is_critical}
        if not critical_node_ids:
            return
        for pipe in self.pipes:
            if pipe.target_node in critical_node_ids and not pipe.flow_sensor:
                self._add_sensor_to_pipe(pipe, "Critical Node Rule")

    def _analyze_choke_points(self):
        """Phase 2.3-A: Identifies and warns about potential hydraulic choke points."""
        graph = nx.DiGraph()
        pipe_lookup = {}
        for pipe in self.pipes:
            graph.add_edge(pipe.source_node, pipe.target_node)
            pipe_lookup[(pipe.source_node, pipe.target_node)] = pipe
        for node in self.nodes:
            if node.type == "junction":
                incoming_pipes = [
                    pipe_lookup[edge] for edge in graph.in_edges(node.node_id)
                ]
                outgoing_pipes = [
                    pipe_lookup[edge] for edge in graph.out_edges(node.node_id)
                ]
                for in_pipe in incoming_pipes:
                    for out_pipe in outgoing_pipes:
                        in_dia, out_dia = (
                            in_pipe.properties.inner_diameter_m,
                            out_pipe.properties.inner_diameter_m,
                        )
                        if in_dia / out_dia > CHOKE_POINT_DIAMETER_RATIO:
                            self.optimization_report.append(
                                f"WARNING: Potential choke point at junction '{node.node_id}'. Pipe '{in_pipe.pipe_id}' ({in_dia*1000:.1f}mm) feeds into narrower pipe '{out_pipe.pipe_id}' ({out_dia*1000:.1f}mm)."
                            )

    def _generate_bill_of_materials(self):
        """Phase 2.4-B: The 'Scribe'. Generates a BOM and appends it to the report."""
        bom = ["--- BILL OF MATERIALS ---"]
        component_counts = Counter(
            node.component_type
            for node in self.nodes
            if node.component_type != "Default"
        )
        if component_counts:
            bom.append("Components:")
            for component, count in sorted(component_counts.items()):
                bom.append(f"  - {component}: {count} pcs")
        sensor_count = sum(1 for pipe in self.pipes if pipe.flow_sensor)
        if sensor_count > 0:
            bom.append("Sensors:")
            bom.append(f"  - Flow Sensor: {sensor_count} pcs")
        pipe_lengths = {}
        for pipe in self.pipes:
            dia_mm = pipe.properties.inner_diameter_m * 1000
            if dia_mm not in pipe_lengths:
                pipe_lengths[dia_mm] = 0
            pipe_lengths[dia_mm] += pipe.properties.length_m
        if pipe_lengths:
            bom.append("Piping:")
            for dia, length in sorted(pipe_lengths.items()):
                bom.append(f"  - Pipe ({dia:.1f}mm ID): {length:.2f} meters")
        if len(bom) > 1:
            self.optimization_report.extend(bom)

    def _add_sensor_to_pipe(self, pipe: Pipe, reason: str):
        """Helper function to add a standardized sensor to a pipe and log it."""
        if pipe.flow_sensor and pipe.flow_sensor.sensor_id.endswith("_OPT"):
            return
        new_sensor_id = f"S_{pipe.pipe_id}_OPT"
        pipe.flow_sensor = FlowSensor(
            sensor_id=new_sensor_id,
            label=f"Optimized Sensor for Pipe {pipe.pipe_id}",
            gpio_pin=-1,
            k_factor_ppl=450.0,
        )
        self.optimization_report.append(
            f"'{reason}': Added sensor '{new_sensor_id}' to pipe '{pipe.pipe_id}'."
        )

    def assign_pins(self):
        """Assigns unique GPIO pins to all sensors that need one."""
        manual_pins = set()
        for pipe in self.pipes:
            if (
                pipe.flow_sensor
                and pipe.flow_sensor.gpio_pin is not None
                and pipe.flow_sensor.gpio_pin >= 0
            ):
                if pipe.flow_sensor.gpio_pin in manual_pins:
                    raise ValueError(
                        f"Hardware conflict: GPIO pin {pipe.flow_sensor.gpio_pin} assigned to multiple sensors."
                    )
                manual_pins.add(pipe.flow_sensor.gpio_pin)

        sensors_needing_assignment = [
            pipe
            for pipe in self.pipes
            if pipe.flow_sensor
            and (pipe.flow_sensor.gpio_pin is None or pipe.flow_sensor.gpio_pin < 0)
        ]

        if not self.available_pins:
            if sensors_needing_assignment:
                raise ValueError(
                    "Blueprint requires pin assignments, but no 'available_pins' were provided."
                )
            return

        pin_pool = iter(pin for pin in self.available_pins if pin not in manual_pins)
        for pipe in sensors_needing_assignment:
            try:
                assigned_pin = next(pin_pool)
                pipe.flow_sensor.gpio_pin = assigned_pin
            except StopIteration:
                raise ValueError(
                    f"Hardware conflict: Not enough available pins. Failed to assign pin to sensor '{pipe.flow_sensor.sensor_id}'."
                )

        # Final sanity check: ensure no duplicates after assignment
        all_assigned = set()
        for pipe in self.pipes:
            if (
                pipe.flow_sensor
                and pipe.flow_sensor.gpio_pin is not None
                and pipe.flow_sensor.gpio_pin >= 0
            ):
                if pipe.flow_sensor.gpio_pin in all_assigned:
                    raise ValueError(
                        f"Hardware conflict detected after assignment: GPIO pin {pipe.flow_sensor.gpio_pin} is duplicated."
                    )
                all_assigned.add(pipe.flow_sensor.gpio_pin)

    # --- File I/O Methods ---
    @classmethod
    def from_file(cls, filepath: str) -> "SystemBlueprint":
        """Loads a blueprint from a JSON file."""
        with open(filepath, "r") as f:
            data = json.load(f)
        return cls(**data)

    def to_file(self, filepath: str):
        """Saves the blueprint to a JSON file with nice formatting."""

        class UUIDEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, uuid.UUID):
                    return str(obj)
                return json.JSONEncoder.default(self, obj)

        json_string = json.dumps(self.model_dump(), indent=2, cls=UUIDEncoder)
        with open(filepath, "w") as f:
            f.write(json_string)
