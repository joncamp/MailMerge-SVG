import os
import copy
import pandas as pd
import xml.etree.ElementTree as ET

class NametagGenerator:
    def __init__(self, template_svg_path, output_svg_path):
        self.template_svg_path = template_svg_path
        self.output_svg_path = output_svg_path
        
        # Register namespaces
        ET.register_namespace('', "http://www.w3.org/2000/svg")
        ET.register_namespace('inkscape', "http://www.inkscape.org/namespaces/inkscape")
        ET.register_namespace('sodipodi', "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd")


    def generate_from_example_layout(self, names_csv_path):
        """Fill all names in a single long SVG, stacking nametags vertically with 0.25 in spacing."""
        # Load names
        df = pd.read_csv(names_csv_path)
        names = [str(v) for v in df.iloc[:, 0].tolist()]

        # Load base SVG (example.svg)
        tree = ET.parse(self.template_svg_path)
        root = tree.getroot()

        ns = {
            'svg': 'http://www.w3.org/2000/svg',
            'inkscape': 'http://www.inkscape.org/namespaces/inkscape',
        }

        # Collect all existing Nametag groups and keep the first as prototype
        all_groups = root.findall('.//svg:g[@inkscape:label="Nametag"]', ns)
        if not all_groups:
            tree.write(self.output_svg_path, encoding='utf-8', xml_declaration=True)
            return

        prototype = copy.deepcopy(all_groups[0])

        # Try to read the base translate Y from the prototype's transform (matrix or translate)
        base_transform = prototype.get('transform', '')
        base_ty = 0.0
        try:
            if 'matrix' in base_transform:
                vals = base_transform.strip().split('matrix(')[1].rstrip(')').split(',')
                if len(vals) == 6:
                    base_ty = float(vals[5])
            elif 'translate' in base_transform:
                vals = base_transform.strip().split('translate(')[1].rstrip(')').split(',')
                if len(vals) >= 2:
                    base_ty = float(vals[1])
        except Exception:
            base_ty = 0.0

        # Find a parent container to which we will append new stacks
        append_parent = None
        # Remove all existing Nametag groups and remember the first parent
        for g in root.iter('{http://www.w3.org/2000/svg}g'):
            children = list(g)
            for child in children:
                if child.tag == '{http://www.w3.org/2000/svg}g' and child.get('{http://www.inkscape.org/namespaces/inkscape}label') == 'Nametag':
                    if append_parent is None:
                        append_parent = g
                    g.remove(child)

        if append_parent is None:
            # Fallback: append to root
            append_parent = root

        # Derive nametag height from the template prototype, and use 0.25 in spacing
        spacing_mm = 25.4 * 0.25  # 0.25 inch in mm
        nametag_height_mm = None
        # Prefer a labeled border rect inside the prototype
        border_rect = prototype.find('.//svg:rect[@inkscape:label="Nametag Border"]', ns)
        if border_rect is not None and border_rect.get('height'):
            try:
                nametag_height_mm = float(border_rect.get('height'))
            except Exception:
                nametag_height_mm = None
        # Fallback: attempt to read the first rect height inside the prototype
        if nametag_height_mm is None:
            any_rect = prototype.find('.//svg:rect', ns)
            if any_rect is not None and any_rect.get('height'):
                try:
                    nametag_height_mm = float(any_rect.get('height'))
                except Exception:
                    nametag_height_mm = None
        # Final fallback: estimate using distance between first two original groups if available
        if nametag_height_mm is None:
            # Try to get delta Y from two Nametag groups' transforms (before removal)
            pass  # No safe estimate; will default below
        # If all else fails, default to one inch minus spacing so step remains 25.4mm
        if nametag_height_mm is None:
            nametag_height_mm = 25.4 - spacing_mm
        step_mm = nametag_height_mm + spacing_mm

        # Build stacked clones (skip empty names)
        for idx, name in enumerate(names):
            if not str(name).strip():
                continue
            # Set name on a fresh clone of the prototype
            clone = copy.deepcopy(prototype)
            tspan = clone.find('.//svg:tspan', ns)
            if tspan is not None:
                tspan.text = name

            # Compose transform directly on the clone to avoid extra wrapper group
            dy = idx * step_mm
            existing_transform = clone.get('transform', '')
            translate = f'translate(0,{dy})'
            if existing_transform:
                clone.set('transform', f"{existing_transform} {translate}")
            else:
                clone.set('transform', translate)

            append_parent.append(clone)

        # Expand document height to fit all tags
        if names:
            original_height_attr = root.get('height', '')
            view_box = root.get('viewBox', '')
            # Compute needed mm height: base_ty + last offset + tag height + small margin
            total_height_mm = base_ty + (len(names) - 1) * step_mm + nametag_height_mm + 0.5
            # Update height in inches if attribute uses inches
            root.set('height', f"{total_height_mm / 25.4}in")
            # Update viewBox height if present
            if view_box:
                parts = view_box.split()
                if len(parts) == 4:
                    parts[3] = str(total_height_mm)
                    root.set('viewBox', ' '.join(parts))

        tree.write(self.output_svg_path, encoding='utf-8', xml_declaration=True)


def main():
    # Use template.svg as the baseline; write to output.svg
    base_path = "template.svg"
    output_path = "output.svg"
    names_path = "names.csv"

    generator = NametagGenerator(base_path, output_path)
    # Directly fill names into existing Nametag groups
    generator.generate_from_example_layout(names_path)

if __name__ == "__main__":
    main() 