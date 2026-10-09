# ADR-0027: Quarantine unusable agenda evidence

* Status: Accepted
* Date: 2026-10-09

## Context

The agenda counted every title cluster as one usable provenance group. `NOT-010` in the
historical corpus is an instruction payload, yet it acquired partial evidence and could
enable a draft. A controlled decision client assigning high scores reproduced the failure.
Sanitizing the model prompt alone did not prevent the original payload from becoming a claim.

## Decision

Exclude titles flagged by the existing injection detector when selecting the lead article.
If no usable title remains, assign evidence component zero, `INSUFICIENTE` evidence state and
an empty claim list. Preserve source IDs and the source excerpt for inspection. The official
attention weights remain unchanged; draft generation continues to apply the evidence guard.

## Consequences and validation

`test_injected_source_cannot_become_publishable_even_with_high_decision_scores` failed before
the correction and passes afterward. It uses the actual `NOT-010` record, derives the case
through the agenda service and verifies that high scores cannot enable generation.

The detector uses explicit patterns, so false positives and undetected attacks remain possible.
A clean title is not proof of semantic support, independent provenance or truth. Other news
clusters remain partial until stronger evidence is established; human review remains required.
