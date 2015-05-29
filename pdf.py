from subprocess import call, Popen
import os
from glob import glob
from tempfile import TemporaryDirectory
from shutil import copyfile

import platform
if platform.system() == 'Windows':
    XELATEX_LOCATION = r"C:\Program Files\MiKTeX 2.9\miktex\bin\x64\miktex-xetex.exe"
    OPEN_COMMAND = r'start "{}"'
else:
    XELATEX_LOCATION = r"xelatex"
    OPEN_COMMAND = r'xdg-open "{}"'

def generate_pdf(tex_src, pdf_path='./marktex.pdf'):
    pdf_path = os.path.abspath(pdf_path)
    pdf_basename = os.path.basename(pdf_path)
    file_title = os.path.splitext(pdf_basename)[0]
    old_dir = os.getcwd()
    os.chdir(os.path.join(os.path.dirname(__file__), 'resources'))

    with TemporaryDirectory() as temp_dir:
        tex_path = os.path.join(temp_dir, file_title + '.tex')
        with open(tex_path, 'w') as tex_file:
            tex_file.write(tex_src)

        # Without a second call some section titles get unaligned.
        for i in range(2):
            call([XELATEX_LOCATION, '-undump=xelatex', '-shell-escape',
                '-output-directory', temp_dir, tex_path])

        copyfile(os.path.join(temp_dir, pdf_basename), pdf_path)

        # Pygments doesn't obey the output directory rule and creates a
        # temporary file at this location.
        os.remove(file_title + '.pyg')

    os.chdir(old_dir)
    return pdf_path

def start(file_location):
    Popen([OPEN_COMMAND.format(file_location)], shell=True)
