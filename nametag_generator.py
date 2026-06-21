"""Nametag grid mail-merge for laser cutting.

Reads a list of names from a CSV and performs a "mail merge" against an SVG
template that contains a single nametag with a ``{{NAME}}`` placeholder. The
nametags are tiled into a grid sized to fit the bed of a Glowforge Pro
(19.5in x 11in), with a small gap between tags so each one is cut separately.

Design goals:
- Keep the template SVG as intact as possible. The nametag artwork is copied
  verbatim from the template (the raw XML is sliced out as text rather than
  being re-serialized), so fonts, the logo, the ruler and the cut border are
  preserved byte-for-byte. The only changes are the substituted name, made-unique
  element ids, and a wrapping ``translate()`` group that positions each copy.
- No third-party dependencies -- standard library only.
"""

import argparse
import csv
import os
import re
import sys


# --- placeholder / label configuration -------------------------------------

DEFAULT_PLACEHOLDER = "{{NAME}}"
NAMETAG_LABEL = "Nametag"
BORDER_LABEL = "Nametag Border"

MM_PER_INCH = 25.4

# Conversion of CSS/SVG absolute length units to millimetres. ``None`` marks
# units that have no fixed physical size (``%`` or unitless user units).
UNIT_TO_MM = {
    "": None,
    "mm": 1.0,
    "cm": 10.0,
    "q": 0.25,
    "in": 25.4,
    "pt": 25.4 / 72.0,
    "pc": 25.4 / 6.0,
    "px": 25.4 / 96.0,
    "%": None,
}

_LENGTH = re.compile(r"^\s*([+-]?[0-9]*\.?[0-9]+)\s*([a-z%]*)\s*$", re.IGNORECASE)


def parse_length(value):
    """Split an SVG length like ``19.5in`` into (number, unit). Returns
    (None, None) when the value is missing or unparseable."""
    m = _LENGTH.match(value or "")
    if not m:
        return None, None
    return float(m.group(1)), m.group(2).lower()


def fmt(value):
    """Format a float compactly (trim trailing zeros) for SVG attributes."""
    return f"{value:.5f}".rstrip("0").rstrip(".")


def xml_escape_text(text):
    """Escape a string for use as XML text content."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


# --- template parsing -------------------------------------------------------

_G_TOKEN = re.compile(r"<g(?=[\s>])|</g>")
_ID_ATTR = re.compile(r'(?<=\s)id="([^"]*)"')


def find_labeled_group(svg_text, label):
    """Return (start, end) char offsets of the <g> whose opening tag carries
    ``inkscape:label="<label>"``, spanning the full element including nested
    groups. Raises ValueError if not found."""
    needle = f'inkscape:label="{label}"'
    label_pos = svg_text.find(needle)
    if label_pos == -1:
        raise ValueError(f'Could not find a <g> with inkscape:label="{label}" in the template.')

    # The label is an attribute of an opening tag; walk back to that tag's '<'.
    start = svg_text.rfind("<", 0, label_pos)
    if start == -1 or svg_text[start:start + 2] != "<g":
        raise ValueError(f'Malformed template: label "{label}" is not on a <g> element.')

    # Walk forward, tracking <g> nesting depth, to find the matching </g>.
    depth = 0
    pos = start
    while True:
        m = _G_TOKEN.search(svg_text, pos)
        if m is None:
            raise ValueError(f'Unbalanced <g> tags while extracting "{label}".')
        token = m.group()
        if token == "</g>":
            depth -= 1
            pos = m.end()
            if depth == 0:
                return start, pos
        else:  # an opening "<g"
            gt = svg_text.find(">", m.end())
            if gt == -1:
                raise ValueError("Malformed template: unterminated <g> tag.")
            self_closing = svg_text[gt - 1] == "/"
            if not self_closing:
                depth += 1
            pos = gt + 1


def get_attr(tag_text, name):
    """Read a single attribute value out of an element's opening-tag text."""
    m = re.search(rf'{re.escape(name)}="([^"]*)"', tag_text)
    return m.group(1) if m else None


def parse_page(svg_text):
    """Inspect the root <svg> element.

    Returns ``(width_uu, height_uu, uu_per_mm)`` where the page size is given in
    the template's own user units (its viewBox), and ``uu_per_mm`` is how many of
    those user units make up one millimetre -- derived from the declared
    ``width``/``height`` so that physical spacing is honoured no matter what
    units or dimensions the template uses. ``uu_per_mm`` is ``None`` when the
    template gives no absolute physical size (then spacing falls back to being
    interpreted directly in user units)."""
    svg_start = svg_text.find("<svg")
    svg_open_end = svg_text.find(">", svg_start)
    svg_tag = svg_text[svg_start:svg_open_end]

    view_box = get_attr(svg_tag, "viewBox")
    if not view_box:
        raise ValueError("Template <svg> has no viewBox; cannot determine page size.")
    parts = view_box.replace(",", " ").split()
    if len(parts) != 4:
        raise ValueError(f"Unexpected viewBox value: {view_box!r}")
    vb_w, vb_h = float(parts[2]), float(parts[3])

    uu_per_mm = _scale_from_dimension(get_attr(svg_tag, "width"), vb_w)
    if uu_per_mm is None:
        uu_per_mm = _scale_from_dimension(get_attr(svg_tag, "height"), vb_h)

    return vb_w, vb_h, uu_per_mm


