# PTLD input and official-API adapter

This directory is a validation and calling layer around the fixed official
`SpatialEcoTyper` 1.0.2 package. It does not copy or modify any package
algorithm.

## Required objects

- Expression: numeric genes-by-cells matrix (dense or `Matrix` sparse), with
  unique gene and cell names. `validate_ptld_input()` calls this object
  `counts` and never alters its values.
- Metadata: one row per cell, row names equal to expression column names, and
  columns `X`, `Y`, `CellType`, and `SampleID`.
- Cell-type mapping: an explicit two-column table, `source` and `target`.
  Every observed input label must be represented. Unknown labels cause an
  error; they are never guessed. Target labels must not contain a period
  (`.`), because the fixed official algorithm reserves it as an internal
  delimiter.

Use de-identified, filename-safe `SampleID` values. Keep each tissue section or
biological specimen as its own sample unless the protocol defines a documented
replicate rule.

## Sequence

```r
source("reproduction/spatialecotyper/ptld/validate_input.R")
source("reproduction/spatialecotyper/ptld/map_cell_types.R")
source("reproduction/spatialecotyper/ptld/run_official_api.R")

checked <- validate_ptld_input(counts, metadata, min_cells_per_sample = 20L)
checked$metadata <- map_ptld_cell_types(checked$metadata, mapping)

# Normalize explicitly using one method supported by official Tutorial 1.
# Do not pass raw counts to the official discovery function.
normdata <- Seurat::NormalizeData(checked$counts)

results <- run_ptld_by_sample(
  normdata, checked$metadata,
  output_dir = "/mnt/f/spatialecotyper_reproduction/results/ptld_adapter",
  prefix = "PTLD",
  nfeatures = 300L,
  radius = 50,
  ncores = 2L
)
```

The defaults `nfeatures = 300`, `radius = 50`, and `ncores = 2` reproduce the
explicit call in official Tutorial 1. Coordinate units must therefore be
compatible with a 50-unit radius. Any PTLD-specific parameter change must be
recorded outside these wrappers and justified before execution. Copy
`ptld-run-config.example.tsv` for each run and record the fixed source commit,
normalization method, input hashes, sample IDs, coordinate unit, parameters,
and execution date.

`validate_ptld_input()` returns the unmodified expression object, aligned
metadata, per-sample summaries, and per-cell library-size/detected-gene QC. It
does not filter cells, normalize expression, infer cell types, pool specimens,
or change Spatial EcoTyper internals.
