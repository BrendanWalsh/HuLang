# Median/90th-Percentile Two-Tier Spatial Hashing Does Not Reduce Candidate Pairs in a Bounded Mixed-Size 3D Benchmark

## Abstract

**[FACT]** Spatial hashing, adaptive spatial subdivision, and hierarchical hashing are established collision-detection strategies [teschner2003optimized_hash; bandi1995adaptive; eitz2007hierarchical_hash]. **[RESEARCH QUESTION]** Does a two-tier hash whose cell sizes are the realized median and 90th-percentile object diameters emit fewer globally deduplicated broad-phase candidate pairs than the best cell size in a declared single-tier grid for identical mixed-size 3D rigid-body proxy scenes? **[NEGATIVE RESULT]** In the bounded experiment and its clean replication, the two-tier policy emitted more unique candidate pairs than the fixed-grid oracle in all 24 scenes: paired differences ranged from +4 to +1413, with no tie or reduction (E1_bounded_no_reduction; `experiments/replication-comparison.json`). **[LIMITATION]** This is a result about one assignment/query policy, 320 cube AABBs, a 100^3 domain, two layouts, four distributions, and three seeds; it does not establish that adaptive or hierarchical hashing is generally ineffective or that no crossover exists.

## Research question

**[RESEARCH QUESTION]** In deterministic mixed-size 3D rigid-body scenes, does the specified median/90th-percentile two-tier spatial hash reduce broad-phase candidate-pair count relative to the best single fixed cell size, and are there replicated distribution or layout regimes in which its advantage changes sign?

**[EMPIRICAL FACT]** The primary outcome is the number of unique unordered candidate pairs emitted before narrow-phase testing. “Reduction” means a lower count on the same generated scene under the same overlap, boundary, and de-duplication conventions. Candidate count is not treated as a proxy for elapsed time, memory, cache behavior, or narrow-phase accuracy.

## Related work

**[FACT]** Teschner et al. study optimized spatial hashing with a hash-compressed regular grid and examine hash and cell-size choices for collision and self-collision detection [teschner2003optimized_hash]. **[FACT]** Bandi and Thalmann describe adaptive spatial subdivision for animated rigid bodies [bandi1995adaptive]. **[FACT]** Eitz and Gu present hierarchical spatial hashing that adapts grid resolution to object scale [eitz2007hierarchical_hash]. **[FACT]** Wong et al. address the mismatch between object size and uniform-grid resolution through virtual subdivision for deformable-object processing [wong2012virtual_subdivision]. **[FACT]** Sweep-and-prune and bounding-volume hierarchies provide distinct broad-phase families and reinforce that candidate generation is separate from exact interference testing [cohen1995icollide; gottschalk1996obbtree].

**[INFERENCE]** These sources establish the broader adaptive, hierarchical, and size/resolution design space, but they do not test the exact median/90th-percentile insertion and cross-tier query policy against this declared fixed-grid oracle. Therefore the present comparison is an exact-policy empirical test, not a claim of novelty for adaptive or hierarchical hashing.

## Methods

### Scene generation and conditions

**[EMPIRICAL FACT]** An object was represented by an axis-aligned bounding box (AABB), with diameter defined as the maximum of its three side lengths. Each scene contained 320 objects in a non-periodic 100 x 100 x 100 domain. The four diameter conditions were mono-size (2.0), clipped low-dispersion lognormal sizes in [1, 5], a separated bimodal mixture with modes 1.5 and 9.0, and a truncated Pareto-like distribution with scale 1.2, shape 1.6, and maximum 14. Centers were either uniform or Gaussian-clustered and clipped to the domain. Seeds were 11, 23, and 37 (lab-notebook.md; E9_missing_factorial_coverage).

### Compared policies

**[EMPIRICAL FACT]** The single-tier baseline was evaluated at cell edges 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0, and 16.0; the oracle is the minimum unique-pair count over this predeclared grid. The two-tier cell edges were the realized median and 90th-percentile diameters, using linear interpolation. Objects at or below the median were inserted into the small hash and larger objects into the large hash. Same-tier pairs were queried within their tier; cross-tier pairs queried large objects against the small-object hash. AABB cell maxima were inclusive and cell coordinates used `floor`. Candidate pairs were globally deduplicated as unordered object-ID pairs (E5_dedup_and_boundary_control; E6_policy_is_not_statistics_only).

