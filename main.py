import ast
from pyvis.network import Network
from collections import defaultdict
from pathlib import Path
import json
import sys

# === Get Python file path from command line ===
if len(sys.argv) < 2:
    print("Usage: python main.py <python_file.py>")
    sys.exit(1)
file_path = sys.argv[1]

# === AST Analysis Code ===
code = Path(file_path).read_text(encoding="utf-8")
tree = ast.parse(code)

function_names = []
function_line_no = {}
calls = []

class_names = []
class_line_no = {}
class_func_map = {}

class Analyzer(ast.NodeVisitor):
    def __init__(self):
        self.class_stack = []
        self.function_names = []
        self.class_func_map = {}
        self.calls = []
        self.super_calls = []
        self.function_line_no = {}

    def visit_ClassDef(self, node):
        class_name = node.name
        self.class_stack.append(class_name)
        self.class_func_map[class_name] = []
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_FunctionDef(self, node):
        if self.class_stack:
            full_name = f"{self.class_stack[-1]}.{node.name}"
            self.class_func_map[self.class_stack[-1]].append(full_name)
        else:
            full_name = node.name

        if full_name not in self.function_names:
            self.function_names.append(full_name)
            self.function_line_no[full_name] = node.lineno

        self.current_function = full_name
        self.generic_visit(node)
        self.current_function = None

    def visit_Call(self, node):
        if not hasattr(self, "current_function") or self.current_function is None:
            return

        if isinstance(node.func, ast.Name):
            callee = node.func.id
        elif isinstance(node.func, ast.Attribute):
            if (
                isinstance(node.func.value, ast.Call)
                and isinstance(node.func.value.func, ast.Name)
                and node.func.value.func.id == "super"
            ):
                callee = node.func.attr
                self.calls.append((self.current_function, callee))
                self.super_calls.append((self.current_function, callee))
                return
            else:
                callee = node.func.attr
        else:
            return

        self.calls.append((self.current_function, callee))
        self.generic_visit(node)
# Run the visitors
analyzer = Analyzer()
analyzer.visit(tree)

function_names = analyzer.function_names
class_func_map = analyzer.class_func_map
function_line_no = analyzer.function_line_no
calls = analyzer.calls
super_calls = analyzer.super_calls


# Filter out self-calls and calls to non-existing functions
filtered_calls = []
for caller, callee in calls:
    if caller == callee:
        continue
    for fn in function_names:
        if fn.endswith(f".{callee}") or fn == callee:
            filtered_calls.append((caller, fn))
            break


# === Build the graph with Pyvis ===
net = Network(height="600px", width="900px", directed=True, bgcolor="#ffffff")

# --- Color styles ---
CLASS_NODE_STYLE = dict(
    shape="box",
    widthConstraint={"minimum": 120},
    heightConstraint={"minimum": 50},
    margin={"top":14, "right":10, "bottom":14, "left":10},
    color={
        "background": "#1e3a5c",
        "border": "#0a1a2f",
        "highlight": {"background": "#fff8c6", "border": "#e60000"}
    },
    font={"face": "arial", "size": 20, "color": "#fff", "align": "center"}
)
FUNC_NODE_STYLE = dict(
    shape="box",
    widthConstraint={"minimum": 110},
    heightConstraint={"minimum": 45},
    margin={"top":12, "right":8, "bottom":12, "left":8},
    color={
        "background": "#d0eaff",
        "border": "#333333",
        "highlight": {"background": "#fff8c6", "border": "#e60000"}
    },
    font={"face": "arial", "size": 18, "align": "center"}
)
GLOBAL_NODE_STYLE = dict(
    shape="ellipse",
    widthConstraint={"minimum": 120},
    heightConstraint={"minimum": 50},
    color={
        "background": "#6e44ff",
        "border": "#2d186c",
        "highlight": {"background": "#fff8c6", "border": "#e60000"}
    },
    font={"face": "arial", "size": 20, "color": "#fff", "align": "center"}
)

# Add nodes for classes
for cls in class_func_map.keys():
    net.add_node(
        n_id=f"class::{cls}",
        label=cls,
        title=f"Class: {cls}",
        **CLASS_NODE_STYLE
    )

# Add a node for global functions (not inside a class)
if any(fn not in [f for fs in class_func_map.values() for f in fs] for fn in function_names):
    net.add_node(
        n_id="global::Global",
        label="Global",
        title="Global Functions",
        **GLOBAL_NODE_STYLE
    )

# Add nodes for functions, with edges from class/global
for fn in function_names:
    parent_cls = None
    for cls, funcs in class_func_map.items():
        if fn in funcs:
            parent_cls = cls
            break
    title = f"{fn} (Class: {parent_cls})" if parent_cls else f"{fn} (Global)"
    net.add_node(n_id=fn, label=fn, title=title, **FUNC_NODE_STYLE)
    if parent_cls:
        net.add_edge(f"class::{parent_cls}", fn, color="#1e3a5c", arrows="to", width=2)
    else:
        net.add_edge("global::Global", fn, color="#6e44ff", arrows="to", width=2)

# Edges for function calls
for caller, callee in filtered_calls:
    if (caller, callee.split(".")[-1]) in super_calls:
        net.add_edge(caller, callee, color="#0077ff", arrows="to", width=2, dashes=True)
    else:
        net.add_edge(caller, callee, color="gray", arrows="to", width=1)


