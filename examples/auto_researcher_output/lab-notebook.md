# Experimenter lab notebook

## Scope and bounded budget

This phase compares the declared single-tier geometric grid with a two-tier policy on deterministic AABB scenes. The execution cap was 24 condition/seed scenes, 320 objects per scene, 10 fixed cell sizes, three seeds, and one permutation fixture (265 JSONL result rows). The implementation uses Python's standard library only; no network access or external services were used. The smoke fixture used 32 objects, and the representative fixture used 320 clustered bimodal objects.

The smoke command and observed output were:

```text
python3 - <<'PY'
import sys
sys.path.insert(0,'experiments')
from run_experiment import make_scene, row
for label, condition, spatial, seed, n in [('smoke','mono','uniform',11,32),('representative','bimodal','clustered',23,320)]:
    objects=make_scene(condition,spatial,seed)[:n]
    a=row(condition,spatial,seed,objects,'single',2.0)
    b=row(condition,spatial,seed,objects,'two_tier')
    print(label, {'seed':seed,'n':n,'single_cell_2':a['unique_pairs'],'two_tier':b['unique_pairs'],'difference':b['unique_pairs']-a['unique_pairs']})
PY
smoke {'seed': 11, 'n': 32, 'single_cell_2': 0, 'two_tier': 0, 'difference': 0}
representative {'seed': 23, 'n': 320, 'single_cell_2': 555, 'two_tier': 1575, 'difference': 1020}
```

## Protocol

`experiments/run_experiment.py` generates each scene once and feeds the same object tuples to every method. Centers use a 100 x 100 x 100 non-periodic domain. Diameters are mono-size 2.0, low-dispersion lognormal (clipped to [1,5]), separated bimodal (1.5/9.0), or truncated Pareto-like (scale 1.2, shape 1.6, maximum 14). Spatial layouts are uniform or Gaussian-clustered centers clipped to the domain. Seeds are 11, 23, and 37; object count is 320.

The fixed single-tier grid is `[0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0, 16.0]`. The two-tier cells are linearly interpolated median and 90th percentile diameters. Objects at or below the median use the small tier; larger objects use the large tier. Same-tier pairs are generated in their selected tier, and cross-tier pairs query large objects against the small-object hash. AABB cell maxima are inclusive and coordinates use `floor`; unordered pairs are globally deduplicated. Candidate counts are not wall-clock or memory measurements.

## Exact execution and artifacts

The reproducible command was:

```text
chmod +x reproduce.sh experiments/run_experiment.py
RUN_ID=initial-20260815 ./reproduce.sh
```

It produced `experiments/runs/initial-20260815/results.jsonl`, `metadata.json`, `failures.jsonl`, and `SHA256SUMS`. The implementation SHA-256 was `abc132bfa89e455edfa5eea704f78b9a41111793b6af71e62dab33f1a81286f5`; result, metadata, failure, and checksum-file hashes were respectively `8892d8547753171ca4e0b2f55ff1197b3d8f7af798c67c73be64cc1b93e52b5a`, `556c06a1ff7f32f1209e17dec2a16fa57443501f615b683b8c9b7e2ecd4626d8`, `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`, and `03c191a31dd4f680d909a0a90b2a055e26ef1e0ffb5888ccad6268246b5179e0`. `metadata.json` records the Python version, platform, command, seeds, grid, percentile, boundary, assignment policy, and row count.

## Results from this phase

All 24 condition/seed scenes completed (`265` result rows); `failures.jsonl` is empty. For each scene, the two-tier candidate set contained every exact overlapping AABB found by the all-pairs check. The paired difference is `two_tier_unique - minimum_single_grid_unique`; positive values favor the fixed-grid oracle.

| distribution | layout | median difference | seed range |
|---|---|---:|---:|
| mono | uniform | 6 | 4..7 |
| mono | clustered | 50 | 43..65 |
| loglow | uniform | 10 | 7..11 |
| loglow | clustered | 104 | 99..112 |
| bimodal | uniform | 161 | 125..182 |
| bimodal | clustered | 1380 | 1151..1413 |
| pareto | uniform | 47 | 38..63 |
| pareto | clustered | 513 | 290..513 |

**Experimenter finding (not yet a surviving replicated finding):** within this bounded protocol, the two-tier policy did not beat the declared fixed-grid oracle in any condition or seed. Thus H1, H2's expected low-dispersion crossover, and H3's expected bimodal advantage are not supported by these raw rows; H4's anticipated heavy-tail mismatch is directionally consistent. This is a candidate negative result only until the replicator reruns the clean command.

The permutation fixture (clustered bimodal, seed 11, permutation seed 991) returned the same two-tier count of 1861 as its unpermuted scene count. The scene hash changes because IDs are permuted; pair-count invariance, not scene-hash equality, is the relevant check.

## Visible failures and confounds

No runtime failures occurred. This experiment does not measure time, memory, cache behavior, or a second independent implementation. The two-tier assignment/query rule is one specific policy, not a universal hierarchical hash. The fixed-grid oracle is intentionally allowed to choose its best cell size after evaluation, and the grid may favor sparse scenes. All objects are cubes, so anisotropy was not tested in this phase. The small sample of three deterministic seeds does not support population-level statistical claims. The clustered centers can yield many multi-cell objects, and those insertion/query visits are reported only as secondary counters.

## Replication run

The clean replication command was:

```text
RUN_ID=replicator-20260815 ./reproduce.sh
```

It wrote `experiments/runs/replicator-20260815/` without modifying the initial run. The replication used the same implementation SHA-256 (`abc132bfa89e455edfa5eea704f78b9a41111793b6af71e62dab33f1a81286f5`), produced 265 result rows, and had zero failure rows. Run-specific metadata, elapsed timings, and result-file hashes differ as expected; all count-bearing result fields, scene/method ordering, scene-level paired differences, and true-overlap counts matched exactly. The direct machine-readable comparison is `experiments/replication-comparison.json`.

The 24-scene conclusion replicated exactly: two-tier minus best-fixed-grid differences remained positive in every scene, with range `+4..+1413`; no tested scene showed a reduction or tie. Candidate coverage also held for every row in both runs, and the permutation fixture retained a two-tier count of 1861. This is a replicated bounded negative result, not evidence that no crossover exists outside this policy and protocol.