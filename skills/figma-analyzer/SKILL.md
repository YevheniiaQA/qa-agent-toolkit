---
name: figma-analyzer
description: Reads Figma designs through MCP and extracts UI elements, states, texts, and constraints into structured data that UI scenario generation and selector collection can consume. Use this skill for any frontend ticket that links a design, whenever the user asks what test cases a mockup implies, whenever requirements text and the design appear to disagree, or before generating UI scenarios. Also use it to catch state-level distinctions such as hidden versus disabled, empty states, and error states that written requirements routinely omit.
---

# Figma Analyzer

A design is a specification that nobody writes down in words. Screenshots are not
enough — the layer structure carries states, variants, and constraints that
determine whether two test cases exist or one.

## Disabled integrations

Follow `qa-conventions` → *Disabled integrations* for Figma (`figma`): read `INTEGRATIONS`, skip a
system that is not listed, report it as `➖ <system> disabled for this project`, never route
around a `qa-guard` block.

**Local alternative:** work from exported frames or screenshots the engineer supplies and say which states they cover. Without either, mark every design-dependent check as blocked on the design rather than inferring the UI from the requirements.

## What to extract

For every screen in scope:

1. **Interactive elements** — buttons, inputs, selects, toggles, links. Record the
   visible label, the element type, and any variant names (`primary/disabled`,
   `input/error`).
2. **States and variants.** This is the highest-value output. A component set with
   `default / hover / focus / disabled / error / loading` implies six checks.
   A missing state implies an open question.
3. **Exact texts.** Labels, placeholders, helper text, error messages, empty-state
   copy, button captions. Scenario assertions quote these verbatim, so copy them
   character for character including punctuation.
4. **Constraints** — max lengths visible in the design, character counters,
   responsive breakpoints, truncation behaviour.
5. **Navigation** — what each control leads to, modal versus page, dismissal paths.
6. **Empty, loading, and error screens.** Teams design them and then forget to
   mention them in the ticket. They are usually the richest source of missed cases.

## Distinctions that change test count

Record these explicitly, because the requirements text almost never does:

| Design shows | Implies |
|---|---|
| Hidden element | Assert absence — element not in the DOM |
| Disabled element | Assert presence + disabled state + no action on click |
| Read-only field | Assert value rendered, input rejected, still submitted |
| Skeleton/loading state | Assert intermediate state exists, not just final |
| Truncated text with tooltip | Assert both truncation and full value on hover/focus |
| Error inline vs toast | Different locator, different assertion, different timing |

## Output

Write to `02-analysis/<TICKET-ID>/design/`:

```
FIGMA_DATA.json      Structured element/state/text inventory per screen
DESIGN_NOTES.md      Human-readable findings, states, and implied cases
```

`FIGMA_DATA.json` shape:

```json
{
  "screens": [
    {
      "name": "Integrations / Connect Confluence",
      "figmaNodeId": "12:345",
      "elements": [
        {
          "role": "textbox",
          "label": "Confluence URL",
          "placeholder": "https://your-domain.atlassian.net",
          "states": ["default", "focus", "error"],
          "errorText": "Enter a valid URL",
          "constraints": { "required": true }
        },
        {
          "role": "button",
          "label": "Connect",
          "states": ["default", "disabled", "loading"],
          "notes": "Disabled until both fields filled"
        }
      ],
      "emptyState": { "text": "No integrations yet", "cta": "Connect your first" }
    }
  ]
}
```

## Discrepancy reporting

When the design and the written requirements disagree, do not pick a winner here.
Append an entry to `02-analysis/<TICKET-ID>/DISCREPANCIES.md` with type
`FIGMA_REQ_MISMATCH`, both versions quoted, and the screen reference.
`discrepancies-fix` owns resolution and knows the priority rules.

## Accessibility signals worth capturing

Designs encode accessibility intent that gets lost in implementation: focus order
implied by layout, colour contrast of text on backgrounds, icon-only buttons that
will need accessible names, form labels that are placeholders only. Flag each of
these as an accessibility check for the UI scenarios, since catching them at
design-review cost is far cheaper than after release.
