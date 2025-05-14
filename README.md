# Code Map Viewer

A simple command‑line tool that analyzes a Python source file, extracts classes, functions, and call relationships via the AST, and generates an interactive HTML visualization with PyVis.

---

## Features

* Parses any Python `.py` file and identifies:

  * **Classes** and their methods
  * **Global** functions
  * **Function call** relationships (caller → callee)
* Produces a clean, hierarchical graph in `function_graph.html`:

  * **Class nodes** as dark boxes
  * **Function nodes** as light boxes
  * **Global** group as a purple circle
  * **Call edges** with arrows
* Customizable CSS for colors, layout, and legend
* No external (paid) APIs required

---

## Requirements

* Python 3.10 or later
* `pyvis` library

Install dependencies with:

```bash
pip install pyvis
```

---

## Usage

Run the script from the command line, passing the target Python file as an argument:

```bash
python main.py sample_code.py
```

* **Input**: `sample_code.py` (or any `.py` file)
* **Output**: `function_graph.html` in the same directory

Open `function_graph.html` in your browser to explore the interactive graph.

---

## Customization

* **CSS & Layout**: Edit the `CSS_CODE` block in `main.py` to adjust colors, fonts, dimensions, or legend styles.
* **Graph Options**: Modify the `net.set_options(...)` call to tweak the PyVis layout or physics settings.
* **Node Styles**: Change `CLASS_NODE_STYLE`, `FUNC_NODE_STYLE`, and `GLOBAL_NODE_STYLE` for different shapes or sizes.

---

## Example

After running:

```bash
python main.py my_module.py
```

You will see a page like this:

Click on any node to highlight its connections.

---

## License

MIT © Tal Frankenthal


