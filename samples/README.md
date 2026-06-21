# Sample nametag templates

Five ready-to-use templates in different shapes, each sized for a nametag you'd
pin to a shirt, paired with a matching CSV. They demonstrate that the generator
**auto-detects whichever `{{TOKEN}}` placeholders a template uses** and merges in
any CSV whose column names match — by name, case-insensitive, in any order.

| Sample | Shape | Tag size | Placeholders / CSV columns |
|--------|-------|----------|----------------------------|
| `01-classic-badge` | Rounded rectangle | 3.5in x 2.25in | `{{NAME}}`, `{{ROLE}}` |
| `02-oval` | Ellipse | 3.5in x 2.2in | `{{FIRSTNAME}}`, `{{LASTNAME}}` |
| `03-circle` | Circle | 2.75in dia. | `{{NAME}}`, `{{TEAM}}` |
| `04-rounded-square` | Rounded square | 2.75in x 2.75in | `{{NAME}}`, `{{PRONOUNS}}` |
| `05-hexagon` | Hexagon | 3.4in x 3.0in | `{{NAME}}`, `{{TITLE}}`, `{{COMPANY}}` |

Each template's bed is the Glowforge Pro 19.5in x 11in, and the red shape is the
cut line, so the generated grid is ready to send straight to the laser.

## Run one

From the repository root:

```bash
python nametag_generator.py --template samples/03-circle.svg --names samples/03-circle.csv --output circle-tags.svg
```

The tool reports the fields it detected and which CSV columns matched, e.g.:

```
Bed: 19.50in x 11.00in   Tag: 2.75in x 2.75in
Fields: name, team  (matched CSV columns: name, team)
Grid: 6 cols x 3 rows = 18 tags/sheet
Records: 6  ->  1 sheet(s)
```

## Make your own

Copy any sample, change the `{{TOKEN}}` placeholders to the fields you want, and
provide a CSV with matching column headers — no code or flags to change. Keep the
two conventions the generator relies on:

- the artwork lives in a group labelled `inkscape:label="Nametag"`, and
- the cut outline is labelled `inkscape:label="Nametag Border"` (it may be a
  `rect`, `circle`, `ellipse`, `polygon`, or `polyline` — its bounding box sets
  the grid tile size).
