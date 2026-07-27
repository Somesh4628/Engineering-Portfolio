from dataclasses import asdict, dataclass
from typing import Any, Dict, List


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
    def map_metrics_to_orthotic(self, metrics: Dict[str, Any]) -> OrthoticParams:
        flags = []
        
        # --- Cadence check ---
        if metrics.get("cadence_steps_per_min", 0.0) == 0.0:
            flags.append("Warning: Cadence is 0. Peak detection failed or subject is stationary.")
            
        # --- Arch Height ---
        # Rationale: Normal arch height is ~15-20mm. Pronation reduces apparent arch height dynamically.
        # High pronation angle (>8 deg) suggests flat feet / overpronation, requiring more arch support.
        # Rule: Base arch height 15mm + 0.5mm per degree of pronation > 5.
        pronation_L = metrics.get("pronation_angle_L_deg", 5.0)
        arch_height = 15.0 + max(0, (pronation_L - 5.0) * 0.5)
        if pronation_L > 15.0:
            flags.append("High left pronation angle detected. Flag for clinician review.")
        
        # Clamp arch height to safe mechanical limits (10mm - 25mm)
        arch_height = max(10.0, min(25.0, arch_height))
        
        # --- Heel Cup Depth ---
        # Rationale: Deeper heel cup (e.g. 15mm+) stabilizes rearfoot in overpronators.
        # Rule: Normal 10mm. If pronation > 8, deepen to 15mm.
        heel_cup_depth = 15.0 if pronation_L > 8.0 else 10.0
        
        # --- Medial / Lateral Posts ---
        # Rationale: Medial post corrects overpronation. Lateral post corrects supination.
        # Rule: 1 degree post for every 2 degrees of pronation over 5 deg. Lateral post if pronation < -2.
        medial_post = max(0.0, (pronation_L - 5.0) / 2.0)
        lateral_post = max(0.0, (-pronation_L - 2.0) / 2.0) if pronation_L < -2.0 else 0.0
        
        # Clamp posts (max 4 degrees correction without clinical intervention)
        if medial_post > 4.0:
            flags.append("Medial post correction > 4 deg requested. Capped at 4 deg for safety. Clinician review required.")
        medial_post = max(0.0, min(4.0, medial_post))
        
        # --- Metatarsal Pad Position ---
        # Rationale: Placed proximal to metatarsal heads. Dynamic based on foot length.
        # Assuming baseline foot length 260.0 for prototype (in production this comes from scan)
        foot_length = metrics.get("foot_length_mm", 260.0)
        met_pad_pos = foot_length * 0.65
        
        # --- Rigidity Zones ---
        # Rationale: 
        # - Heel: Firm for shock absorption and rearfoot control.
        # - Midfoot (Arch): Firm if overpronating to support arch, Medium for normal, Soft for supinators.
        # - Forefoot: Soft for toe-off comfort.
        if pronation_L > 8.0:
            arch_rigidity = "firm"
        elif pronation_L < 0.0:
            arch_rigidity = "soft"
        else:
            arch_rigidity = "medium"
        zones = [
            RigidityZone(zone="heel", target="firm"),
            RigidityZone(zone="midfoot", target=arch_rigidity),
            RigidityZone(zone="forefoot", target="soft")
        ]
        
        return OrthoticParams(
            arch_height_mm=round(arch_height, 2),
            heel_cup_depth_mm=round(heel_cup_depth, 2),
            medial_post_deg=round(medial_post, 2),
            lateral_post_deg=round(lateral_post, 2),
            met_pad_position_mm=round(met_pad_pos, 2),
            rigidity_zones=zones,
            flags_for_review=flags
        )
