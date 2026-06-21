# Nametag Generator

Mail-merge a list of names from a CSV onto an SVG nametag template and tile the
results into a grid sized for a **Glowforge Pro** laser cutter/engraver
(19.5in x 11in bed). Each nametag is copied verbatim from the template so the
artwork — fonts, logo, ruler and the red cut border — is preserved intact; only
the `{{NAME}}` placeholder is replaced.

## Requirements

- Python 3.7 or higher
- **No third-party packages** — the standard library only.

## Quick start

```bash
python nametag_generator.py
```

With the bundled `template.svg` and `names.csv` this writes `output.svg`
containing one nametag per name, arranged in a grid that fits the Glowforge bed.

## How it works

1. Reads `template.svg` and locates the nametag artwork (the `<g>` whose Inkscape
   label is `Nametag`).
2. Reads names from the first column of `names.csv` (a leading `Name` header row
   is skipped automatically).
3. For each name it copies the nametag, substitutes `{{NAME}}` (XML-escaped),
   makes the copy's element ids unique, and wraps it in a `translate()` group at
   its grid cell.
4. Page size is read from the template's `viewBox` and the tag size from the
   `Nametag Border` rectangle, so the grid auto-fits whatever bed the template
   describes. With the bundled 3.25in x 0.75in tag on a 19.5in x 11in bed this
   yields a **5 x 13 grid (65 tags per sheet)**.
5. If there are more names than fit on one sheet, additional sheets are written
   as `output_2.svg`, `output_3.svg`, and so on.

**Any template size or unit works.** The template's page is reproduced exactly —
the same `viewBox`, `width`, `height` and surrounding markup are kept verbatim,
so the output is dimensionally identical to the input. `--gap` and `--margin` are
given in millimetres and converted to the template's own coordinate system using
its declared physical `width`/`height`, so a 2&nbsp;mm gap is a real 2&nbsp;mm
gap whether the template is authored in millimetres, inches, points or pixels.
(If a template declares no absolute size, `--gap`/`--margin` are interpreted
directly in user units.)

The template is treated as read-only and is never modified.

## Options

```
python nametag_generator.py [options]

  --template PATH     Template SVG (default: template.svg)
  --names PATH        CSV of names (default: names.csv)
  --output PATH       Output SVG; extra sheets get _2, _3 suffixes (default: output.svg)
  --gap MM            Gap between nametags in millimetres (default: 2.0)
  --margin MM         Margin around the grid in millimetres (default: 0.0)
  --placeholder TEXT  Placeholder string to replace (default: {{NAME}})
  --column NAME       CSV column to read names from (default: first column)
```

Examples:

```bash
# Wider spacing and a 5mm margin around the sheet
python nametag_generator.py --gap 4 --margin 5

# Custom files and a named CSV column
python nametag_generator.py --names attendees.csv --output tags.svg --column "Full Name"
```

## Files

- `template.svg` — SVG template containing one nametag with a `{{NAME}}` placeholder.
- `names.csv` — names to merge (first column; optional `Name` header).
- `nametag_generator.py` — the generator.
- `output.svg` — generated grid (created when you run the tool).

## Template requirements

- The nametag artwork must live in a group labelled `Nametag`
  (`inkscape:label="Nametag"`).
- That group must contain the text placeholder `{{NAME}}`.
- The cut border rectangle should be labelled `Nametag Border`
  (`inkscape:label="Nametag Border"`); its width/height define the tile size.
- The root `<svg>` must have a `viewBox`. Its `width`/`height` (in any absolute
  unit — mm, in, pt, px…) define the physical bed size; the grid and the
  `--gap`/`--margin` spacing adapt to it automatically. The page is otherwise
  reproduced exactly in the output.
