#!/usr/bin/env python3
"""Converts manual.md into a beautifully styled HTML file ready for PDF export."""
import markdown
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(SCRIPT_DIR, "manual.md")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "manual.html")

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    md_content = f.read()

# Convert Markdown → HTML with extensions
html_body = markdown.markdown(
    md_content,
    extensions=[
        "tables",
        "fenced_code",
        "codehilite",
        "toc",
        "md_in_html",
    ],
    extension_configs={
        "codehilite": {"css_class": "highlight", "guess_lang": False},
        "toc": {"permalink": False},
    },
)

# Premium dark-themed CSS matching GitHub style
css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg-primary: #ffffff;
    --bg-secondary: #f6f8fa;
    --bg-tertiary: #eef1f5;
    --text-primary: #1f2328;
    --text-secondary: #57606a;
    --text-link: #0969da;
    --border: #d0d7de;
    --accent-green: #1a7f37;
    --accent-red: #cf222e;
    --accent-purple: #6639ba;
    --accent-orange: #9a6700;
    --accent-blue: #0550ae;
    --code-bg: #f6f8fa;
}

@media print {
    body { padding: 0 !important; }
    .page-break { page-break-after: always; }
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.75;
    font-size: 15px;
    max-width: 900px;
    margin: 0 auto;
    padding: 40px 32px;
}

h1 {
    font-size: 2em;
    font-weight: 700;
    margin-top: 48px;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 2px solid var(--border);
    letter-spacing: -0.02em;
    color: var(--text-primary);
}

h1:first-child { margin-top: 0; }

h2 {
    font-size: 1.5em;
    font-weight: 600;
    margin-top: 40px;
    margin-bottom: 12px;
    color: var(--text-primary);
}

h3 {
    font-size: 1.2em;
    font-weight: 600;
    margin-top: 32px;
    margin-bottom: 8px;
    color: var(--accent-purple);
}

h4 {
    font-size: 1em;
    font-weight: 600;
    margin-top: 24px;
    margin-bottom: 8px;
    color: var(--accent-blue);
}

p { margin-bottom: 16px; }

a { color: var(--text-link); text-decoration: none; }
a:hover { text-decoration: underline; }

strong { font-weight: 600; color: var(--text-primary); }

code {
    font-family: 'JetBrains Mono', 'SF Mono', 'Fira Code', monospace;
    font-size: 0.88em;
    background: var(--bg-tertiary);
    padding: 2px 6px;
    border-radius: 4px;
    color: var(--accent-purple);
}

pre {
    background: var(--code-bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px 20px;
    margin: 16px 0;
    overflow-x: auto;
    line-height: 1.5;
}

pre code {
    background: none;
    padding: 0;
    color: var(--text-primary);
    font-size: 0.85em;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0;
    font-size: 0.9em;
}

th {
    background: var(--bg-tertiary);
    color: var(--text-primary);
    font-weight: 600;
    text-align: left;
    padding: 10px 14px;
    border: 1px solid var(--border);
}

td {
    padding: 10px 14px;
    border: 1px solid var(--border);
    color: var(--text-secondary);
}

tr:nth-child(even) { background: var(--bg-secondary); }

blockquote {
    border-left: 4px solid var(--accent-blue);
    margin: 16px 0;
    padding: 12px 20px;
    background: var(--bg-secondary);
    border-radius: 0 8px 8px 0;
    color: var(--text-secondary);
    font-style: italic;
}

blockquote strong { color: var(--accent-blue); }

hr {
    border: none;
    border-top: 1px solid var(--border);
    margin: 48px 0;
}

ul, ol {
    margin: 12px 0;
    padding-left: 24px;
}

li { margin-bottom: 6px; }

img {
    max-width: 100%;
    border-radius: 8px;
    margin: 16px 0;
}

/* Diff-style highlights */
pre code .gi, .highlight .gi { color: var(--accent-green); }
pre code .gd, .highlight .gd { color: var(--accent-red); }

/* Emoji styling */
.emoji { font-size: 1.1em; }
"""

html_document = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GraphCortex — Complete Study Manual</title>
    <style>{css}</style>
</head>
<body>
{html_body}
</body>
</html>
"""

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(html_document)

print(f"[✓] HTML manual generated: {OUTPUT_FILE}")
print(f"    Open in browser and use Cmd+P → Save as PDF")
