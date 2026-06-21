# MailMerge-SVG

Mail-merge data from a CSV onto an SVG template and produce ready-to-use output in
one of two layouts:

- **Grid mode** — tile many small records (name badges, labels, place cards) into a
  grid sized for a **Glowforge Pro** laser cutter/engraver (19.5in x 11in bed).
- **Individual mode** — emit one full-page SVG per CSV row (certificates, awards,
  invitations, signage).

In both modes every copy is taken verbatim from the template, so the artwork —
fonts, logos, borders, embedded images — is preserved intact; only the `{{...}}`
placeholders are replaced. The tool picks the layout **automatically** from the
template, or you can force it with `--mode`.

## Requirements

- Python 3.7 or higher
- **No third-party packages** — the standard library only.

## Quick start

```bash
# Grid of name badges (bundled template.svg + names.csv -> output.svg)
python mailmerge.py

# One certificate SVG per row, written to a folder
python mailmerge.py --template samples/certificate.svg --names samples/certificate.csv --out-dir out
```

The first command writes `output.svg` containing one badge per name, arranged in a
grid that fits the Glowforge bed. The second auto-detects that the certificate has
no repeating tile and writes one file per row (e.g. `out/John Doe.svg`).

See [`samples/`](samples/) for ready-to-use templates — five grid shapes (rounded
rectangle, oval, circle, rounded square, hexagon) plus a full-page certificate.

## Modes

| Mode | When it's used | Output |
| --- | --- | --- |
| `grid` | Template has a repeating tile group (label `Nametag`, `Tile`, or `Cell`) | A tiled sheet (`output.svg`, paginated to `output_2.svg`, …) |
| `individual` | Template has no tile group | One file per CSV row in `--out-dir` |
| `auto` (default) | — | Picks `grid` if a tile group is found, otherwise `individual` |

## Web app (no install)

[`index.html`](index.html) is a self-contained, browser-based version of the same
tool — no Python, no server, no dependencies. Drop in your template SVG and CSV,
pick the mode, preview the result, and download a single file or all of them as a
`.zip`. All processing happens locally in your browser; nothing is uploaded.

**Run it three ways:**

- **Open locally** — double-click `index.html` (or open it in any browser).
- **GitHub Pages (free hosting)** — the included workflow
  ([`.github/workflows/pages.yml`](.github/workflows/pages.yml)) publishes it on
  every push to `main`. Enable **Settings → Pages → Source: GitHub Actions** once;
  the app is then live at `https://joncamp.github.io/MailMerge-SVG/`.
