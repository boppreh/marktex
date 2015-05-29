#! /bin/env python3
import re
from subprocess import call, Popen
import os
from glob import glob

import platform
if platform.system() == 'Windows':
    XELATEX_LOCATION = r"C:\Program Files\MiKTeX 2.9\miktex\bin\x64\miktex-xetex.exe"
    OPEN_COMMAND = r'start "{}"'
else:
    XELATEX_LOCATION = r"xelatex"
    OPEN_COMMAND = r'xdg-open "{}"'

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

languages = """
cucumber 	abap 	ada 	ahk
antlr 	apacheconf 	applescript 	as
aspectj 	autoit 	asy 	awk
basemake 	bash 	bat 	bbcode
befunge 	bmax 	boo 	brainfuck
bro 	bugs 	c 	ceylon
cfm 	cfs 	cheetah 	clj
cmake 	cobol 	cl 	console
control 	coq 	cpp 	croc
csharp 	css 	cuda 	cyx
d 	dg 	diff 	django
dpatch 	duel 	dylan 	ec
erb 	evoque 	fan 	fancy
fortran 	gas 	genshi 	glsl
gnuplot 	go 	gosu 	groovy
gst 	haml 	haskell 	hxml
html 	http 	hx 	idl
irc 	ini 	java 	jade
js 	json 	jsp 	kconfig
koka 	lasso 	livescrit 	llvm
logos 	lua 	mako 	mason
matlab 	minid 	monkey 	moon
mxml 	myghty 	mysql 	nasm
newlisp 	newspeak 	numpy 	ocaml
octave 	ooc 	perl 	php
plpgsql 	postgresql 	postscript 	pot
prolog 	psql 	puppet 	python
qml 	ragel 	raw 	ruby
rhtml 	sass 	scheme 	smalltalk
sql 	ssp 	tcl 	tea
tex 	text 	vala 	vgl
vim 	xml 	xquery 	yaml 
"""

def include_source(match):
    language = match.group(2)
    if language not in languages:
        language = 'latex'
    path = os.path.abspath(match.group(1))
    return r'\inputminted[fontsize=\small]{{{}}}{{{}}}'.format(language, path)

def include_image(match):
    path = os.path.abspath(match.groups()[-1])
    if len(match.groups()) == 1:
        return r"""
\begin{{center}}
\includegraphics[width=\linewidth,height=0.8\textheight,keepaspectratio]{{{}}}
\end{{center}}
""".format(path)
    else:
        return r"""
\begin{{figure}}
\begin{{center}}
\includegraphics[width=\linewidth,height=0.7\textheight,keepaspectratio]{{{}}}
\caption{{{}}}
\end{{center}}
\end{{figure}}
""".format(path, match.groups(1))

def include_math(match):
    text = match.group(1).strip()
    text = text.replace('(', '\\left(')
    text = text.replace(')', '\\right)')
    text = text.replace('[', '\\left[')
    text = text.replace(']', '\\right]')
    text = text.replace('/', '\\over')
    text = text.replace('*', '\\times')
    text = re.sub(r'([^a-zA-Z])log([^a-zA-Z])', r'\1\\log\2', text)
    if '\n' in text:
        text = re.sub(r'\n+', r'\\\\', text).strip('\n')
        return '\\begin{gather*}' + text + '\\end{gather*}'
    else:
        return '$' + text + '$'

presentation_rules = [
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

generic_rules = [
        # Latex hates unescaped characters.
        (r'([$#%])', r'\\\1'),

        # Annotations using {text}(annotation) syntax.
        # Hackish because we enter math mode needlessly, but I found no other
        # way.
        (r'\{([^\n]+?)\}\(([^\n]+?)\)', r'$\\underbrace{\\text{\1}}_{\\text{\2}}$'),

        # Two dollars start math mode.
        (r'\\\$\\\$([^$]+?)\\\$\\\$', include_math),


        # Tables as such:
        #
        # | Header 1 | Header 2 | Header 3 |
        # |---------:|:--------:|:---------|
        # | Value    |   Value  |    Value |
        # | Value    |   Value  |    Value |
        # | Value    |   Value  |    Value |
        (r'(?<=\n\n)((?:^\|.+?\|\n)+)', convert_table),

        # Simple images using !(image.jpg) syntax.
        (r'^!\(([^)]+?\.(?:jpg|jpeg|gif|png|bmp|pdf|tif))\)$', include_image),

        # Code embedding with !(code.py) syntax.
        (r'^!\(([^)]+?\.(\w+))\)$', include_source),

        # Captioned images using ![caption](image.jpg) syntax.
        (r'^!\[([^\]]+?)\]\(([^)]+?)\)$', include_image),
        
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
]

def apply(rules_list, src):
    for rules in rules_list:
        for rule, replacement in rules:
            src = re.sub(rule, replacement, src, flags=re.MULTILINE | re.DOTALL)
    return src

def translate(rules_list, src, header, footer):
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
    src = re.sub(r'((?:^\s\s.*\n)+|`.*?[^\\]`)', remove_verbatim, src, flags=re.MULTILINE)

    src = apply(rules_list, src)

    def reinsert_verbatim(match):
        v = verbatims[int(match.group(1))]
        v = v.replace('{', r'\{')
        v = v.replace('}', r'\}')
        if '\n' in v:
            return r"""\begin{{minted}}[fontsize=\small]{{latex}}
{}
\end{{minted}}""".format(verbatims.pop())
        else:
            return '\\texttt{{\\lstinline{{{}}}}}'.format(v.strip('`'))
    src = re.sub(verbatim_replacement + r'(\d+)!', reinsert_verbatim, src)

    return header + src + footer

def translate_presentation(src):
    # If the user uses section titles, but not slide titles, the slides will
    # look weird. So it's best if we use the section slides as slide titles.
    if not re.search(r'^## ', src, flags=re.MULTILINE):
        src = re.sub(r'^#', r'##', src, flags=re.MULTILINE)
        pass

    header = r"""
\documentclass[10pt, compress]{beamer}

\usetheme{m}

\usepackage{amsmath}
\usepackage{booktabs}
\usepackage{minted}
\usepackage{listings}

\usepackage{hyperref}
\hypersetup{colorlinks=true,urlcolor=blue}

\usemintedstyle{trac}

\newcommand{\lasttitle}{}

\begin{document}
"""

    footer = r'\end{document}'


    return translate([presentation_rules, generic_rules], src, header, footer)

def generate_pdf(tex_src):
    old_dir = os.getcwd()
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

    pdf_location = os.path.abspath('demo.pdf')
    os.chdir(old_dir)
    return pdf_location

def run(src, outfile):
    tex_src = translate_presentation(src)
    pdf_location = generate_pdf(tex_src)
    os.rename(pdf_location, outfile)

if __name__ == '__main__':
    from sys import argv, stdin
    if len(argv) <= 1:
        src = stdin.buffer.read().decode('utf-8')
        #src = '$$1 + 1 / 1 + 1\n1 * 1 / 1 * 1$$'
        print(translate_presentation(src))
        run(src, 'marktex.pdf')
        Popen([OPEN_COMMAND.format('marktex.pdf')], shell=True)
    elif len(argv) >= 2:
        for file_path in argv[1:]:
            contents = open(file_path).read()
            out_path = re.sub(r'\.\w+$', '.pdf', file_path)
            run(contents, out_path)
