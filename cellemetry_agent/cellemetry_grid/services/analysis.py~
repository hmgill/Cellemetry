"""
Statistical analysis functions for segmentation masks.
Unchanged from original implementation.
"""
import os
import xlsxwriter
import numpy as np
from scipy.spatial import KDTree
from skimage.measure import regionprops
from typing import Optional, Dict, Any


def load_masks(filename: str) -> Optional[np.ndarray]:
    """Load .npz mask stack from disk."""
    try:
        data = np.load(filename)
        return data['masks'] if 'masks' in data else data[data.files[0]]
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return None


def get_basic_stats(filename: str, pixel_scale: Optional[float] = None) -> Dict[str, Any]:
    """Calculate Count, Mean Area, and Std Dev Area."""
    masks = load_masks(filename)
    if masks is None or masks.size == 0:
        return {"count": 0, "area_mean": 0.0, "area_std": 0.0, "unit": "px²"}

    areas_px = np.sum(masks, axis=(1, 2))

    if pixel_scale:
        conversion_factor = pixel_scale ** 2
        areas = areas_px * conversion_factor
        unit = "µm²"
    else:
        areas = areas_px
        unit = "px²"

    return {
        "count": int(len(areas)),
        "area_mean": float(np.mean(areas)),
        "area_std": float(np.std(areas)),
        "unit": unit
    }


def get_spatial_stats(filename: str, pixel_scale: Optional[float] = None) -> Dict[str, Any]:
    """Calculate spatial metrics including NND and density."""
    masks = load_masks(filename)
    defaults = {
        "avg_nnd": 0.0, "std_nnd": 0.0,
        "density": 0.0,
        "avg_neighbor_count": 0.0, "std_neighbor_count": 0.0,
        "dist_unit": "px", "density_unit": "N/A"
    }

    if masks is None or masks.size == 0:
        return defaults

    # Get centroids
    centroids_px = []
    for m in masks:
        props = regionprops(m.astype(int))
        if props:
            centroids_px.append(props[0].centroid)

    centroids_px = np.array(centroids_px)
    n_objects = len(centroids_px)
    image_pixel_area = masks[0].size

    # Unit conversion
    if pixel_scale:
        dist_factor = pixel_scale
        dist_unit = "µm"
        image_phys_area = (image_pixel_area * (pixel_scale ** 2)) / (1000 ** 2)
        density_unit = "cells/mm²"
    else:
        dist_factor = 1.0
        dist_unit = "px"
        image_phys_area = image_pixel_area / 10000.0
        density_unit = "cells/10k px²"

    if n_objects < 2:
        res = defaults.copy()
        res.update({
            "density": float(n_objects / image_phys_area) if image_phys_area > 0 else 0,
            "dist_unit": dist_unit,
            "density_unit": density_unit
        })
        return res

    # KDTree calculations
    tree = KDTree(centroids_px)

    # Nearest neighbor distance
    dists_px, _ = tree.query(centroids_px, k=2)
    valid_dists_px = dists_px[:, 1]

    # Local crowding
    neighbors = tree.query_ball_point(centroids_px, r=100)
    neighbor_counts = [len(n) - 1 for n in neighbors]

    return {
        "avg_nnd": float(np.mean(valid_dists_px) * dist_factor),
        "std_nnd": float(np.std(valid_dists_px) * dist_factor),
        "density": float(n_objects / image_phys_area),
        "avg_neighbor_count": float(np.mean(neighbor_counts)),
        "std_neighbor_count": float(np.std(neighbor_counts)),
        "dist_unit": dist_unit,
        "density_unit": density_unit
    }


def analyze_relationships(cell_file: str, nuc_file: str) -> Dict[str, Any]:
    """Calculate Cell/Nucleus overlap ratios."""
    cells = load_masks(cell_file)
    nuclei = load_masks(nuc_file)

    if cells is None or nuclei is None or cells.size == 0 or nuclei.size == 0:
        return {"matched_pairs": 0, "avg_ratio": 0.0, "std_ratio": 0.0}

    H, W = cells[0].shape
    cell_map = np.zeros((H, W), dtype=int)
    for idx, mask in enumerate(cells):
        cell_map[mask > 0] = idx + 1

    ratios = []
    for nuc_mask in nuclei:
        props = regionprops(nuc_mask.astype(int))
        if not props:
            continue
        cy, cx = map(int, props[0].centroid)
        if 0 <= cy < H and 0 <= cx < W:
            cell_id = cell_map[cy, cx]
            if cell_id > 0:
                cell_area = np.sum(cells[cell_id - 1])
                nuc_area = np.sum(nuc_mask)
                if nuc_area > 0:
                    ratios.append(cell_area / nuc_area)

    if not ratios:
        return {"matched_pairs": 0, "avg_ratio": 0.0, "std_ratio": 0.0}

    return {
        "matched_pairs": len(ratios),
        "avg_ratio": float(np.mean(ratios)),
        "std_ratio": float(np.std(ratios))
    }