def _scale_from_dimension(dim_value, viewbox_extent):
    """User units per millimetre implied by a physical width/height attribute
    paired with the matching viewBox extent. Returns ``None`` if it can't be
    determined (missing, percentage, or unitless)."""
    value, unit = parse_length(dim_value)
    if value is None or not viewbox_extent:
        return None
    mm_per_unit = UNIT_TO_MM.get(unit)
    if mm_per_unit is None:
        return None
    physical_mm = value * mm_per_unit
    if physical_mm <= 0:
        return None
    return viewbox_extent / physical_mm


def parse_tag_geometry(nametag_xml):
    """Return (width, height, stroke) of the Nametag Border rect, in the
    template's user units (the same space as the viewBox and transforms)."""
    border_pos = nametag_xml.find(f'inkscape:label="{BORDER_LABEL}"')
    if border_pos == -1:
        raise ValueError(f'Could not find the "{BORDER_LABEL}" rect in the nametag group.')
    rect_start = nametag_xml.rfind("<rect", 0, border_pos)
    rect_end = nametag_xml.find(">", border_pos)
    rect_tag = nametag_xml[rect_start:rect_end]

    width = get_attr(rect_tag, "width")
    height = get_attr(rect_tag, "height")
    if width is None or height is None:
        raise ValueError("Nametag Border rect is missing width/height.")

    stroke = 0.0
    style = get_attr(rect_tag, "style") or ""
    m = re.search(r"stroke-width:([0-9.]+)", style)
    if m:
        stroke = float(m.group(1))
    return float(width), float(height), stroke


# --- grid layout ------------------------------------------------------------

def compute_grid(page_w, page_h, tag_w, tag_h, stroke, gap, margin):
    """Compute how many columns/rows of tags fit on the bed."""
    pitch_x = tag_w + gap
    pitch_y = tag_h + gap
    avail_w = page_w - stroke - 2 * margin
    avail_h = page_h - stroke - 2 * margin

    cols = int((avail_w - tag_w) / pitch_x) + 1 if avail_w >= tag_w else 0
    rows = int((avail_h - tag_h) / pitch_y) + 1 if avail_h >= tag_h else 0
    cols = max(cols, 1)
    rows = max(rows, 1)
    return cols, rows, pitch_x, pitch_y


# --- name copy generation ---------------------------------------------------

def make_tag_copy(nametag_xml, name, index, placeholder, tx, ty):
    """Return a positioned, name-substituted copy of the nametag group."""
    body = nametag_xml.replace(placeholder, xml_escape_text(name))
    # Make every id unique to this copy so the merged SVG stays valid.
    body = _ID_ATTR.sub(lambda m: f'id="{m.group(1)}__{index}"', body)
    return (
        f'<g id="nametag-{index}" '
        f'inkscape:label="Nametag {index + 1}" '
        f'transform="translate({fmt(tx)},{fmt(ty)})">'
        f"{body}</g>"
    )


# --- csv input --------------------------------------------------------------

def read_names(csv_path, column=None):
    """Read names from a CSV. Uses the named column when given, otherwise the
    first column. A leading ``Name`` header row is skipped automatically."""
    with open(csv_path, newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.reader(fh))
    if not rows:
        return []

    col_index = 0
    data_rows = rows
    header = [c.strip() for c in rows[0]]
    if column is not None:
        lowered = [h.lower() for h in header]
        if column.lower() in lowered:
            col_index = lowered.index(column.lower())
            data_rows = rows[1:]
        else:
            raise ValueError(f'Column "{column}" not found in CSV header: {header}')
    elif header and header[0].lower() == "name":
        data_rows = rows[1:]

    names = []
    for row in data_rows:
        if col_index < len(row):
            value = row[col_index].strip()
            if value:
                names.append(value)
    return names


# --- output assembly --------------------------------------------------------

def page_filename(output_path, page_number):
    if page_number == 1:
        return output_path
    stem, ext = os.path.splitext(output_path)
    return f"{stem}_{page_number}{ext}"


