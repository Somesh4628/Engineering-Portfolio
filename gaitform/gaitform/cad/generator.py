import json
import matplotlib
import numpy as np
import scipy.ndimage
import trimesh
from scipy.interpolate import CubicSpline
import matplotlib.pyplot as plt

matplotlib.use("Agg")
from typing import Optional
from gaitform.mapping.rules import OrthoticParams

class CADGenerator:
    def __init__(self, length_mm: float = 260.0, width_mm: float = None):
        self.length = length_mm
        # Standard anatomical ratio: foot width ≈ 37% of foot length.
        # Used as a proxy when no direct width measurement is available.
        # Source: Wunderlich & Cavanagh, Am J Phys Anthropol, 2001.
        self.width = width_mm if width_mm is not None else round(length_mm * 0.37, 1)

    def generate_mesh(
        self,
        params: OrthoticParams,
        scan_mesh: Optional[trimesh.Trimesh] = None,
        foot_side: str = "left",
    ) -> trimesh.Trimesh:
        """
        Generates a watertight orthotic shell.
        """
        res_x = 40
        res_y = 100

        t_pts = [0.0, 0.08, 0.20, 0.50, 0.75, 0.92, 1.0]

        x_min_pts = (
            np.array([-0.05, -0.22, -0.32, -0.38, -0.48, -0.28, -0.05]) * self.width
        )
        x_max_pts = np.array([0.05, 0.22, 0.32, 0.05, 0.52, 0.32, 0.05]) * self.width

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
            if yy[iy, 0] < (self.length * 0.15):
                center = (max_vals[iy] + min_vals[iy]) / 2.0
                local_half_width = (max_vals[iy] - min_vals[iy]) / 2.0
                if local_half_width > 0:
                    edge_dist = np.abs(xx[iy, :] - center) / local_half_width
                    zz_top[iy, :] += params.heel_cup_depth_mm * (edge_dist**2)

        zz_top = zz_top.flatten()

        midfoot_mask = (yy_flat >= self.length * 0.15) & (yy_flat <= self.length * 0.60)
        medial_mask = xx_flat < 0 if foot_side == "left" else xx_flat > 0
        arch_mask = midfoot_mask & medial_mask

        arch_center_y = self.length * 0.4
        arch_center_x = -self.width / 2 if foot_side == "left" else self.width / 2
        dist_to_arch = np.sqrt(
            (xx_flat - arch_center_x) ** 2 + (yy_flat - arch_center_y) ** 2
        )
        # Arch support spread scales with foot width.
        # 20mm was calibrated for a 98mm-wide foot (20/98 ≈ 0.204).
        # Scale this ratio to the actual foot width.
        arch_spread = self.width * 0.204
        arch_bump = np.exp(-(dist_to_arch**2) / (2 * arch_spread**2)) * params.arch_height_mm
        zz_top[arch_mask] += arch_bump[arch_mask]

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
            ray_origins = np.column_stack((xx_flat, yy_flat, np.zeros(len(xx_flat))))
            ray_directions = np.tile([0, 0, 1], (len(xx_flat), 1))
            intersector = trimesh.ray.ray_triangle.RayMeshIntersector(scan_mesh)
            locations, index_ray, _ = intersector.intersects_location(
                ray_origins, ray_directions, multiple_hits=False
            )
            
            procedural_backup = zz_top.copy()
            if len(index_ray) > 0:
                unique_rays, first_hit = np.unique(index_ray, return_index=True)
                candidate_z = locations[first_hit, 2]
                valid = candidate_z > 3.0
                zz_top[unique_rays[valid]] = candidate_z[valid]
            
            max_deviation = np.max(np.abs(zz_top - procedural_backup))
            if max_deviation > 1.5:
                params.flags_for_review.append(
                    f"Surface deviation {max_deviation:.2f}mm exceeds \u00b11.5mm clinical tolerance. Verify fit before printing."
                )
            else:
                params.flags_for_review.append(
                    f"Scan fit validated: max deviation {max_deviation:.2f}mm within \u00b11.5mm tolerance."
                )

        zz_bottom = np.zeros_like(xx_flat)
        if params.medial_post_deg > 0:
            slope = np.tan(np.radians(params.medial_post_deg))
            zz_bottom += np.where(xx_flat < 0, -xx_flat * slope, 0)

        top_verts = np.column_stack((xx_flat, yy_flat, zz_top))
        bottom_verts = np.column_stack((xx_flat, yy_flat, zz_bottom))
        vertices = np.vstack((top_verts, bottom_verts))

        faces = []

        def get_idx(ix, iy, is_bottom=False):
            offset = res_x * res_y if is_bottom else 0
            return offset + iy * res_x + ix

        for iy in range(res_y - 1):
            for ix in range(res_x - 1):
                t1 = get_idx(ix, iy)
                t2 = get_idx(ix + 1, iy)
                t3 = get_idx(ix + 1, iy + 1)
                t4 = get_idx(ix, iy + 1)
                faces.extend([[t1, t2, t3], [t1, t3, t4]])

                b1 = get_idx(ix, iy, True)
                b2 = get_idx(ix + 1, iy, True)
                b3 = get_idx(ix + 1, iy + 1, True)
                b4 = get_idx(ix, iy + 1, True)
                faces.extend([[b1, b3, b2], [b1, b4, b3]])

        for ix in range(res_x - 1):
            t1, t2 = get_idx(ix, 0), get_idx(ix + 1, 0)
            b1, b2 = get_idx(ix, 0, True), get_idx(ix + 1, 0, True)
            faces.extend([[t1, b1, b2], [t1, b2, t2]])
            iy = res_y - 1
            t1, t2 = get_idx(ix, iy), get_idx(ix + 1, iy)
            b1, b2 = get_idx(ix, iy, True), get_idx(ix + 1, iy, True)
            faces.extend([[t2, b2, b1], [t2, b1, t1]])

        for iy in range(res_y - 1):
            t1, t2 = get_idx(0, iy), get_idx(0, iy + 1)
            b1, b2 = get_idx(0, iy, True), get_idx(0, iy + 1, True)
            faces.extend([[t2, b2, b1], [t2, b1, t1]])
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
        # Met pad position drives the midfoot/forefoot boundary so the heatmap
        # matches the actual orthotic geometry.
        met_boundary = params.met_pad_position_mm
        plt.fill_between(
            [-self.width / 2, self.width / 2], self.length * 0.25, met_boundary,
            color="orange", alpha=0.5, label="Midfoot",
        )
        plt.fill_between(
            [-self.width / 2, self.width / 2], met_boundary, self.length,
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
