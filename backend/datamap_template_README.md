# DataLens Datamap Template

Upload an Excel file (.xlsx) with the following columns (exact names, case-insensitive):

| Column | Required | Description |
|---|---|---|
| `question_id` | Yes | Groups variables belonging to the same question (e.g. Q5 for a multi-response question) |
| `variable_name` | Yes | Exact SPSS variable name |
| `question_text` | Yes | Human-readable question label shown in the UI |
| `question_type` | Yes | `single`, `multi`, `grid`, or `numeric` |
| `answer_option` | No | Label for this specific answer option / variable |
| `is_weight` | No | Set to `Yes` for the rim weight variable row |

## Example rows

| question_id | variable_name | question_text | question_type | answer_option | is_weight |
|---|---|---|---|---|---|
| Q1 | Q1 | Overall satisfaction with Brand X | single | | |
| Q5 | Q5_1 | Brands you are aware of | multi | Brand A | |
| Q5 | Q5_2 | Brands you are aware of | multi | Brand B | |
| Q5 | Q5_3 | Brands you are aware of | multi | Brand C | |
| Q8 | Q8 | Likelihood to recommend (0-10) | numeric | | |
| WAVE | WAVE | Survey wave | single | | |
| WT | wgt_final | Rim weight | single | | Yes |

## Notes
- For **single-code** questions, one row per question is sufficient.
- For **multi-response** questions, add one row per option variable, all sharing the same `question_id`.
- The `wave_variable` is the SPSS variable that identifies which wave each respondent belongs to. Specify its name when uploading via the UI.
- The weight row (is_weight = Yes) does not need a question_id; only the variable_name matters.
