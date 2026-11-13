# TMS import formats

Column names and conventions per system. Produce the internal field set first,
then map. When the target is unknown, export the TestRail shape — it imports into
most systems with minor column renaming.

## The multi-row step convention

All of these systems read steps as separate rows: case-level fields on the first
row, blank on continuation rows.

```csv
"ID","Title","Priority","Preconditions","Step","Step Data","Expected Result","References"
"TC-283-01","Connect a workspace","High","User is signed in","Open Settings → Integrations","","The Integrations page loads","F-283-01"
"","","","","Click Connect Confluence","","A dialog opens with two fields",""
"","","","","Enter the workspace URL","https://acme.atlassian.net","The field accepts the value",""
```

A single cell containing all steps imports as one block that no tester can follow
and no TMS can show step-level results against.

## TestRail

```csv
"Title","Section","Template","Type","Priority","Estimate","References","Preconditions","Steps","Expected Result","Custom_external_id"
```

- `Section` takes a path: `Platform > Integrations > Confluence`
- Use the *Test Case (Steps)* template for per-step rows
- `Custom_external_id` holds your stable ID and is the idempotency key for re-import
- Priority values: `Critical`, `High`, `Medium`, `Low`

## Xray (Jira)

```csv
"Issue Key","Summary","Description","Test Type","Priority","Labels","Components","Action","Data","Expected Result","Test Repository Path","Requirement"
```

- Leave `Issue Key` empty to create; fill it to update
- `Test Type` is `Manual`
- `Test Repository Path` takes `/Platform/Integrations/Confluence`
- `Requirement` links to the Jira issue key, which is what produces the coverage view

## Zephyr Scale

```csv
"Name","Objective","Precondition","Folder","Status","Priority","Owner","Labels","Test Script Type","Step","Test Data","Expected Result","Issues"
```

- `Test Script Type` is `STEP_BY_STEP`
- `Folder` takes `/Platform/Integrations/Confluence`
- `Issues` accepts a comma-separated list of Jira keys

## qTest

```csv
"Id","Name","Description","Precondition","Test Step Description","Test Step Expected Result","Module","Priority","Type","Status"
```

- `Module` is the folder path, slash-separated

## Azure Test Plans

```csv
"ID","Work Item Type","Title","Test Step","Step Action","Step Expected","Area Path","Priority","State"
```

- `Work Item Type` is `Test Case`
- `Step Action` and `Step Expected` support limited HTML; plain text is safer

## Generic XLSX

When no system is named, produce an XLSX with two sheets:

- **Test Cases** — one row per case, steps in a numbered block
- **Steps** — one row per step, keyed by case ID

Freeze the header row, set column widths, and wrap long text. The person opening
this has not asked for a spreadsheet puzzle.

## Encoding

UTF-8 **with BOM**, comma-separated, CRLF line endings, every field quoted.
Without the BOM, Excel corrupts non-ASCII characters silently on open — and the
person importing will not notice until the cases are already in the system with
broken text.

Verify by reading the file back and parsing it before reporting completion.