def save_stats_to_excel(
    base_filename: str,
    cell_stats: Optional[Dict] = None,
    nuc_stats: Optional[Dict] = None,
    spatial_stats: Optional[Dict] = None,
    rel_stats: Optional[Dict] = None
) -> str:
    """Write statistics to a multi-sheet Excel file."""
    filename = os.path.splitext(base_filename)[0] + ".xlsx"

    try:
        workbook = xlsxwriter.Workbook(filename)
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1})
        num_fmt = workbook.add_format({'num_format': '0.00'})

        # Morphology sheet
        ws_morph = workbook.add_worksheet("Morphology")
        headers = ["Structure", "Count", "Mean Area", "StdDev Area", "Unit"]
        ws_morph.write_row(0, 0, headers, header_fmt)

        row = 1
        if cell_stats and cell_stats.get("count", 0) > 0:
            ws_morph.write(row, 0, "Cells")
            ws_morph.write(row, 1, cell_stats.get('count', 0))
            ws_morph.write(row, 2, cell_stats.get('area_mean', 0), num_fmt)
            ws_morph.write(row, 3, cell_stats.get('area_std', 0), num_fmt)
            ws_morph.write(row, 4, cell_stats.get('unit', 'px²'))
            row += 1

        if nuc_stats and nuc_stats.get("count", 0) > 0:
            ws_morph.write(row, 0, "Nuclei")
            ws_morph.write(row, 1, nuc_stats.get('count', 0))
            ws_morph.write(row, 2, nuc_stats.get('area_mean', 0), num_fmt)
            ws_morph.write(row, 3, nuc_stats.get('area_std', 0), num_fmt)
            ws_morph.write(row, 4, nuc_stats.get('unit', 'px²'))

        ws_morph.set_column(0, 4, 15)

        # Spatial sheet
        if spatial_stats and spatial_stats.get("density", 0) > 0:
            ws_spat = workbook.add_worksheet("Spatial")
            headers = [
                "Structure", "Global Density", "Density Unit",
                "Mean NND", "StdDev NND", "Dist Unit",
                "Mean Neighbors (r=100)", "StdDev Neighbors"
            ]
            ws_spat.write_row(0, 0, headers, header_fmt)

            ws_spat.write(1, 0, "Cells")
            ws_spat.write(1, 1, spatial_stats.get('density', 0), num_fmt)
            ws_spat.write(1, 2, spatial_stats.get('density_unit', 'N/A'))
            ws_spat.write(1, 3, spatial_stats.get('avg_nnd', 0), num_fmt)
            ws_spat.write(1, 4, spatial_stats.get('std_nnd', 0), num_fmt)
            ws_spat.write(1, 5, spatial_stats.get('dist_unit', 'px'))
            ws_spat.write(1, 6, spatial_stats.get('avg_neighbor_count', 0), num_fmt)
            ws_spat.write(1, 7, spatial_stats.get('std_neighbor_count', 0), num_fmt)

            ws_spat.set_column(0, 7, 18)

        # Relational sheet
        if rel_stats and rel_stats.get("matched_pairs", 0) > 0:
            ws_rel = workbook.add_worksheet("Relational")
            headers = ["Relationship", "Matched Pairs", "Mean Area Ratio", "StdDev Ratio"]
            ws_rel.write_row(0, 0, headers, header_fmt)

            ws_rel.write(1, 0, "Cell_to_Nucleus")
            ws_rel.write(1, 1, rel_stats.get('matched_pairs', 0))
            ws_rel.write(1, 2, rel_stats.get('avg_ratio', 0), num_fmt)
            ws_rel.write(1, 3, rel_stats.get('std_ratio', 0), num_fmt)

            ws_rel.set_column(0, 3, 20)

        workbook.close()
        return filename

    except Exception as e:
        print(f"Error creating Excel file: {e}")
        return f"Error: {e}"
