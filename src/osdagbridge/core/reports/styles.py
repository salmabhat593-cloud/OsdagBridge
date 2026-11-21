"""
OsdagBridge - Centralized Formatting & Style System (styles.py)
Single source of truth for LaTeX document layout, table formatting, 
color palettes, headers/footers, and visualization styling.
"""

# ==============================================================================
# 1. COLOR PALETTE (Hex for Matplotlib & RGB for LaTeX)
# ==============================================================================
COLOR_PALETTE = {
    "primary": "#2E7D32",       # Deep Forest Green (Osdag Theme)
    "secondary": "#1B5E20",     # Darker Green
    "accent": "#8BC34A",        # Light Green
    "table_head_bg": "#E8F5E9", # Soft Green Tint for Table Headers
    "table_row_alt": "#F9FBF9", # Alternating Row Background
    "border": "#BDBDBD",        # Subtle Gray Border
    "text_dark": "#212121",     # Primary Text
    "pass": "#2E7D32",          # Green for Passing Checks (UR <= 1.0)
    "fail": "#D32F2F",          # Red for Failing Checks (UR > 1.0)
    "threshold": "#C62828",     # Red for UR=1.0 Reference Line
    "steel": "#455A64",         # Blue-Grey for Structural Steel
    "concrete": "#78909C",      # Grey for Concrete
    "rebar": "#E65100",         # Amber/Orange for Reinforcement Rebar
}

# LaTeX \definecolor statements to be injected into Document Preamble
LATEX_COLORS_PREAMBLE = r"""
\definecolor{OsdagPrimary}{HTML}{2E7D32}
\definecolor{OsdagSecondary}{HTML}{1B5E20}
\definecolor{OsdagAccent}{HTML}{8BC34A}
\definecolor{TableHeadBg}{HTML}{E8F5E9}
\definecolor{TableRowAlt}{HTML}{F9FBF9}
\definecolor{TableBorder}{HTML}{BDBDBD}
\definecolor{PassColor}{HTML}{2E7D32}
\definecolor{FailColor}{HTML}{D32F2F}
"""

# ==============================================================================
# 2. DOCUMENT GEOMETRY & VERTICAL SPACING (Fixes Footer Overlap & Margin Bleed)
# ==============================================================================
DOCUMENT_GEOMETRY_PREAMBLE = r"""
\usepackage[
    a4paper,
    top=2.5cm,
    bottom=3.0cm,
    left=2.3cm,
    right=2.3cm,
    headheight=26pt,
    headsep=16pt,
    footskip=32pt
]{geometry}
\usepackage{needspace}
\usepackage{colortbl}
"""

# ==============================================================================
# 3. TYPOGRAPHY & TABLE SPACING RULES
# ==============================================================================
TABLE_FORMATTING_PREAMBLE = r"""
% Row padding and standard arraystretch
\renewcommand{\arraystretch}{1.25}
\setlength{\extrarowheight}{2pt}

% Column alignment types with explicit paragraph wrapping
\newcolumntype{L}[1]{>{\raggedright\arraybackslash}p{#1}}
\newcolumntype{C}[1]{>{\centering\arraybackslash}p{#1}}
\newcolumntype{R}[1]{>{\raggedleft\arraybackslash}p{#1}}
"""

# ==============================================================================
# 4. HEADER & FOOTER THEME (fancyhdr)
# ==============================================================================
HEADER_FOOTER_PREAMBLE = r"""
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small\textcolor{gray}{\textbf{OsdagBridge} | Design \& Analysis Report}}
\fancyhead[R]{\small\textcolor{gray}{\leftmark}}
\fancyfoot[L]{\footnotesize\textcolor{gray}{Osdag -- IIT Bombay / FOSSEE}}
\fancyfoot[C]{\thepage}
\fancyfoot[R]{\footnotesize\textcolor{gray}{Confidential}}
\renewcommand{\headrulewidth}{0.4pt}
\renewcommand{\footrulewidth}{0.4pt}
\renewcommand{\headrule}{\hbox to\headwidth{\color{TableBorder}\leaders\hrule height \headrulewidth\hfill}}
\renewcommand{\footrule}{\hbox to\headwidth{\color{TableBorder}\leaders\hrule height \footrulewidth\hfill}}
"""

# ==============================================================================
# 5. MASTER REPEATED-HEADER LONGTABLE GENERATOR (Fixes Missing Headers on Page Breaks)
# ==============================================================================
def make_longtable(col_spec: str, caption: str, headers: list, rows: list, label: str = None) -> str:
    """
    Builds a robust LaTeX LongTable that:
    1. Uses \endfirsthead on the first page.
    2. Repeats the column header row on every page transition using \endhead.
    3. Shows a subtle 'Continued on next page' using \endfoot.
    4. Completes with \endlastfoot.
    """
    header_tex = " & ".join([r"\textbf{" + str(h) + "}" for h in headers]) + r" \\"
    col_count = len(headers)
    label_tex = f"\\label{{{label}}}\n" if label else ""

    tex = [
        r"\vspace{0.8em}",
        rf"\begin{{longtable}}{{{col_spec}}}",
        rf"\caption{{\textbf{{{caption}}}}}{label_tex}",
        r"\hline",
        r"\rowcolor{TableHeadBg}",
        header_tex,
        r"\hline",
        r"\endfirsthead",
        "",
        rf"\multicolumn{{{col_count}}}{{c}}{{\small\textit{{Table \dots\ continued from previous page}}}} \\",
        r"\hline",
        r"\rowcolor{TableHeadBg}",
        header_tex,
        r"\hline",
        r"\endhead",
        "",
        r"\hline",
        rf"\multicolumn{{{col_count}}}{{r}}{{\footnotesize\textit{{Continued on next page\dots}}}} \\",
        r"\endfoot",
        "",
        r"\hline",
        r"\endlastfoot",
        "",
    ]

    for row in rows:
        if isinstance(row, (list, tuple)):
            row_str = " & ".join([str(c) for c in row]) + r" \\"
            tex.append(row_str)
            tex.append(r"\hline")
        elif isinstance(row, str):
            tex.append(row)

    tex.append(r"\end{longtable}")
    tex.append(r"\vspace{0.5em}")
    return "\n".join(tex)