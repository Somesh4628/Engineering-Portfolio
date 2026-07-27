"""Module docstring."""
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from gaitform.sensors.pressure_parser import PressureMapResult


@dataclass
class RigidityZone:
    zone: str
    target: str


@dataclass
class OrthoticParams:
    arch_height_mm: float
    heel_cup_depth_mm: float
    medial_post_deg: float
    lateral_post_deg: float
    met_pad_position_mm: float
    rigidity_zones: List[RigidityZone]
    flags_for_review: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class OrthoticParameterMapper:
    def map_metrics_to_orthotic(
        self, metrics: Dict[str, Any], pressure: Optional[PressureMapResult] = None
    ) -> Dict[str, OrthoticParams]:

        def calculate_for_foot(pronation: float, side: str) -> OrthoticParams:
            foot_length = metrics.get(
                f"foot_length_{side}_mm",
                metrics.get("foot_length_mm", 260.0)
            )
            flags = []

            # --- Cadence check ---
            if metrics.get("cadence_steps_per_min", 0.0) == 0.0:
                flags.append(
                    "Warning: Cadence is 0. Peak detection failed or subject is stationary."
                )

            # --- Stance/swing computation check ---
            if not metrics.get("stance_swing_computed", False):
                flags.append(
                    "Stance/swing time fixed at 60/40 protocol assumption "
                    "(insufficient heel strike pairs detected for dynamic computation). "
                    "Not a patient-specific measurement."
                )

            # --- Pronation confidence check ---
            conf_key = "pronation_confidence_l" if side == "left" else "pronation_confidence_r"
            if metrics.get(conf_key, 1.0) < 0.6:
                flags.append(
                    f"{side.capitalize()} pronation angle low confidence "
                    f"({metrics.get(conf_key, 0.0):.2f}). Landmark visibility poor — "
                    f"value used for seeding only. Manual goniometer assessment required."
                )

            # --- Arch Height ---
            # Base arch is scaled by patient height (taller patients have slightly larger arches)
            patient_height = metrics.get("patient_height_m", 1.75)
            if patient_height is None or patient_height <= 0:
                patient_height = 1.75

            # Base arch is 15.0 for a 1.75m person. Scale proportionally.
            base_arch = 15.0 * (patient_height / 1.75)

            # Add correction for pronation
            arch_height = base_arch + max(0, (pronation - 5.0) * 0.5)

            if pronation > 15.0:
                flags.append(
                    f"High {side} pronation angle detected. Flag for clinician review."
                )

            # Clamp arch height to safe mechanical limits (10mm - 25mm)
            arch_height = max(10.0, min(25.0, arch_height))

            # --- Heel Cup Depth ---
            heel_cup_depth = 15.0 if pronation > 8.0 else 10.0

            # --- Medial / Lateral Posts ---
            medial_post = max(0.0, (pronation - 5.0) / 2.0)
            lateral_post = (
                max(0.0, (-pronation - 2.0) / 2.0) if pronation < -2.0 else 0.0
            )

            # Clamp posts (max 4 degrees correction without clinical intervention)
            if medial_post > 4.0:
                flags.append(
                    "Medial post correction > 4 deg requested. Capped at 4 deg for safety. Clinician review required."
                )
            medial_post = max(0.0, min(4.0, medial_post))

            # --- Metatarsal Pad Position ---
            met_pad_pos = foot_length * 0.65

            # --- Rigidity Zones ---
            if pronation > 8.0:
                arch_rigidity = "firm"
            elif pronation < 0.0:
                arch_rigidity = "soft"
            else:
                arch_rigidity = "medium"

            # --- Pressure override ---
            # If pressure mat data is available, override zone rigidity targets based on
            # measured peak plantar pressure rather than the pronation proxy.
            # Clinical rationale: >200kPa peak pressure indicates high-load zone requiring
            # firm support. Source: Bus et al., Diabetes Metab Res Rev, 2016.
            if pressure is not None:
                heel_rigidity = "firm" if pressure.heel_peak_kpa > 200 else "medium"
                arch_rigidity_override = (
                    "firm" if pressure.midfoot_peak_kpa > 200 else arch_rigidity
                )
                forefoot_rigidity = (
                    "firm" if pressure.forefoot_peak_kpa > 200 else "soft"
                )
                flags.append(
                    f"Pressure mat data used for zoning: heel={pressure.heel_peak_kpa:.0f}kPa, "
                    f"midfoot={pressure.midfoot_peak_kpa:.0f}kPa, forefoot={pressure.forefoot_peak_kpa:.0f}kPa"
                )
                zones = [
                    RigidityZone(zone="heel", target=heel_rigidity),
                    RigidityZone(zone="midfoot", target=arch_rigidity_override),
                    RigidityZone(zone="forefoot", target=forefoot_rigidity),
                ]
            else:
                zones = [
                    RigidityZone(zone="heel", target="firm"),
                    RigidityZone(zone="midfoot", target=arch_rigidity),
                    RigidityZone(zone="forefoot", target="soft"),
                ]

            return OrthoticParams(
                arch_height_mm=round(arch_height, 2),
                heel_cup_depth_mm=round(heel_cup_depth, 2),
                medial_post_deg=round(medial_post, 2),
                lateral_post_deg=round(lateral_post, 2),
                met_pad_position_mm=round(met_pad_pos, 2),
                rigidity_zones=zones,
                flags_for_review=flags,
            )

        pronation_l = metrics.get("pronation_angle_l_deg")
        pronation_r = metrics.get("pronation_angle_r_deg")

        # If either value is None or invalid, use 0.0 (neutral — no correction)
        # and add a clinician flag. Never silently guess a corrective value.
        _flags_missing = []
        if pronation_l is None or not isinstance(pronation_l, (int, float)):
            pronation_l = 0.0
            _flags_missing.append(
                "Left pronation angle unavailable — landmark visibility too low. "
                "No correction applied. Manual assessment required."
            )
        if pronation_r is None or not isinstance(pronation_r, (int, float)):
            pronation_r = 0.0
            _flags_missing.append(
                "Right pronation angle unavailable — landmark visibility too low. "
                "No correction applied. Manual assessment required."
            )

        result = {
            "left": calculate_for_foot(pronation_l, "left"),
            "right": calculate_for_foot(pronation_r, "right"),
        }

        # Attach any missing-data flags to both sides
        for flag in _flags_missing:
            result["left"].flags_for_review.append(flag)
            result["right"].flags_for_review.append(flag)

        return result
