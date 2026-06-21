# Nametag Generator

Mail-merge data from a CSV onto an SVG nametag template and tile the results into
a grid sized for a **Glowforge Pro** laser cutter/engraver (19.5in x 11in bed).
Each nametag is copied verbatim from the template so the artwork — fonts, logo,
ruler and the cut border — is preserved intact; only the `{{...}}` placeholders
are replaced.

## Requirements

- Python 3.7 or higher
- **No third-party packages** — the standard library only.

## Quick start

```bash
python nametag_generator.py
```

With the bundled `template.svg` and `names.csv` this writes `output.svg`
containing one nametag per name, arranged in a grid that fits the Glowforge bed.

See [`samples/`](samples/) for five ready-to-use templates in different shapes
(rounded rectangle, oval, circle, rounded square, hexagon) with their own CSVs.

## Web app (no install)

[`index.html`](index.html) is a self-contained, browser-based version of the same
tool — no Python, no server, no dependencies. Drop in your template SVG and CSV,
adjust the gap/margin, preview the grid, and download each laid-out sheet. All
processing happens locally in your browser; nothing is uploaded.

**Run it three ways:**

- **Open locally** — double-click `index.html` (or open it in any browser).
- **GitHub Pages (free hosting)** — once this is merged to `main`, the included
  workflow ([`.github/workflows/pages.yml`](.github/workflows/pages.yml))
  publishes it automatically. In the repo, enable **Settings → Pages → Source:
  GitHub Actions** once; the app is then live at
  `https://joncamp.github.io/Nametag-Generator/`.
- **Gist** — paste `index.html` into a public [gist](https://gist.github.com) and
  open it through `https://htmlpreview.github.io/?<raw-gist-url>`.

The web app and the Python CLI share identical merge logic and produce
byte-for-byte identical output.

## How it works

1. Reads the template and locates the nametag artwork (the `<g>` whose Inkscape
   label is `Nametag`).
2. **Auto-detects every `{{TOKEN}}` placeholder** in that artwork and matches
   each to a CSV column of the same name — case-insensitive, any column order.
   A template can use one field (`{{NAME}}`) or many (`{{FIRSTNAME}}`,
   `{{LASTNAME}}`, `{{TITLE}}`, …); whatever the template declares, a matching
   CSV merges in automatically with no flags to change.
3. For each CSV row it copies the nametag, substitutes the placeholder values
   (XML-escaped), makes the copy's element ids unique, and wraps it in a
   `translate()` group at its grid cell.
4. Page size is read from the template's `viewBox` and the tag size from the
   `Nametag Border` element, so the grid auto-fits whatever bed the template
   describes. With the bundled 3.25in x 0.75in tag on a 19.5in x 11in bed this
   yields a **5 x 13 grid (65 tags per sheet)**.
5. If there are more rows than fit on one sheet, additional sheets are written
   as `output_2.svg`, `output_3.svg`, and so on.

**Any nametag shape.** The `Nametag Border` cut outline may be a `rect`,
`circle`, `ellipse`, `polygon`, or `polyline`; its bounding box defines the grid
tile size.

**Any template size or unit works.** The template's page is reproduced exactly —
the same `viewBox`, `width`, `height` and surrounding markup are kept verbatim,
so the output is dimensionally identical to the input. `--gap` and `--margin` are
given in millimetres and converted to the template's own coordinate system using
its declared physical `width`/`height`, so a 2&nbsp;mm gap is a real 2&nbsp;mm
gap whether the template is authored in millimetres, inches, points or pixels.
(If a template declares no absolute size, `--gap`/`--margin` are interpreted
directly in user units.)

The template is treated as read-only and is never modified.

## CSV format

A header row whose column names match the template's placeholders. Matching is
case-insensitive and order-independent; extra columns are ignored, and any
template field with no matching column is left blank (with a warning).

```csv
Name,Title,Company
Sally Joe,Engineer,Contoso
Jim Bob,Designer,Fabrikam
```

## Options

```
python nametag_generator.py [options]

  --template PATH     Template SVG (default: template.svg)
  --names PATH        CSV of merge data (default: names.csv)
  --output PATH       Output SVG; extra sheets get _2, _3 suffixes (default: output.svg)
  --gap MM            Gap between nametags in millimetres (default: 2.0)
  --margin MM         Margin around the grid in millimetres (default: 0.0)
```

Examples:

```bash
# Wider spacing and a 5mm margin around the sheet
python nametag_generator.py --gap 4 --margin 5

# A different shape + its CSV
python nametag_generator.py --template samples/05-hexagon.svg --names samples/05-hexagon.csv --output hex.svg
```

## Files

- `template.svg` — SVG template containing one nametag with `{{...}}` placeholders.
- `names.csv` — merge data; column headers match the template's placeholders.
- `nametag_generator.py` — the generator.
- `index.html` — browser-based version of the generator (no install).
- `output.svg` — generated grid (created when you run the tool).
- `samples/` — example templates in various shapes, each with a matching CSV.

## Template requirements

- The nametag artwork must live in a group labelled `Nametag`
  (`inkscape:label="Nametag"`).
- That group must contain at least one `{{TOKEN}}` placeholder.
- The cut outline must be labelled `Nametag Border`
  (`inkscape:label="Nametag Border"`); it may be a `rect`, `circle`, `ellipse`,
  `polygon`, or `polyline`, and its bounding box defines the tile size.
- The root `<svg>` must have a `viewBox`. Its `width`/`height` (in any absolute
  unit — mm, in, pt, px…) define the physical bed size; the grid and the
  `--gap`/`--margin` spacing adapt to it automatically. The page is otherwise
  reproduced exactly in the output.
