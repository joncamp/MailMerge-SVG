# Nametag Generator

This Python application generates nametags from an SVG template and arranges them in a grid for laser cutting.

## Requirements

- Python 3.7 or higher
- Required packages (install using `pip install -r requirements.txt`):
  - svgwrite
  - pandas
  - lxml

## Usage

1. Prepare your files:
   - Create an SVG template file with `<<NAME>>` as the placeholder for names
   - Create a CSV file with names in the first column

2. Run the application:
   ```bash
   python nametag_generator.py
   ```

3. The application will:
   - Read the template SVG file
   - Replace `<<NAME>>` with names from the CSV file
   - Arrange the nametags in a grid
   - Save the result as a new SVG file

## File Structure

- `template.svg`: Your SVG template file with `{{NAME}}` placeholder
- `names.csv`: CSV file containing names (one per row)
- `output.svg`: Generated SVG file with arranged nametags

## Example

1. Create a template.svg file:
```svg
<svg width="100" height="50" viewBox="0 0 100 50">
  <rect width="100" height="50" fill="white" stroke="black"/>
  <text x="50" y="25" text-anchor="middle" dominant-baseline="middle">{{NAME}}</text>
</svg>
```

2. Create a names.csv file:
```csv
Name
John Doe
Jane Smith
Bob Johnson
```

3. Run the application to generate the output.svg file with arranged nametags. 