import re

from generic import translate as translate_generic

rules = [
        (r'\A\s*([^#]+)',
r"""
\\begin{frame}{}
\1
\\end{frame}
"""),

        # A ## title without body is rendered as a plain frame.
        (r'^##\s?([^\n]+?)(?:\s?##)?$(\s*)(?=##|!\[#|\Z)', r'\\plain{}{\1}\2'),

        # Use ## to title slides.
        (r'^##\s?([^\n]+?)(?:\s?##)?$(.+?)(?=^#|\Z|^!\[#|^\\plain)',
r"""
\\renewcommand{\\lasttitle}{\1}
\\begin{frame}[fragile]{\\lasttitle}
\2
\\end{frame}
"""),

        # Use # to start sections.
        (r'^#\s?([^#].+?)#?$', r'\\section{\1}\\renewcommand{\\lasttitle}{\1}'),


        # Three dots by themselves on a line make a frame pause.
        (r'^\.{3}$', r'\\pause'),

        # A horizontal line indicates a frame break.
        (r'^-+$',
r"""
\\end{frame}
\\begin{frame}[fragile]{\\lasttitle}
"""),
]

def translate(src):
    # If the user uses section titles, but not slide titles, the slides will
    # look weird. So it's best if we use the section slides as slide titles.
    if not re.search(r'^## ', src, flags=re.MULTILINE):
        src = re.sub(r'^#', r'##', src, flags=re.MULTILINE)
        pass

    header = r"""
\usetheme{m}

\usepackage{amsmath}
\usepackage{booktabs}
\usepackage{listings}

\usepackage{hyperref}
\hypersetup{colorlinks=true,urlcolor=blue}

\newcommand{\lasttitle}{}

\begin{document}
"""

    footer = r'\end{document}'

    result = translate_generic(rules, src, header, footer)
    if 'minted' in result:
        result = r"""\usepackage{minted}
\usemintedstyle{trac}
""" + result
    return r'\documentclass[10pt, compress]{beamer}' + result
