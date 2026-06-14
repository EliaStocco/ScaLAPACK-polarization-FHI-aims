#!/usr/bin/env python3

import argparse
import numpy as np
import matplotlib.pyplot as plt
from math import sqrt


def main():
    parser = argparse.ArgumentParser(
        description="Estimate BLACS grid efficiency for k-point parallel calculations."
    )

    parser.add_argument(
        "-n",
        "--n_basis",
        type=int,
        required=True,
        help="Number of basis functions (e.g. 7360)"
    )

    parser.add_argument(
        "-k",
        "--k_points",
        type=int,
        required=True,
        help="Number of k-points (e.g. 36)"
    )

    parser.add_argument(
        "-c",
        "--max_cores",
        type=int,
        default=4096,
        help="Maximum total number of cores to consider (default: 4096)"
    )
    parser.add_argument(
        "-l",
        "--list_cores",
        type=int,
        nargs="+",
        help="Explicit list of total core counts to evaluate",
        default=None
    )
    parser.add_argument(
        "-e",
        "--efficiency_threshold",
        type=float,
        default=0.95,
        help="Threshold above which points are annotated (default: 0.95)"
    )

    args = parser.parse_args()

    n_basis = args.n_basis
    n_kpoints = args.k_points
    max_cores = args.max_cores
    threshold = args.efficiency_threshold

    # core_list = np.arange(n_kpoints, max_cores + 1, n_kpoints)
    core_list = np.arange(
        n_kpoints,
        max_cores + 1,
        n_kpoints
    )

    if args.list_cores:
        # Keep only values divisible by k-points
        core_list = np.array(
            [c for c in args.list_cores if c % n_kpoints == 0]
        )

        invalid = [c for c in args.list_cores if c % n_kpoints != 0]
        if invalid:
            print(
                f"Warning: skipping core counts not divisible "
                f"by {n_kpoints}: {invalid}"
            )


    efficiencies = []
    best_grids = []

    for total_cores in core_list:

        cores_per_k = total_cores // n_kpoints

        best_eff = 0.0
        best_grid = (1, cores_per_k)

        for nprow in range(1, int(sqrt(cores_per_k)) + 1):

            if cores_per_k % nprow == 0:
                npcol = cores_per_k // nprow

                # BLACS grid efficiency metric
                eff = (
                    4.0 * nprow * npcol
                    / (nprow + npcol) ** 2
                )

                if eff > best_eff:
                    best_eff = eff
                    best_grid = (nprow, npcol)

        efficiencies.append(best_eff)
        best_grids.append(best_grid)

    # Plot
    plt.figure(figsize=(12, 6))
    plt.plot(core_list, efficiencies, marker='o')

    plt.xlabel("Total cores")
    plt.ylabel("BLACS grid efficiency")
    plt.title(
        f"BLACS Grid Efficiency\n"
        f"n_basis={n_basis}, k-points={n_kpoints}"
    )

    plt.grid(True)
    plt.ylim(0, 1.05)

    # Annotate efficient points with total core count
    for cores, eff, grid in zip(core_list, efficiencies, best_grids):

        if eff >= threshold:
            plt.annotate(
                f"{cores}",
                (cores, eff),
                textcoords="offset points",
                xytext=(0, 8),
                ha='center',
                fontsize=8
            )

    plt.tight_layout()
    plt.savefig("efficiency.pdf",bbox_inches="tight")

    # Print recommendations
    print("\nRecommended configurations:")
    print(
        f"{'Total Cores':>12} "
        f"{'Cores/k':>10} "
        f"{'Grid':>10} "
        f"{'Efficiency':>12}"
    )

    for cores, eff, grid in zip(core_list, efficiencies, best_grids):

        if eff >= threshold:
            print(
                f"{cores:12d} "
                f"{cores // n_kpoints:10d} "
                f"{grid[0]}x{grid[1]:<7} "
                f"{eff:12.3f}"
            )


if __name__ == "__main__":
    main()