# Layout options (hierarchical)
net.set_options("""
{
  "layout": {
    "hierarchical": {
      "direction": "UD",
      "sortMethod": "directed",
      "levelSeparation": 120,
      "nodeSpacing": 180
    }
  },
  "physics": {"enabled": false},
  "interaction": {"hover": true, "selectConnectedEdges": false},
  "autoResize": true
}
""")

# Create initial HTML file
HTML_PATH = "function_graph.html"
net.write_html(HTML_PATH)
html = Path(HTML_PATH).read_text(encoding="utf-8")

# === CSS and Legend ===
CSS_CODE = '''
<style>
body {
  margin: 0;
  min-height: 100vh;
  background: linear-gradient(120deg, #e0e7ff 0%, #f4f8fb 100%);
  font-family: 'Inter', 'Rubik', 'Open Sans', Arial, sans-serif;
}
.header {
  width: 100vw;
  background: linear-gradient(90deg, #007cf0 0%, #00dfd8 100%);
  color: #fff;
  padding: 32px 0 24px 0;
  text-align: center;
  font-size: 2.5rem;
  font-weight: 800;
  letter-spacing: 2px;
  box-shadow: 0 2px 16px rgba(0,0,0,0.10);
  border-bottom-left-radius: 32px;
  border-bottom-right-radius: 32px;
}
#main-graph-container {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  min-height: 80vh;
  margin-top: 48px;
}
#graph-div {
  width: 1200px;
  height: 700px;
  background: #fff;
  border-radius: 24px;
  box-shadow: 0 8px 40px rgba(0,0,0,0.13);
  padding: 24px;
  display: flex;
  justify-content: center;
  align-items: center;
  transition: box-shadow 0.2s;
}
#graph-div > iframe, #graph-div > div {
  width: 100% !important;
  height: 100% !important;
  min-height: 500px;
  min-width: 700px;
  border: none;
  background: transparent;
}
#legend {
  position: fixed;
  top: 32px;
  right: 40px;
  z-index: 9999;
  background: #fff;
  border: 2px solid #007cf0;
  border-radius: 14px;
  padding: 18px 28px;
  box-shadow: 0 2px 16px rgba(0,0,0,0.10);
  font-family: 'Inter', Arial, sans-serif;
  min-width: 200px;
  opacity: 0.97;
}
#legend .legend-title {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 10px;
  color: #007cf0;
}
#legend .legend-row {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}
#legend .legend-icon {
  width: 30px; height: 30px;
  margin-right: 12px;
  display: inline-block;
}
#legend .legend-class {
  background: #1e3a5c; border: 2px solid #0a1a2f; border-radius: 7px;
}
#legend .legend-func {
  background: #d0eaff; border: 2px solid #333; border-radius: 7px;
}
#legend .legend-global {
  background: #6e44ff; border: 2px solid #2d186c; border-radius: 50%;
}
@media (max-width: 1300px) {
  #graph-div { width: 98vw; height: 60vw; min-width: 300px; min-height: 200px; }
  #legend { right: 10px; top: 10px; padding: 10px 12px; min-width: 120px; }
}
</style>
<link href="https://fonts.googleapis.com/css?family=Inter:400,500,700&display=swap" rel="stylesheet">
'''

LEGEND_HTML = '''
<div id="legend">
  <div class="legend-title">Nodes</div>
  <div class="legend-row">
    <span class="legend-icon legend-class"></span>
    <span>Class (dark square)</span>
  </div>
  <div class="legend-row">
    <span class="legend-icon legend-func"></span>
    <span>Function (light square)</span>
  </div>
  <div class="legend-row">
    <span class="legend-icon legend-global"></span>
    <span>Global (purple circle)</span>
  </div>
  <hr style="margin: 12px 0;">
  <div class="legend-title">Edges</div>
  <div class="legend-row">
    <svg width="30" height="12" style="margin-right:12px"><line x1="0" y1="6" x2="30" y2="6" stroke="#1e3a5c" stroke-width="3"/></svg>
    <span>Class → Function (Belongs to)</span>
  </div>
  <div class="legend-row">
    <svg width="30" height="12" style="margin-right:12px"><line x1="0" y1="6" x2="30" y2="6" stroke="gray" stroke-width="1"/></svg>
    <span>Function → Function (Call)</span>
  </div>
  <div class="legend-row">
    <svg width="30" height="12" style="margin-right:12px"><line x1="0" y1="6" x2="30" y2="6" stroke="#0077ff" stroke-width="2" stroke-dasharray="5,4"/></svg>
    <span>super() Call</span>
  </div>
  <div class="legend-row">
    <svg width="30" height="12" style="margin-right:12px"><line x1="0" y1="6" x2="30" y2="6" stroke="#6e44ff" stroke-width="2"/></svg>
    <span>Global → Function</span>
  </div>
</div>
'''

# Inject CSS into <head>
html = html.replace('</head>', CSS_CODE + '</head>', 1)

# Wrap the graph and inject the legend before <div id="mynetwork">
html = html.replace(
    '<div id="mynetwork"',
    LEGEND_HTML + '\n<div id="main-graph-container">\n  <div id="graph-div">\n    <div id="mynetwork"',
    1
)

# Close containers after the Pyvis script
html = html.replace(
    '</script>',
    '</script>\n  </div>\n</div>',
    1
)

# Final save
Path(HTML_PATH).write_text(html, encoding="utf-8")
print("HTML updated and saved – open function_graph.html now")