**[EMPIRICAL FACT]** Both methods used the same generated object tuples, AABB convention, boundary convention, and global pair de-duplication. An all-pairs check supplied the finite-scene true-overlap count. The experiment records candidate coverage, cell visits, and timings, but candidate count is the primary endpoint and the notebook does not treat the timing counters as a controlled systems benchmark (E4_exact_overlap_coverage; E8_unmeasured_costs).

### Reproducibility and analysis

**[EMPIRICAL FACT]** The initial run was executed with `RUN_ID=initial-20260815 ./reproduce.sh`; the clean replication used `RUN_ID=replicator-20260815 ./reproduce.sh`. Each produced 265 result rows, zero failure rows, and preserved separate run directories. The implementation SHA-256 was `abc132bfa89e455edfa5eea704f78b9a41111793b6af71e62dab33f1a81286f5`; the direct replication comparison reports semantic equality of count-bearing rows and a maximum unique-pair-count delta of zero (`experiments/replication-comparison.json`; lab-notebook.md).

**[METHOD CHECK]** For each scene, the paired difference was:

`two_tier_unique_candidates - minimum_single_tier_unique_candidates`.

**[INFERENCE]** A negative paired difference would favor the two-tier method; a positive value favors the fixed-grid oracle. The planned crossover and bimodal-advantage hypotheses were evaluated only within the recorded condition sequence and seed set, not as population-level statistical tests.

## Experiments

**[EMPIRICAL FACT]** The bounded matrix comprised 4 distributions x 2 layouts x 3 seeds = 24 scenes. All 24 completed in both runs; no runtime failures were recorded. A separate clustered-bimodal permutation fixture tested order sensitivity for the two-tier method (lab-notebook.md; E7_permutation_scope).

## Results

### Candidate-pair counts

**[NEGATIVE RESULT]** The two-tier count exceeded the best fixed-grid count in every replicated scene. The paired-difference range was +4 to +1413, with median differences as follows (E1_bounded_no_reduction; E2_distribution_layout_pattern):

| Distribution | Layout | Median paired difference | Seed range |
|---|---|---:|---:|
| mono | uniform | +6 | +4 to +7 |
| mono | clustered | +50 | +43 to +65 |
| loglow | uniform | +10 | +7 to +11 |
| loglow | clustered | +104 | +99 to +112 |
| bimodal | uniform | +161 | +125 to +182 |
| bimodal | clustered | +1380 | +1151 to +1413 |
| Pareto-like | uniform | +47 | +38 to +63 |
| Pareto-like | clustered | +513 | +290 to +513 |

**[NEGATIVE RESULT]** The proposed low-dispersion crossover was not observed, and the separated-bimodal condition did not provide an advantage. The sign remained positive across all tested conditions; this falsifies those expectations within the bounded matrix but does not show that a crossover cannot occur for other dispersions, object counts, domains, or policies (E3_no_observed_crossover).

**[BOUNDED OBSERVATION]** Clustered layouts had larger positive median differences than uniform layouts for each distribution. **[LIMITATION]** Layout changes also changed realized occupancy and overlap counts, and only one clustered parameterization and one domain were used; this pattern is not a general density law (E2_distribution_layout_pattern).

### Coverage and order control

**[METHOD CHECK]** In both runs, every result row had candidate true-overlap count equal to the all-pairs true-overlap count, so no false negatives were observed on these finite generated scenes under the declared AABB convention (E4_exact_overlap_coverage). **[METHOD CHECK]** The clustered-bimodal permutation fixture produced the same two-tier unique candidate count, 1861, before and after ID/insertion permutation in both runs. This supports order invariance only for that fixture and policy (E7_permutation_scope).

## Candidate novel findings

**[CANDIDATE NOVEL FINDING]** The narrowest surviving observation is: for this exact median/90th-percentile two-tier assignment/query policy, the policy produced more globally deduplicated candidate pairs than the declared best fixed-grid single-tier oracle on all 24 replicated n=320 cube scenes. The novelty audit found no exact overlap with the mapped studies, so this may be retained as a candidate exact-protocol result (NA1).

