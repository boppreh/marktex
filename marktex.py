#! /bin/env python3
import presentation
import re
from pdf import generate_pdf, start
import tempfile

templates = {'presentation': presentation.translate}

def compile_src(marktex_src, template='presentation'):
    """
    Compiles the Marktex source to a temporary PDF and returns its path.
    """
    tex_src = templates[template](marktex_src)
    temp_id, pdf_path = tempfile.mkstemp(suffix='.pdf')
    generate_pdf(tex_src, pdf_path)
    return pdf_path

def compile_file(marktex_file, template='presentation'):
    """
    Compiles the Marktex file at the given location to a similarly named PDF.
    """
    with open(marktex_file) as file:
        marktex_src = file.read()
        tex_src = templates[template](marktex_src)
        pdf_path = re.sub(r'\.\w+$', '.pdf', marktex_file)
        generate_pdf(tex_src, pdf_path)
    return pdf_path

if __name__ == '__main__':
    #start(compile_file('example.md')); exit()
    from sys import argv, stdin
    if len(argv) <= 1:
        marktex_src = stdin.buffer.read().decode('utf-8')
        start(compile_src(marktex_src))
    elif len(argv) >= 2:
        for file_path in argv[1:]:
            compile_file(file_path)