def generate(template_path, names_csv_path, output_path,
             gap=2.0, margin=0.0, placeholder=DEFAULT_PLACEHOLDER, column=None):
    with open(template_path, encoding="utf-8") as fh:
        svg_text = fh.read()

    start, end = find_labeled_group(svg_text, NAMETAG_LABEL)
    prefix = svg_text[:start]
    suffix = svg_text[end:]
    nametag_xml = svg_text[start:end]

    if placeholder not in nametag_xml:
        raise ValueError(
            f'Placeholder "{placeholder}" not found inside the nametag group. '
            "Check the template or pass --placeholder."
        )

    page_w, page_h, uu_per_mm = parse_page(svg_text)
    tag_w, tag_h, stroke = parse_tag_geometry(nametag_xml)

    # ``gap`` and ``margin`` arrive in millimetres; convert them into the
    # template's user units so spacing is physically correct on any template.
    # If the template declares no absolute size, treat the values as user units.
    scale = uu_per_mm if uu_per_mm else 1.0
    gap_uu = gap * scale
    margin_uu = margin * scale

    cols, rows, pitch_x, pitch_y = compute_grid(
        page_w, page_h, tag_w, tag_h, stroke, gap_uu, margin_uu
    )
    per_page = cols * rows

    names = read_names(names_csv_path, column)
    if not names:
        raise ValueError(f"No names found in {names_csv_path}.")

    total_pages = (len(names) + per_page - 1) // per_page
    written = []
    for page in range(total_pages):
        chunk = names[page * per_page:(page + 1) * per_page]
        copies = []
        for i, name in enumerate(chunk):
            col = i % cols
            row = i // cols
            tx = margin_uu + col * pitch_x
            ty = margin_uu + row * pitch_y
            copies.append(make_tag_copy(nametag_xml, name, i, placeholder, tx, ty))

        out_svg = prefix + "".join(copies) + suffix
        out_name = page_filename(output_path, page + 1)
        with open(out_name, "w", encoding="utf-8") as fh:
            fh.write(out_svg)
        written.append((out_name, len(chunk)))

    # For human-readable reporting only. When the template has no absolute size
    # we report raw user units rather than inches.
    mm_per_uu = (1.0 / uu_per_mm) if uu_per_mm else None
    if mm_per_uu is not None:
        page_size_in = (page_w * mm_per_uu / MM_PER_INCH, page_h * mm_per_uu / MM_PER_INCH)
        tag_size_in = (tag_w * mm_per_uu / MM_PER_INCH, tag_h * mm_per_uu / MM_PER_INCH)
    else:
        page_size_in = None
        tag_size_in = None

    return {
        "page_size_uu": (page_w, page_h),
        "tag_size_uu": (tag_w, tag_h),
        "page_size_in": page_size_in,
        "tag_size_in": tag_size_in,
        "grid": (cols, rows),
        "per_page": per_page,
        "names": len(names),
        "files": written,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Mail-merge names from a CSV onto an SVG nametag template, "
                    "tiled into a Glowforge-ready grid."
    )
    parser.add_argument("--template", default="template.svg", help="Template SVG (default: template.svg)")
    parser.add_argument("--names", default="names.csv", help="CSV of names (default: names.csv)")
    parser.add_argument("--output", default="output.svg", help="Output SVG (default: output.svg)")
    parser.add_argument("--gap", type=float, default=2.0, help="Gap between nametags in mm (default: 2.0)")
    parser.add_argument("--margin", type=float, default=0.0, help="Margin around the grid in mm (default: 0.0)")
    parser.add_argument("--placeholder", default=DEFAULT_PLACEHOLDER,
                        help='Placeholder text to replace (default: "{{NAME}}")')
    parser.add_argument("--column", default=None, help="CSV column name to read names from (default: first column)")
    args = parser.parse_args(argv)

    try:
        result = generate(
            args.template, args.names, args.output,
            gap=args.gap, margin=args.margin,
            placeholder=args.placeholder, column=args.column,
        )
    except (ValueError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    cols, rows = result["grid"]
    if result["page_size_in"] and result["tag_size_in"]:
        pw, ph = result["page_size_in"]
        tw, th = result["tag_size_in"]
        print(f"Bed: {pw:.2f}in x {ph:.2f}in   Tag: {tw:.2f}in x {th:.2f}in")
    else:
        pw, ph = result["page_size_uu"]
        tw, th = result["tag_size_uu"]
        print(f"Bed: {pw:g} x {ph:g} (user units)   Tag: {tw:g} x {th:g} (user units)")
    print(f"Grid: {cols} cols x {rows} rows = {result['per_page']} tags/sheet")
    print(f"Names: {result['names']}  ->  {len(result['files'])} sheet(s)")
    for name, count in result["files"]:
        print(f"  {name}: {count} tag(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
