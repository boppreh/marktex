import re
from subprocess import call, Popen
import os
from glob import glob

rules = [
        # Use # to start sections.
        (r'^#\s?([^#].+?)#?$', r'\\section{\1}'),

        # Use ## to title slides.
        (r'^##\s?(.+?)(?:##)?$((?:\n|.)+?)(?=##|\Z)',
r"""
\\begin{frame}{\1}
\2
\\end{frame}
"""),

        # Begin and end itemize for bullet points.
        (r'((?:^-\s*[^-\n]+\n*){2,})',
r"""
\\begin{itemize}
\1
\\end{itemize}
"""),

        # Add \item to each bullet point.
        (r'^-\s*([^-\n]+)$', lambda m: '\item ' + m.group(1)),

        # Replace single linebreaks with double linebreaks.
        (r'([^\n])\n([^\n])', r'\1\n\n\2'),

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
        src = re.sub(rule, replacement, src, flags=re.MULTILINE)
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

Something else.
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
