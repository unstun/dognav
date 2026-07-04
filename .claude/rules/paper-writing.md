---
paths: ["3_paper/**", "**/*.tex", "**/*.bib"]
---
# Paper Writing Rules

## Language and Writing Flow

- MUST: draft paper body text in Chinese first, then polish into English after finalization. Project README-style documentation is also written in Chinese unless explicitly changed.
- MUST: paper polishing workflow: parallel agents collect real sentences from the same field -> extract sentence-pattern features -> rewrite according to those patterns while marking matched source sentences -> self-check that information was not lost.

## Four-Step Citation Check

1. Use `search_web` / Semantic Scholar to locate the paper.
2. Cross-check the DOI with two sources.
3. Run `curl -LH "Accept: application/x-bibtex" https://doi.org/<DOI>` to fetch BibTeX.
4. Confirm the claim exists in the original text.

If verification fails, mark `[CITATION NEEDED]`. Never generate BibTeX from memory.

## Claim-to-Contract Traceability

- MUST: every experimental claim in the paper maps to a Contract success/failure signal under `.pipeline/contracts/`.
- MUST: experiment results without a corresponding Contract must not be written as paper claims; mark `[NO CONTRACT]`.
- MUST: an experiment judged as failure by the Contract must not be repackaged as success in the paper.

## Forbidden

- NEVER: use parentheses for explanatory inserts, except abbreviation definitions such as Deep Reinforcement Learning (DRL). Prefer prose alternatives like "that is", "consists of", or "as shown in Figure...".
- NEVER: use code-style variable names in formulas. Use standard mathematical notation and omit punctuation at the end of display equations.
- NEVER: write methodology as enumerate-style paragraph lists; use prose narrative.
- NEVER: fabricate terminology, over-package simple concepts, or use sales language. Terminology must trace to literature.
