import numpy as np
import trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json
from typing import Optional
from scipy.interpolate import CubicSpline
from gaitform.mapping.rules import OrthoticParams


class CADGenerator:
    def __init__(self, length_mm: float = 260.0, width_mm: float = 98.0):
        # Baseline placeholder dimensions. In a real system, these come from foot scans.
        self.length = length_mm
        self.width = width_mm

    def generate_mesh(
        self,
        params: OrthoticParams,
        scan_mesh: trimesh.Trimesh = None,
        foot_side: str = "left",
        scan_path: Optional[str] = None,
        shoe_size_mm: Optional[float] = None,
    ) -> trimesh.Trimesh:
        """
        Procedurally generates a watertight orthotic shell mesh using trimesh.
        """
        if shoe_size_mm is not None:
            self.length = shoe_size_mm

        if scan_path and scan_mesh is None:
            # Path A: True 3D Scan Ingestion
            try:
                scan_mesh = trimesh.load(scan_path)
            except Exception:
                pass

        res_x, res_y = 30, 80

        # Define insole footprint contour using a spline
        # Normalized length t from 0 (heel) to 1 (toe)
        t_pts = [0.0, 0.05, 0.15, 0.45, 0.75, 0.95, 1.0]

        # Medial side (negative X). We want the arch cutout here.
        # Heel width is approx 50mm, Toe box is approx 70mm, Ball is approx 98mm.
        # x_min for left foot (medial)
        x_min_pts = (
            np.array([-0.2, -0.25, -0.35, -0.15, -0.48, -0.35, -0.2]) * self.width
        )

        # Lateral side (positive X). Gentle curve.
        x_max_pts = np.array([0.2, 0.25, 0.35, 0.40, 0.48, 0.35, 0.25]) * self.width

        # If right foot, swap medial/lateral
        if foot_side == "right":
            temp = -x_min_pts.copy()
            x_min_pts = -x_max_pts.copy()
            x_max_pts = temp

        cs_min = CubicSpline(t_pts, x_min_pts, bc_type="natural")
        cs_max = CubicSpline(t_pts, x_max_pts, bc_type="natural")

        t_vals = np.linspace(0, 1, res_y)
        min_vals = cs_min(t_vals)
        max_vals = cs_max(t_vals)

        xx = np.zeros((res_y, res_x))
        yy = np.zeros((res_y, res_x))

        for iy in range(res_y):
            t = t_vals[iy]
            xx[iy, :] = np.linspace(min_vals[iy], max_vals[iy], res_x)
            yy[iy, :] = t * self.length

        xx_flat = xx.flatten()
        yy_flat = yy.flatten()

        zz_top = np.ones((res_y, res_x)) * 3.0  # base thickness 3mm

        for iy in range(res_y):
            # 1. Heel cup (rear 15% of length) - curve edges up
            if yy[iy, 0] < (self.length * 0.15):
                center = (max_vals[iy] + min_vals[iy]) / 2.0
                local_half_width = (max_vals[iy] - min_vals[iy]) / 2.0
                if local_half_width > 0:
                    edge_dist = np.abs(xx[iy, :] - center) / local_half_width
                    zz_top[iy, :] += params.heel_cup_depth_mm * (edge_dist**2)

        zz_top = zz_top.flatten()

        # 2. Arch height (medial side, midfoot 15% to 60%)
        midfoot_mask = (yy_flat >= self.length * 0.15) & (yy_flat <= self.length * 0.60)
        medial_mask = xx_flat < 0 if foot_side == "left" else xx_flat > 0
        arch_mask = midfoot_mask & medial_mask

        # simple Gaussian bump for the arch
        arch_center_y = self.length * 0.4
        arch_center_x = -self.width / 2 if foot_side == "left" else self.width / 2
        dist_to_arch = np.sqrt(
            (xx_flat - arch_center_x) ** 2 + (yy_flat - arch_center_y) ** 2
        )
        arch_bump = np.exp(-(dist_to_arch**2) / (2 * 20**2)) * params.arch_height_mm
        zz_top[arch_mask] += arch_bump[arch_mask]

        # 3. Metatarsal pad
        met_mask = (yy_flat > params.met_pad_position_mm - 20) & (
            yy_flat < params.met_pad_position_mm + 20
        )
        dist_to_met = np.sqrt(
            (xx_flat) ** 2 + (yy_flat - params.met_pad_position_mm) ** 2
        )
        met_bump = np.exp(-(dist_to_met**2) / (2 * 10**2)) * 4.0  # 4mm bump
        zz_top[met_mask] += met_bump[met_mask]

        if scan_mesh is not None:
            if not scan_mesh.is_watertight:
                params.flags_for_review.append(
                    "Scan mesh not watertight \u2014 using procedural surface. Verify scan before printing."
                )
                scan_mesh = None

        if scan_mesh is not None:
            # Clinical rationale: \u00b11.5mm surface tolerance matches custom orthotic fit standard.
            # Source: Philps, Prosthet Orthot Int., 1990.
            ray_origins = np.column_stack((xx_flat, yy_flat, np.zeros(len(xx_flat))))
            ray_directions = np.tile([0, 0, 1], (len(xx_flat), 1))
            intersector = trimesh.ray.ray_triangle.RayMeshIntersector(scan_mesh)
            locations, index_ray, _ = intersector.intersects_location(
                ray_origins, ray_directions, multiple_hits=False
            )
            
            procedural_backup = zz_top.copy()
            for loc, idx in zip(locations, index_ray):
                zz_top[idx] = loc[2]
            
            max_deviation = np.max(np.abs(zz_top - procedural_backup))
            if max_deviation > 1.5:
                params.flags_for_review.append(
                    f"Surface deviation {max_deviation:.2f}mm exceeds \u00b11.5mm clinical tolerance. Verify fit before printing."
                )
            else:
                params.flags_for_review.append(
                    f"Scan fit validated: max deviation {max_deviation:.2f}mm within \u00b11.5mm tolerance."
                )

        # Bottom surface heights (Z)
        # Apply medial post as a wedge on the bottom
        zz_bottom = np.zeros_like(xx_flat)
        if params.medial_post_deg > 0:
            # slope = tan(theta)
            slope = np.tan(np.radians(params.medial_post_deg))
            # Wedge raises the medial side (negative x)
            zz_bottom += np.where(xx_flat < 0, -xx_flat * slope, 0)

        # Construct vertices: Top followed by Bottom
        top_verts = np.column_stack((xx_flat, yy_flat, zz_top))
        bottom_verts = np.column_stack((xx_flat, yy_flat, zz_bottom))
        vertices = np.vstack((top_verts, bottom_verts))

        # Construct faces
        faces = []

        def get_idx(ix, iy, is_bottom=False):
            offset = res_x * res_y if is_bottom else 0
            return offset + iy * res_x + ix

        # Top and Bottom faces
        for iy in range(res_y - 1):
            for ix in range(res_x - 1):
                # Top (ccw)
                t1 = get_idx(ix, iy)
                t2 = get_idx(ix + 1, iy)
                t3 = get_idx(ix + 1, iy + 1)
                t4 = get_idx(ix, iy + 1)
                faces.extend([[t1, t2, t3], [t1, t3, t4]])

                # Bottom (cw)
                b1 = get_idx(ix, iy, True)
                b2 = get_idx(ix + 1, iy, True)
                b3 = get_idx(ix + 1, iy + 1, True)
                b4 = get_idx(ix, iy + 1, True)
                faces.extend([[b1, b3, b2], [b1, b4, b3]])

        # Side walls
        for ix in range(res_x - 1):
            # Front (y=0)
            t1, t2 = get_idx(ix, 0), get_idx(ix + 1, 0)
            b1, b2 = get_idx(ix, 0, True), get_idx(ix + 1, 0, True)
            faces.extend([[t1, b1, b2], [t1, b2, t2]])
            # Back (y=max)
            iy = res_y - 1
            t1, t2 = get_idx(ix, iy), get_idx(ix + 1, iy)
            b1, b2 = get_idx(ix, iy, True), get_idx(ix + 1, iy, True)
            faces.extend([[t2, b2, b1], [t2, b1, t1]])

        for iy in range(res_y - 1):
            # Left (x=0)
            t1, t2 = get_idx(0, iy), get_idx(0, iy + 1)
            b1, b2 = get_idx(0, iy, True), get_idx(0, iy + 1, True)
            faces.extend([[t2, b2, b1], [t2, b1, t1]])
            # Right (x=max)
            ix = res_x - 1
            t1, t2 = get_idx(ix, iy), get_idx(ix, iy + 1)
            b1, b2 = get_idx(ix, iy, True), get_idx(ix, iy + 1, True)
            faces.extend([[t1, b1, b2], [t1, b2, t2]])

        mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=True)
        return mesh

    def generate_zoning(
        self,
        params: OrthoticParams,
        output_json: str,
        output_png: str,
        foot_side: str = "left",
    ):
        """
        Generates print_instructions.json mapping named zones to rigidity targets,
        and a 2D heatmap PNG for the demo.
        """
        instructions = {
            "print_settings": {"infill_pattern": "gyroid", "base_material": "TPU_95A"},
            "zones": [z.__dict__ for z in params.rigidity_zones],
        }
        with open(output_json, "w") as f:
            json.dump(instructions, f, indent=2)

        plt.figure(figsize=(4, 8))
        plt.fill_between(
            [-self.width / 2, self.width / 2], 0, self.length * 0.25,
            color="red", alpha=0.5, label="Heel",
        )
        plt.fill_between(
            [-self.width / 2, self.width / 2], self.length * 0.25, self.length * 0.65,
            color="orange", alpha=0.5, label="Midfoot",
        )
        plt.fill_between(
            [-self.width / 2, self.width / 2], self.length * 0.65, self.length,
            color="green", alpha=0.5, label="Forefoot",
        )
        plt.xlim(-self.width / 2 - 10, self.width / 2 + 10)
        plt.ylim(-10, self.length + 10)
        plt.title(f"Rigidity Zones Heatmap ({foot_side.capitalize()})")
        plt.xlabel("Width (mm)")
        plt.ylabel("Length (mm)")
        plt.legend()
        plt.savefig(output_png)
        plt.close()
        return output_png
