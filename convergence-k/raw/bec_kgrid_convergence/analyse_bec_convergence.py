#!/usr/bin/env python3
"""Plot Born-effective-charge convergence across polarization k-grids.

``post_process_aims`` writes ``postprocess/bec.txt`` for each k-grid.  The
largest available k-grid is the reference unless ``--reference`` is supplied.
The table reports both the largest absolute component of
``Z*(n) - Z*(n_max)`` and the mean and standard deviation of the absolute
diagonal and off-diagonal tensor-component differences over all atoms.
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


GRID_PATTERN = re.compile(r"k-grid-(\d+)$")


def load_tensors(root: Path) -> dict[int, np.ndarray]:
    """Load fd2bec's one-row-per-atom, nine-component BEC tensors."""
    tensors: dict[int, np.ndarray] = {}
    for folder in root.glob("k-grid-*"):
        match = GRID_PATTERN.fullmatch(folder.name)
        bec_file = folder / "postprocess" / "bec.txt"
        if match is None or not bec_file.is_file():
            continue
        data = np.loadtxt(bec_file, ndmin=2)
        if data.ndim != 2 or data.shape[1] != 9:
            raise ValueError(
                f"{bec_file} must contain nine tensor components per atom; got {data.shape}."
            )
        tensors[int(match.group(1))] = data.reshape((-1, 3, 3))
    return dict(sorted(tensors.items()))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parent,
        help="directory containing k-grid-<n> folders (default: script directory)",
    )
    parser.add_argument(
        "--reference", type=int,
        help="reference string length (default: largest available k-grid)",
    )
    parser.add_argument(
        "--output", type=Path, default=Path("bec-convergence"),
        help="directory for the CSV and figure, relative to --root unless absolute",
    )
    parser.add_argument("--show", action="store_true", help="display the figure after saving it")
    args = parser.parse_args()

    root = args.root.resolve()
    output = args.output if args.output.is_absolute() else root / args.output
    tensors = load_tensors(root)
    if len(tensors) < 2:
        raise SystemExit(
            "Need postprocess/bec.txt files for at least two k-grids. "
            "Run raw/post_process_bec.sh in an activated fd2bec environment first."
        )

    reference_grid = args.reference if args.reference is not None else max(tensors)
    if reference_grid not in tensors:
        raise SystemExit(f"k-grid-{reference_grid} has no postprocess/bec.txt output.")
    reference = tensors[reference_grid]

    rows: list[dict[str, float | int]] = []
    for grid, tensor in tensors.items():
        if tensor.shape != reference.shape:
            raise SystemExit(
                f"k-grid-{grid} has tensor shape {tensor.shape}; reference has {reference.shape}."
            )
        difference = tensor - reference
        atom_norms = np.linalg.norm(difference, axis=(1, 2))
        absolute_difference = np.abs(difference)

        diagonal_mask = np.eye(3, dtype=bool)
        on_diagonal = absolute_difference[:, diagonal_mask]
        off_diagonal = absolute_difference[:, ~diagonal_mask]

        rows.append(
            {
                "k_grid": grid,
                "max_abs_component_difference_e": float(np.max(np.abs(difference))),
                "max_atom_frobenius_difference_e": float(np.max(atom_norms)),
                "mean_atom_frobenius_difference_e": float(np.mean(atom_norms)),
                "mean_abs_on_diagonal_difference_e": float(np.mean(on_diagonal)),
                "std_abs_on_diagonal_difference_e": float(np.std(on_diagonal)),
                "mean_abs_off_diagonal_difference_e": float(np.mean(off_diagonal)),
                "std_abs_off_diagonal_difference_e": float(np.std(off_diagonal)),
            }
        )

    output.mkdir(parents=True, exist_ok=True)
    table = output / "bec_convergence.csv"
    with table.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    grids = [int(row["k_grid"]) for row in rows]
    errors = [float(row["max_abs_component_difference_e"]) for row in rows]
    figure, axis = plt.subplots(figsize=(6.4, 4.2), constrained_layout=True)
    axis.plot(grids, errors, "o-", color="tab:red", linewidth=1.6, markersize=5)
    axis.set(
        xlabel="Polarization k-grid length, n",
        ylabel=r"max $|Z^*(n) - Z^*(n_{\mathrm{max}})|$ ($e$)",
        title=rf"Born-charge convergence (reference: $n = {reference_grid}$)",
    )
    axis.set_xticks(grids)
    axis.grid(True, alpha=0.3)
    plot = output / "bec_convergence.png"
    figure.savefig(plot, dpi=300)
    print(f"Reference: k-grid-{reference_grid}")
    print(f"Wrote table: {table}")
    print(f"Saved plot: {plot}")
    if args.show:
        plt.show()


if __name__ == "__main__":
    main()
