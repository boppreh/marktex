#! /bin/env python3
import presentation
import re
from pdf import generate_pdf, start

templates = {'presentation': presentation.translate}

def compile_src(marktex_src, template='presentation'):
    tex_src = templates[template](marktex_src)
    return generate_pdf(tex_src)

def compile_file(marktex_file, template='presentation'):
    with open(marktex_file) as file:
        marktex_src = file.read()
        tex_src = templates[template](marktex_src)
        return generate_pdf(tex_src, re.sub(r'\.\w+$', '.pdf', marktex_file))

if __name__ == '__main__':
    #start(compile_file('example.md')); exit()
    from sys import argv, stdin
    if len(argv) <= 1:
        marktex_src = stdin.buffer.read().decode('utf-8')
        start(compile_src(marktex_src))
    elif len(argv) >= 2:
        for file_path in argv[1:]:
            compile_file(file_path)
