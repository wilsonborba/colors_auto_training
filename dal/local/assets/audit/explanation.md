# dal/local/assets/audit

Frozen audit dataset (never used for training).

Put here:
- `img/` (or equivalent): the 1,000 audit images
- `annotations/` (or `labels.csv`): ground truth annotations
- optional: `datasheet.md` describing collection/coverage/limits

Rule:
- Do not write training outputs here.
- Do not add samples casually; changes must be deliberate and versioned.