**[LIMITATION]** This is not evidence that adaptive spatial hashing, hierarchical hashing, or size-aware resolution is novel or generally ineffective. Those broader method families are established prior art [bandi1995adaptive; teschner2003optimized_hash; eitz2007hierarchical_hash; wong2012virtual_subdivision]. The candidate result also cannot isolate percentile selection from the complete tier assignment and cross-tier query policy (E6_policy_is_not_statistics_only; E10_prior_art_novelty_boundary).

## Threats to validity

**[LIMITATION]** External validity is narrow: the run used one object count, cube-only AABBs, one domain size, two layouts, no matched sparse/crowded factorial controls, no anisotropic objects, no domain-size sweep, and three deterministic seeds (E9_missing_factorial_coverage).

**[LIMITATION]** The fixed-grid oracle is selected after evaluating the declared grid, so it is a strong count-oriented comparator rather than one preselected production cell size. The two-tier method intentionally changes assignment and cross-tier querying, not only scale values. No both-tier insertion variant or alternative cross-tier policy was run (E6_policy_is_not_statistics_only; E8_unmeasured_costs).

**[LIMITATION]** Inclusive boundary and floor rules were shared but not stress-tested with objects exactly on cell boundaries. Integer overflow was not stress-tested, and the hash implementation was not independently reimplemented (E5_dedup_and_boundary_control; E4_exact_overlap_coverage).

**[LIMITATION]** Candidate counts alone do not establish wall-clock performance, memory use, cache behavior, insertion/query cost, or narrow-phase accuracy. Broad-phase systems and hierarchical representations can trade these quantities against candidate count [cohen1995icollide; gottschalk1996obbtree] (E8_unmeasured_costs).

## Limitations

**[LIMITATION]** The study is intentionally a bounded replicated benchmark rather than a full factorial evaluation. It omits assignment-policy sensitivity, intermediate dispersion sweeps, anisotropic AABBs, matched occupancy controls, larger object counts, and independent implementations. Consequently, it identifies a reproducible outcome for one protocol, not a causal explanation or universal ranking of spatial-hash designs (E6_policy_is_not_statistics_only; E9_missing_factorial_coverage).

## Conclusion

**[NEGATIVE RESULT]** Under the recorded bounded protocol, the median/90th-percentile two-tier spatial hash did not reduce broad-phase candidate pairs: it lost to the best declared single-tier grid in all 24 replicated scenes. The result is strongest as a reproducible negative result for the specified policy and benchmark, not as a general statement about adaptive hashing.

**[INFERENCE]** The positive differences across mono-size, low-dispersion, bimodal, and Pareto-like conditions suggest that percentile-derived scales plus this assignment/query policy were mismatched to the tested scenes, especially in clustered layouts, but the experiment does not identify whether the cause is scale selection, tier routing, cross-tier visits, occupancy, or an interaction among them. Resolving that explanation requires the omitted sensitivity and factorial experiments.

## References

**[FACT]** The complete machine-readable bibliography is in `references.bib`; citation IDs below map directly to `sources.jsonl`.

- `bandi1995adaptive` — Bandi and Thalmann, *An Adaptive Spatial Subdivision of the Object Space for Fast Collision Detection of Animated Rigid Bodies*, 1995.
- `teschner2003optimized_hash` — Teschner et al., *Optimized Spatial Hashing for Collision Detection of Deformable Objects*, 2003.
- `eitz2007hierarchical_hash` — Eitz and Gu, *Hierarchical Spatial Hashing for Real-Time Collision Detection*, 2007.
- `wong2012virtual_subdivision` — Wong, Leach, and Zambetta, *Virtual subdivision for GPU based collision detection of deformable objects using a uniform grid*, 2012.
- `cohen1995icollide` — Cohen et al., *I-COLLIDE: An Interactive and Exact Collision Detection System for Large-Scale Environments*, 1995.
- `gottschalk1996obbtree` — Gottschalk, Lin, and Manocha, *OBBTree: A Hierarchical Structure for Rapid Interference Detection*, 1996.
