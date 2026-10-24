# Reproducible research plan

## Scope and research question

**Question.** In deterministic mixed-size 3D rigid-body scenes, does an adaptive two-tier spatial hash whose tier scales are derived from the median and 90th-percentile object diameters produce fewer broad-phase candidate pairs than the best single fixed cell size, and in which distribution regimes does that result change?

The comparison is limited to broad-phase *candidate-pair count*. It must not claim lower wall-clock time, lower memory, better cache behavior, or better narrow-phase accuracy unless those quantities are separately measured. “Reduces” means a lower count under the same scene, insertion/query conventions, and pair de-duplication rule.

## Phase order and ownership

1. **Planner (this file):** freeze terminology, factors, metrics, controls, reproducibility rules, and acceptance criteria.
2. **Literature mapper:** populate `sources.jsonl` and `references.bib` with primary collision-detection/spatial-hashing sources and stable citation IDs. Record bibliographic uncertainty rather than inventing metadata.
3. **Hypothesis generator:** populate `hypotheses.jsonl`; every hypothesis must identify its measurable outcome, expected direction, regime, and falsifier.
4. **Experimenter:** create `experiments/`, `lab-notebook.md`, and executable `reproduce.sh`; run bounded experiments and retain raw outputs, commands, seeds, environment details, and hashes. Failures must be logged visibly.
5. **Skeptical critic:** populate/update `evidence.jsonl` with claim-level support, confounds, unsupported extrapolations, and negative results.
6. **Novelty auditor:** check every surviving discovery against the mapped prior art; downgrade or remove claims that are already established or not supported by the experiment.
7. **Replicator:** rerun only strong experiments from clean commands/environment and record direct comparison with the original outputs.
8. **Paper writer:** write `paper.md` with the required sections and citation IDs on every factual claim.
9. **Final verifier:** write `verification.json` covering artifact presence, schema checks, reproducibility, hashes, citation coverage, and replication status.

Later phases must preserve existing files and append or make surgical updates; no phase may silently replace a prior result.

## Terminology and algorithm contract

- Object: an axis-aligned bounding box (AABB) used as a deterministic rigid-body proxy.
- Diameter: `max(width, height, depth)` of an object AABB.
- Candidate pair: an unordered pair of distinct object IDs emitted by the broad phase before narrow-phase overlap testing, after global de-duplication.
- Scene: a fixed set of object AABBs plus a fixed insertion/query order.
- Single-tier baseline: one uniform spatial hash with cell edge length `s`.
- Two-tier method: two uniform hashes with cell edge lengths derived from the scene diameter statistics: `s_small = median diameter` and `s_large = 90th-percentile diameter`, with a precisely documented assignment/query rule. The implementation must state whether objects are inserted into one tier, both tiers, or selected by size, and must use the same pair de-duplication and boundary convention in all methods.
- Fixed-size oracle: the baseline evaluated over a declared geometric grid of `s` values, including the two derived scales where valid, so “best single fixed cell size” is not chosen from the adaptive result.

The methods must use the same AABB overlap convention, periodic/non-periodic domain convention, out-of-domain handling, cell-coordinate rounding, duplicate suppression, and object IDs. The 90th percentile definition (interpolation/method and behavior for small `N`) is part of the recorded protocol.

## Deterministic experimental design

### Controlled factors

Use a bounded factorial or documented fractional-factorial design over:

- **Object count:** at least three fixed sizes spanning small, medium, and upper-bound scenes (for example 1,000; 5,000; 20,000), subject to local runtime limits.
- **Size distributions:** mono-size control; lognormal with low, medium, and high dispersion; bimodal mixtures with separated modes; and a heavy-tail/Pareto-like case. Parameters, truncation, and exact sampling method must be recorded.
- **Spatial distributions:** uniform random positions; clustered positions; and a deterministic adversarial/structured arrangement. Keep object centers inside a declared bounded 3D domain.
- **Overlap/density controls:** choose parameters that expose both sparse and crowded scenes; report realized occupancy and true AABB-overlap count separately from candidate count.
- **Aspect ratios:** include a near-cubic control and at least one anisotropic-size condition while retaining the diameter definition above.
- **Randomness:** use a small declared seed set (minimum three seeds for stochastic conditions) plus at least one fully deterministic seed/fixture. Seed values must be visible in raw output.

