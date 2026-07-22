# BiFeO3 AFM Berry-Phase Workflow

This folder prepares the same style of workflow that was used for `CrI3`, but adapted to the two BiFeO3 AFM geometries in this project:

- `BiFeO3_R-3c_AFM`
- `BiFeO3_R3c_AFM`

For each structure, the workflow is organized exactly as requested:

- `LDA`
- `PBEsol`
- `HSE06`

and for each functional the calculation is split into four stages:

- `relax`
- `converge`
- `lapack`
- `scalapack`

The idea is:

1. Relax each structure for each functional.
2. Converge the density in the `converge` folder.
3. Save the density matrices.
4. Compute the polarization with the same density matrices using both the LAPACK and ScaLAPACK implementations.

## What I changed

### 1. BiFeO3-specific input tree

I created the BiFeO3 workflow tree under `BiFeO3/` and mirrored the structure of the existing `CrI3` setup so the workflow is easy to compare and reuse.

### 2. K-point and polarization settings

All BiFeO3 stage inputs now use:

- `k_grid 8 8 8`
- `output polarization 1 80 8 8`
- `output polarization 2 8 80 8`
- `output polarization 3 8 8 80`

This is now consistent across the convergence and polarization stages.

### 3. ScaLAPACK requirement

In every ScaLAPACK control file, the Kohn-Sham solver is explicitly set to:

- `KS_method parallel`

This was important because you specifically asked that the ScaLAPACK folders use the parallel solver.

### 4. Relaxation job settings

For the `LDA` and `PBEsol` relaxations I set:

- one node
- `#SBATCH --time=01:00:00`

I also removed:

- `--cell-constraints az bz cz`

from the BiFeO3 relax folders, as requested.

### 5. Relaxation launcher

I added `run-all-relaxations.sh` at the top of `BiFeO3/` to submit all six relaxation jobs:

- 2 structures
- 3 functionals

It simply walks the workflow tree and calls each relaxation `main.sh`.

## The FHI-aims error and the fix

You hit an FHI-aims initialization error while building the free-atom density:

- the code wanted to occupy a `4p` shell for Fe
- but the Fe species definition did not allow that shell in its `valence` block

This is not really a density-matrix restart problem. It happens earlier, while FHI-aims is constructing the self-consistent free-atom reference used for the initial charge density.

The practical fix is to add the missing Fe `4p` shell to the species definition.

I updated the Fe block in:

- `BiFeO3/species.tight.in`
- every generated BiFeO3 `control.in`
- every generated BiFeO3 `aims.in`

The Fe valence block now reads, in essence:

```text
valence      4  s   1.99999
valence      4  p   0.00001
valence      3  p   6.
valence      3  d   6.
```

That preserves the total electron count while making the `4p` shell available to the atomic initialization.

## Why I did not try to "fix the density guess" directly

I checked the FHI-aims source and the manual. The important points are:

- the free-atom occupations are determined from the species `valence` block
- the initial charge density is built from that free-atom reference
- `force_occupation_basis` is not implemented for periodic systems
- `force_occupation_projector` currently only works with LAPACK and also requires restart files

So for this periodic BiFeO3 workflow, changing the species definition is the robust solution.

## Files in this folder

- `BiFeO3_R-3c_AFM/`
- `BiFeO3_R3c_AFM/`
- `run-all.sh`
- `run-all-relaxations.sh`
- `species.tight.in`

Each structure folder contains the three functionals and the four workflow stages listed above.

## How to run

### Run all relaxations

From inside `BiFeO3/`:

```bash
./run-all-relaxations.sh
```

That submits all relaxation jobs for both structures and all functionals.

### Then continue stage by stage

Once a relaxation is finished, proceed with the corresponding:

1. `converge`
2. `lapack`
3. `scalapack`

folders.

The polarization comparison should use the same converged density matrices for both the LAPACK and ScaLAPACK implementations, so the comparison remains meaningful.

## Notes

- The workflow is designed to compare the AFM BiFeO3 structures, not to re-derive the species basis set from scratch.
- The Fe initialization fix is deliberately minimal and only adds the missing `4p` channel needed by FHI-aims.
- If you later decide to experiment with a different Fe atomic reference, the change should be made consistently in the species definition and then propagated through the generated stage inputs.
