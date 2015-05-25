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
    # Right alignment.
    alignment = re.sub(':-+ ', 'r', alignment)
    # Left alignment.
    alignment = re.sub('-+:? ', 'l', alignment)
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

        # A ## title without body is rendered as a plain frame.
        (r'^##\s?([^\n]+?)(?:\s?##)?$(\s*)(?=##|\Z|!\[#)', r'\\plain{}{\1}\2'),

        # Latex hates unescaped characters.
        (r'([$#%])', r'\\\1'),

        # Annotations using {text}(annotation) syntax.
        # Hackish because we enter math mode needlessly, but I found no other
        # way.
        (r'\{([^\n]+?)\}\(([^\n]+?)\)', r'$\\underbrace{\\text{\1}}_{\\text{\2}}$'),


        # Tables as such:
        #
        # | Header 1 | Header 2 | Header 3 |
        # |---------:|:--------:|:---------|
        # | Value    |   Value  |    Value |
        # | Value    |   Value  |    Value |
        # | Value    |   Value  |    Value |
        (r'(?<=\n\n)((?:^\|.+?\|\n)+)', convert_table),

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
\inputminted[fontsize=\small]{latex}{\1}
"""),

        # Captioned images using ![caption](image.jpg) syntax.
        (r'^!\[([^\]]+?)\]\(([^)]+?)\)$',
r"""
\\begin{figure}
\\begin{center}
\\includegraphics[width=\\linewidth,height=0.7\\textheight,keepaspectratio]{\2}
\\caption{\1}
\\end{center}
\\end{figure}
"""),
        
        # [Text links](example.org)
        (r'(?<=\W)\[([^\]]*)\]\(([^)]+?)\)(?=\W)', r'\\href{\2}{\\underline{\1}}'),

        # Add \item to each bullet point.
        (r'^- ?([^-][^\n]*)$', r'\item \1'),

        # Begin and end itemize for bullet points.
        (r'((?:^\\item [^\n]+$(?:\\pause|\n)*){2,})',
r"""
\\begin{itemize}
\1
\\end{itemize}
"""),

        # Replace single linebreaks with double linebreaks.
        (r'([^\n])\n([^\n])', r'\1\n\n\2'),

        # **bold**
        (r'(^|\s)\*\*(.+?)\*\*([^\w\d*]|$)', r'\1\\textbf{\2}\3'),

        # *italics*
        (r'(^|\s)\*(.+?)\*([^\w\d*]|$)', r'\1\\textit{\2}\3'),

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
    # To avoid processing what should be verbatim (`` and two-spaces indented)
    # we remove all verbatim code, replacing with a unique value, and reinsert
    # after all rules are done.
    from uuid import uuid4
    verbatim_replacement = str(uuid4())
    verbatims = []

    def remove_verbatim(match):
        n = len(verbatims)
        verbatims.append(match.group(1))
        return verbatim_replacement + str(n) + '!'
    src = re.sub(r'((?:\n  .+)+|`.*?[^\\]`)', remove_verbatim, src, re.MULTILINE)

    for rule, replacement in rules:
        src = re.sub(rule, replacement, src, flags=re.MULTILINE | re.DOTALL)

    def reinsert_verbatim(match):
        v = verbatims[int(match.group(1))]
        if '\n' in v:
            return r"""\begin{{minted}}[fontsize=\small]{{latex}}
{}
\end{{minted}}""".format(verbatims.pop())
        else:
            return '\\mintinline{{latex}}{{{}}}'.format(v.strip('`'))
    src = re.sub(verbatim_replacement + r'(\d+)!', reinsert_verbatim, src)

    return src

XELATEX_LOCATION = r"C:\Program Files\MiKTeX 2.9\miktex\bin\x64\miktex-xetex.exe"

def generate_pdf(tex_src):
    os.chdir(os.path.join(os.path.dirname(__file__), 'resources'))
    tex_location = 'demo.tex'
    with open(tex_location, 'w', encoding='utf-8') as file:
        file.write(tex_src)
    call([XELATEX_LOCATION, '-undump=xelatex', '-shell-escape', tex_location])
    # Without a second call some section titles get unaligned.
    call([XELATEX_LOCATION, '-undump=xelatex', '-shell-escape', tex_location])
    for temp_file in glob('demo.*'):
        if temp_file != 'demo.pdf':
            os.remove(temp_file)
    return os.path.abspath('demo.pdf')

if __name__ == '__main__':
    # TODO: command line, non-presentation, more templates, better math
    tex_src = apply_rules(rules, open('resources/example.md').read())
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