The same generated scene files must be fed to every algorithm variant. Do not regenerate a scene per method. If a condition cannot run within the local bound, record the exact failure and do not substitute an unreported condition.

### Baselines and sensitivity

For each scene, evaluate:

1. the single-tier baseline across a predeclared logarithmic/geometric grid of cell sizes covering below the smallest relevant diameter through above the largest relevant diameter;
2. the best baseline cell size selected only after all baseline runs;
3. the two-tier median/90th-percentile method;
4. a sensitivity variant that changes only the tier assignment/query policy, if needed to distinguish the statistic choice from implementation policy.

The primary comparison is two-tier candidate pairs versus the minimum candidate pairs among the fixed-grid single-tier runs. Report the fixed grid and any tie-breaking rule. Do not compare against a post hoc single size outside the declared grid without labeling it exploratory.

## Measurements and analysis

For every `(condition, seed, method, cell-size/policy)` record:

- candidate-pair count;
- number of unique pairs after de-duplication;
- true AABB-overlap pair count;
- false-positive candidate count and candidate/true ratio (undefined ratios must be represented explicitly);
- object count, domain dimensions, realized size quantiles, and occupancy statistics;
- insertion/query counters if implementation naturally exposes them (secondary only);
- status (`ok` or `failed`), error type/message, command, seed, environment, and output hash.

Primary summaries are paired differences and ratios on identical scenes. For each condition report median and range across seeds, and retain per-seed rows. Identify crossover regimes using a predeclared rule (for example, the smallest size-dispersion or crowding level at which the replicated paired difference changes sign), not visual cherry-picking. Include uncertainty or variability summaries appropriate to the finite seed set; do not imply population-level statistical certainty from a small deterministic benchmark.

## Confounds and falsification checks

The critic must explicitly test or discuss: unequal pair de-duplication, boundary-cell rounding, objects spanning many cells, tier assignment that changes the algorithm rather than only its scale, percentile definition for small samples, fixed-grid selection bias, regenerated scenes, clustered-vs-uniform density, anisotropy, domain-size effects, memory/time tradeoffs, candidate-count overflow or integer limits, and accidental dependence on object ID/order. Include permutation/order checks where feasible. Any result that fails a control or cannot be rerun is not a surviving finding.

## Reproducibility and artifact contracts

`reproduce.sh` must run from the workspace with no network access, use only available/local dependencies, fail on command errors, print each command, and write outputs into a run-specific directory without deleting prior runs. It must expose exact seeds and parameters. Raw outputs must be machine-readable (prefer JSONL/CSV), while `lab-notebook.md` explains each run and visible failures. The experimenter must hash source/configuration and raw outputs (for example SHA-256) and record the commands and environment in the notebook.

Required line-oriented schemas:

- `sources.jsonl`: one source per line with stable `citation_id`, full bibliographic fields, source type, URL/DOI, and relevance note.
- `hypotheses.jsonl`: one hypothesis per line with stable ID, statement, measurable prediction, regime, falsifier, and status.
- `evidence.jsonl`: one claim/evidence record per line with claim ID, claim text, evidence artifact/run IDs, support status, confounds, replication status, and citation IDs where applicable.
- `verification.json`: structured pass/fail checks with paths, commands, hashes, and reasons for every failed or skipped check.

## Acceptance criteria for a surviving finding

A finding may appear as a result or candidate novel finding only if it is (a) supported by paired raw rows from identical scenes, (b) based on the declared metric and algorithm contract, (c) reproduced from clean commands by the replicator, (d) audited against primary sources, and (e) accompanied by its regime, effect summary, and limitations. A non-reduction, null result, failed run, or unresolved confound must be reported as such rather than omitted.

The paper must distinguish factual sourced claims, empirical findings, inferences, limitations, candidate novelty, and negative results with explicit labels. Every factual claim in `paper.md` must carry a `citation_id` that exists in `sources.jsonl`; experiment-only claims must point to evidence/run IDs.

## Bounded execution policy

Before running the full matrix, execute one smoke condition and one representative mixed-size condition to estimate runtime and output size. Set an explicit wall-clock/row-count budget in the notebook, cap the matrix if necessary, and preserve the cap decision. Prefer complete replicated smaller conditions over an unreplicated oversized sweep. No network retrieval or external service is allowed during experiments.
