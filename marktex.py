import re
from subprocess import call
import os

rules = {
        r'\A':
r"""
\\documentclass[10pt, compress]{beamer}

\\usetheme{m}

\\usepackage{booktabs}
\\usepackage[scale=2]{ccicons}
\\usepackage{minted}

\\usemintedstyle{trac}

\\begin{document}
""",

        r'\Z':
r"""
\\end{document}
""",

        r'^#\s?(.+?)#?$': r'\\section{\1}',

}

def apply_rules(rules, src):
    for rule, replacement in rules.items():
        src = re.sub(rule, replacement, src, flags=re.MULTILINE)
    return src

XELATEX_LOCATION = r"C:\Program Files\MiKTeX 2.9\miktex\bin\x64\miktex-xetex.exe"

def generate_pdf(tex_src):
    os.chdir(os.path.join(os.path.dirname(__file__), 'resources'))
    tex_location = 'demo.tex'
    with open(tex_location, 'w', encoding='utf-8') as file:
        file.write(tex_src)
    call([XELATEX_LOCATION, '-undump=xelatex', '-shell-escape', tex_location])
    call([XELATEX_LOCATION, '-undump=xelatex', '-shell-escape', tex_location])
    for temp_file in glob('demo.*'):
        if temp_file != 'demo.pdf':
            os.remove(temp_file)
    return os.path.abspath('demo.pdf')

if __name__ == '__main__':
    src = """
# Primeira seção
"""
    tex_src = apply_rules(rules, src)
    print(tex_src)
    os.system('start "{}"'.format(generate_pdf(tex_src)))
    exit()
    from sys import argv
    if len(argv) <= 1:
        pass
    elif len(argv) == 2:
        pass
    elif len(argv) == 3:
        pass
