---
name: excel-analysis
description: Guidelines for analyzing multi-sheet Excel files, complex headers, and numeric data
---

## Handling Multi-Sheet Excel Files
- Parse ALL sheets; note each sheet name in the output.
- If a sheet named "Summary" or "Overview" exists, read it first to understand the overall structure.
- Clearly note which sheets contain raw data and which contain pivots/summaries.

## Reading Files with the Correct Header
The following variables are automatically injected into every run_code call:
- file_path: path to the first file (= file_paths[0])
- file_paths: list of paths to all files in the conversation
- files_metadata: list of dicts {suggested_header_row, sheets_columns} matching the same index as file_paths
- suggested_header_row: header row of file_paths[0]
- sheet_names: list of sheet names of file_paths[0]
- sheets_columns: dict {sheet_name: [column names]} of file_paths[0]

Standard pattern — 1 file:
  import pandas as pd
  df = pd.read_excel(file_path, sheet_name=sheet_names[0], header=suggested_header_row)
  print(df.columns.tolist())          # always print column names before accessing

Pattern — multiple files (accessing second file onward):
  import pandas as pd
  meta1 = files_metadata[1]
  df1 = pd.read_excel(file_paths[1], header=meta1['suggested_header_row'])
  print(df1.columns.tolist())

Note on integer column names: if sheets_columns contains 1, 6, 9 (integers), access them as int:
  df[1]  # Correct
  df['1']  # Wrong — KeyError

If column names are wrong after using suggested_header_row:
1. Try header=0 through header=9 (up to 10 attempts), printing df.columns each time.
2. If still wrong after 10 tries, read raw (header=None, nrows=12) and print everything.

## Merged Headers
- If the first row has merged cells, flatten to a single row.
- Column names after flattening: join parts with " > " (e.g. "Revenue > Q1").

## Date Formatting
- Auto-detect date columns and convert to ISO 8601 (YYYY-MM-DD).
- Warn if mixed formats exist within the same column.

## Anomalies to Check
- Negative values in monetary/revenue/quantity columns → flag as anomaly.
- Null or zero values exceeding 20% of a column → warn about data quality.
- Outliers (> 3 standard deviations) → mark for verification.

## Trend Analysis
- If time-series data is present, calculate period-over-period growth (QoQ, MoM, YoY).
- Compare actuals vs. plan if both columns exist.

## Creating Charts

The `output_dir` variable is pre-injected — save images there so the frontend can download them.

STEP 1 — CALL THIS TOOL BEFORE WRITING ANY CHART CODE:
  read_reference(skill="excel-analysis", filename="chart_templates.md")
Choose an appropriate template, copy it, and adjust for the user's request.

STEP 2 — Mandatory rules in chart code:
- Call `matplotlib.use('Agg')` BEFORE importing pyplot (avoids GUI errors on the server)
- Call `plt.close()` after saving
- The last line MUST be: `print(f"chart_saved:{chart_path}")` — print exactly this format, NOT JSON, NOT a dict
- File names must be lowercase, no accents, no spaces

Preferred library: seaborn as default. Fall back to plain matplotlib only if seaborn import fails.

Correct example (last line):
  chart_path = f"{output_dir}/chart_revenue.png"
  plt.savefig(chart_path)
  plt.close()
  print(f"chart_saved:{chart_path}")    # CORRECT

Wrong examples — do NOT do this:
  print({"chart_saved": chart_path})    # WRONG — backend cannot parse
  print(json.dumps({"chart_saved": chart_path}))  # WRONG
