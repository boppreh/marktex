import re
from subprocess import call, Popen
import os
from glob import glob

def convert_table(match):
    text = match.group(1)
    # Remove starting |
    text = re.sub(r'(^|\n)\|\s*', r'\1', text)
    # Remove trailing | and replace with \\
    text = re.sub(r'\s*\|(\n|$)', r' \\\\\1', text)
    # Use remaining |'s to align values.
    text = re.sub('\s*\|\s*', ' & ', text)
    lines = text.split('\n')
    headers, alignment, *content = lines
    # Center alignment.
    alignment = re.sub(':-+: ', 'c', alignment)
    # Left alignment.
    alignment = re.sub('-+: ', 'l', alignment)
    # Right alignment.
    alignment = re.sub(':-+ ', 'r', alignment)
    # Remove everything that was left in the alignment string.
    alignment = re.sub('[^lcr ]', '', alignment)
    # Put everything together, remembering to escape curly braces because they
    # are used in Python's format.
    return """
\\begin{{table}}
\\begin{{tabular}}{{{1}}}
\\toprule
{0}
\\midrule
{2}
\\bottomrule
\\end{{tabular}}
\\end{{table}}
""".format(headers, alignment, '\n'.join(content))

rules = [
        # Latex hates unescaped characters.
        (r'([_$])', r'\\\1'),

        # Use # to start sections.
        (r'^#\s?([^#].+?)#?$', r'\\section{\1}\\renewcommand{\\lasttitle}{\1}'),

        # A ## title without body is rendered as a plain frame.
        (r'^##\s?([^\n]+?)(?:\s?##)?$(\s*)(?=##|\Z|!\[#)', r'\\plain{}{\1}\2'),

        # Use ## to title slides.
        (r'^##\s?([^\n]+?)(?:\s?##)?$(.+?)(?=##|\Z|!\[#)',
r"""
\\renewcommand{\\lasttitle}{\1}
\\begin{frame}[fragile]{\\lasttitle}
\2
\\end{frame}
"""),

        # Tables as such:
        #
        # | Header 1 | Header 2 | Header 3 |
        # |---------:|:--------:|:---------|
        # | Value    |   Value  |    Value |
        # | Value    |   Value  |    Value |
        # | Value    |   Value  |    Value |
        (r'(?<=\n\n)((?:^\|.+?\|\n)+)', convert_table),

        # Lines starting with two spaces are interpreted as verbatim code.
        # TODO: remove verbatim code and only reinsert after processing all
        # rules, to avoid replacing something incorrectly.
        (r'((?:^  .+?$\n*)+)',
r"""
\\begin{minted}[fontsize=\small]{latex}
\1
\\end{minted}
"""),

        # Three dots by themselves on a line make a frame pause.
        (r'^\.{3}$', r'\\pause'),

        # A horizontal line indicates a frame break.
        (r'^-+$',
r"""
\\end{frame}
\\begin{frame}[fragile]{\\lasttitle}
"""),

        # Simple images using !(image.jpg) syntax.
        (r'^!\(([^)]+?\.(?:jpg|jpeg|gif|png|bmp|pdf|tif))\)$',
r"""
\\begin{center}
\\includegraphics[width=\\linewidth,height=0.8\\textheight,keepaspectratio]{\1}
\\end{center}
"""),

        # Code embedding with !(code.py) syntax.
        (r'^!\(([^)]+?\.(\w+))\)$',
r"""
\inputminted[fontsize=\small]{\2}{\1}
"""),

        # Captioned images using ![caption](image.jpg) syntax.
        (r'^!\[([^#][^\]]*)\]\(([^)]+?)\)$',
r"""
\\begin{figure}
\\begin{center}
\\includegraphics[width=\\linewidth,height=0.7\\textheight,keepaspectratio]{\2}
\\caption{\1}
\\end{center}
\\end{figure}
"""),

        # Plain slide images using ![#caption](image.jpg) syntax.
        (r'^!\[#\s?([^\]]+)\]\(([^)]+?)\)$',
r"""
\\plain{\1}{\\vspace{-2em}\\begin{center}\\includegraphics[width=\\linewidth,height=0.8\\textheight,keepaspectratio]{\2}\\end{center}}
"""),

        # Annotations using {text}(annotation) syntax.
        # Hackish because we enter math mode needlessly, but I found no other
        # way.
        (r'(?<=\W)\{([^\}]*)\}\(([^)]+?)\)(?=\W)', r'$\\underbrace{\\text{\1}}_{\\text{\2}}$'),
        
        # [Text links](example.org)
        (r'(?<=\W)\[([^\]]*)\]\(([^)]+?)\)(?=\W)', r'\\href{\2}{\\underline{\1}}'),

        # Add \item to each bullet point.
        (r'^- ?([^-\n]+)$', r'\item \1'),

        # Begin and end itemize for bullet points.
        (r'((?:^\\item [^\n]+$(?:\\pause|\n)*){2,})',
r"""
\\begin{itemize}
\1
\\end{itemize}
"""),

        # Replace single linebreaks with double linebreaks.
        (r'([^\n])\n([^\n])', r'\1\n\n\2'),

        # `monospaced`
        (r'(^|\s)`(.+?)`([^\w\d`]|$)', r'\1\\texttt{\2}\3'),

        # *italics*
        (r'(^|\s)\*(.+?)\*([^\w\d*]|$)', r'\1\\textit{\2}\3'),

        # **bold**
        (r'(^|\s)\*\*(.+?)\*\*([^\w\d*]|$)', r'\1\\textbf{\2}\3'),

        # Add header.
        (r'\A',
r"""
\\documentclass[10pt, compress]{beamer}

\\usetheme{m}

\\usepackage{amsmath}
\\usepackage{booktabs}
\\usepackage[scale=2]{ccicons}
\\usepackage{minted}

\\usepackage{hyperref}
\\hypersetup{colorlinks=true,urlcolor=blue}

\\usemintedstyle{trac}

\\newcommand{\\lasttitle}{}

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
    # TODO: tables, command line, non-presentation, more templates, better math
    src = """
# Primeira seção

## Teste literal

Aqui vai um pouco de `código`:

  Testing

`if __name__ == '__main__':`

-

!(../marktex.py)

## Título do slide

- Bullet 1
...
- Bullet 2
...

And now, for *something* **else**.

## Segundo slide

Aqui tem mais {coisa}(anotação).
-
[E mais um slide](example.org).

## Ibagens

!(images/moodle.png)

## Ibagens Legendárias

![Exemplo de figura.](images/moodle.png)


![#Frame especial para figura](images/moodle.png)

## Questions?

## Tableas!

| Tables        | Are           | Cool  |
|:-------------:|--------------:|:------|
| col 3 is      |    r-l        | $1600 |
| col 2 is      | centered      |   $12 |
| zebra stripes | are neat      |    $1 |
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
