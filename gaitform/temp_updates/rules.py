from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional
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
            self, metrics: Dict[str, Any], pressure: Optional[PressureMapResult] = None) -> Dict[str, OrthoticParams]:

        foot_length = metrics.get("foot_length_mm", 260.0)

        def calculate_for_foot(pronation: float, side: str) -> OrthoticParams:
            flags = []

            # --- Cadence check ---
            if metrics.get("cadence_steps_per_min", 0.0) == 0.0:
                flags.append(
                    "Warning: Cadence is 0. Peak detection failed or subject is stationary."
                )

            # --- Arch Height ---
            arch_height = 15.0 + max(0, (pronation - 5.0) * 0.5)
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
                arch_rigidity_override = "firm" if pressure.midfoot_peak_kpa > 200 else arch_rigidity
                forefoot_rigidity = "firm" if pressure.forefoot_peak_kpa > 200 else "soft"
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

        pronation_L = metrics.get("pronation_angle_L_deg", 5.0)
        pronation_R = metrics.get("pronation_angle_R_deg", 5.0)

        return {
            "left": calculate_for_foot(pronation_L, "left"),
            "right": calculate_for_foot(pronation_R, "right"),
        }