- **Gist** — paste `index.html` into a public [gist](https://gist.github.com) and
  open it through `https://htmlpreview.github.io/?<raw-gist-url>`.

The web app and the Python CLI share identical merge logic and produce
byte-for-byte identical output.

## How it works

1. Reads the template and looks for a repeating **tile group** (the `<g>` whose
   Inkscape label is `Nametag`, `Tile`, or `Cell`). If one exists → grid mode; if
   not → individual mode.
2. **Auto-detects every `{{TOKEN}}` placeholder** and matches each to a CSV column
   of the same name — case-insensitive, any column order. A template can use one
   field (`{{NAME}}`) or many (`{{NAME}}`, `{{POSITION}}`, `{{DATE}}`, …); whatever
   the template declares, a matching CSV merges in automatically with no flags to
   change.
3. **Grid mode** copies the tile per row, substitutes the placeholder values
   (XML-escaped), makes the copy's element ids unique, and wraps it in a
   `translate()` group at its grid cell. Page size is read from the template's
   `viewBox` and the tile size from the `… Border` element, so the grid auto-fits
   whatever bed the template describes. With the bundled 3.25in x 0.75in tag on a
   19.5in x 11in bed this yields a **5 x 13 grid (65 tags per sheet)**; overflow
   rows spill onto `output_2.svg`, `output_3.svg`, …
4. **Individual mode** substitutes the placeholders across the whole template and
   writes one file per row, named after a chosen field (`--name-field`, defaulting
   to the first matched field). Filenames are sanitised and de-duplicated
   (`Ada Lovelace.svg`, `Ada Lovelace-2.svg`, …). The output is byte-for-byte the
   template with its tokens replaced — no re-serialisation.

**Any tile shape.** In grid mode the `… Border` cut outline may be a `rect`,
`circle`, `ellipse`, `polygon`, or `polyline`; its bounding box defines the tile
size.

**Any template size or unit works.** The template's page is reproduced exactly —
the same `viewBox`, `width`, `height` and surrounding markup are kept verbatim, so
the output is dimensionally identical to the input. In grid mode `--gap` and
`--margin` are given in millimetres and converted to the template's own coordinate
system using its declared physical `width`/`height`, so a 2&nbsp;mm gap is a real
2&nbsp;mm gap whether the template is authored in millimetres, inches, points or
pixels. (If a template declares no absolute size, `--gap`/`--margin` are
interpreted directly in user units.)

The template is treated as read-only and is never modified.

## CSV format

A header row whose column names match the template's placeholders. Matching is
case-insensitive and order-independent; extra columns are ignored, and any template
field with no matching column is left blank (with a warning).

```csv
Name,Title,Company
Sally Joe,Engineer,Contoso
Jim Bob,Designer,Fabrikam
```

## Options

```
python mailmerge.py [options]

  --template PATH     Template SVG (default: template.svg)
  --names PATH        CSV of merge data (default: names.csv)
  --mode MODE         auto | grid | individual (default: auto)

  Grid mode:
  --output PATH       Output SVG; extra sheets get _2, _3 suffixes (default: output.svg)
  --gap MM            Gap between tiles in millimetres (default: 2.0)
  --margin MM         Margin around the grid in millimetres (default: 0.0)

  Individual mode:
  --out-dir DIR       Folder for the per-row SVGs (default: output)
  --name-field FIELD  Template field used to name each file (default: first matched field)
```

Examples:

```bash
# Wider spacing and a 5mm margin around the grid sheet
python mailmerge.py --gap 4 --margin 5

# A different grid shape + its CSV
python mailmerge.py --template samples/05-hexagon.svg --names samples/05-hexagon.csv --output hex.svg

# Certificates: one file per row, named by the POSITION field instead of NAME
python mailmerge.py --template samples/certificate.svg --names samples/certificate.csv \
  --out-dir certs --name-field position

# Force a mode (e.g. emit individual files from a template that also has a tile)
python mailmerge.py --mode individual --out-dir out
```

## Files

- `template.svg` — grid template containing one tile with `{{...}}` placeholders.
- `names.csv` — merge data; column headers match the template's placeholders.
- `mailmerge.py` — the generator (grid + individual modes).
- `index.html` — browser-based version of the generator (no install).
- `output.svg` — generated grid (created when you run grid mode).
- `samples/` — example templates: five grid shapes and a full-page certificate,
  each with a matching CSV.

## Template requirements

**Grid mode**

- The tile artwork must live in a group labelled `Nametag`, `Tile`, or `Cell`
  (`inkscape:label="Tile"`).
- That group must contain at least one `{{TOKEN}}` placeholder.
- The cut outline must be labelled `<tile-label> Border` (e.g.
  `inkscape:label="Tile Border"`); it may be a `rect`, `circle`, `ellipse`,
  `polygon`, or `polyline`, and its bounding box defines the tile size.

**Individual mode**

- Any SVG containing at least one `{{TOKEN}}` placeholder. No tile group is needed.

**Both modes**

- The root `<svg>` must have a `viewBox`. Its `width`/`height` (in any absolute
  unit — mm, in, pt, px…) define the physical size; in grid mode the grid and the
  `--gap`/`--margin` spacing adapt to it automatically. The page is otherwise
  reproduced exactly in the output.

---

*Formerly **Nametag-Generator**. It now also subsumes the old Certificate-Generator
tool via individual mode.*
