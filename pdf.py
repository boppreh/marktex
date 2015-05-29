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

def generate_pdf(tex_src, target_path='./marktex.pdf'):
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
    os.rename(pdf_location, target_path)
    return target_path

def start(file_location):
    Popen([OPEN_COMMAND.format(file_location)], shell=True)
