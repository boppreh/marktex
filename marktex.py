import re
from subprocess import call, Popen
import os
from glob import glob

rules = [
        # Use # to start sections.
        (r'^#\s?([^#].+?)#?$', r'\\section{\1}'),

        # Use ## to title slides.
        (r'^##\s?(.+?)(?:##)?$(.+?)(?=##|\Z)',
r"""
\\begin{frame}{\1}
\2
\\end{frame}
"""),

        # Horizontal lines denote frame breaks.
        # Unfortunately mtheme does not support this, exploding in a "capacity
        # exceeded" error.
        # (r'^-+$', r'\\framebreak'),

        # Three dots by themselves on a line make a frame pause.
        (r'^...$', r'\\pause'),

        # Add \item to each bullet point.
        (r'^- ?([^-\n]+)$', r'\item \1'),

        # Begin and end itemize for bullet points.
        (r'((?:^\\item [^\n]+$\n*){2,})',
r"""
\\begin{itemize}
\1
\\end{itemize}
"""),

        # Replace single linebreaks with double linebreaks.
        (r'([^\n])\n([^\n])', r'\1\n\n\2'),

        # *italics*
        (r'(^|\s)\*(.+?)\*([^\w\d*]|$)', r'\1\\textit{\2}\3'),

        # **bold**
        (r'(^|\s)\*\*(.+?)\*\*([^\w\d*]|$)', r'\1\\textbf{\2}\3'),

        # Add header.
        (r'\A',
r"""
\\documentclass[10pt, compress]{beamer}

\\usetheme{m}

\\usepackage{booktabs}
\\usepackage[scale=2]{ccicons}
\\usepackage{minted}

\\usemintedstyle{trac}

\\begin{document}
"""),

        # Add footer.
        (r'\Z', r'\\end{document}'),
]

def apply_rules(rules, src):
    for rule, replacement in rules:
        src = re.sub(rule, replacement, src, flags=re.MULTILINE | re.DOTALL)
    return src

XELATEX_LOCATION = r"C:\Program Files\MiKTeX 2.9\miktex\bin\x64\miktex-xetex.exe"

def generate_pdf(tex_src):
    os.chdir(os.path.join(os.path.dirname(__file__), 'resources'))
    tex_location = 'demo.tex'
    with open(tex_location, 'w', encoding='utf-8') as file:
        file.write(tex_src)
    call([XELATEX_LOCATION, '-undump=xelatex', '-shell-escape', tex_location])
    for temp_file in glob('demo.*'):
        if temp_file != 'demo.pdf':
            os.remove(temp_file)
    return os.path.abspath('demo.pdf')

if __name__ == '__main__':
    src = """
# Primeira seção

## Título do slide

- Bullet 1
- Bullet 2

And now, for *something* **else**.

## Segundo slide

Aqui tem mais coisa.
...
E mais um slide.
"""
    tex_src = apply_rules(rules, src)
    print(tex_src)
    Popen(['start', generate_pdf(tex_src)], shell=True)
    exit()
    from sys import argv
    if len(argv) <= 1:
        pass
    elif len(argv) == 2:
        pass
    elif len(argv) == 3:
        pass
