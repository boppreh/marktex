from subprocess import call, Popen
import os
from glob import glob
from tempfile import TemporaryDirectory
from shutil import copyfile

import platform
if platform.system() == 'Windows':
    XELATEX_LOCATION = r"C:\Program Files\MiKTeX 2.9\miktex\bin\x64\miktex-xetex.exe"
    OPEN_COMMAND = r'start'
else:
    XELATEX_LOCATION = r"xelatex"
    OPEN_COMMAND = r'xdg-open'

def generate_pdf(tex_src, pdf_path):
    """
    Given a source latex file, compiles this source to PDF at the given path.
    """

    # There are four directories at play here:
    # 1. The current directory, will be changed and must be restored and is
    # otherwise not touched.
    # 2. The marktex/resources directory with the beamer theme use as current
    # directory during the generation.
    # 3. The temporary directory, where we write the source tex file and all
    # latex temporary files are created.
    # 4. The directory at the target path, which we only touch to create the
    # pdf file.

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

def start(file_location):
    """
    Displays a file by e.g. opening a PDF viewer, browser, etc.
    """
    Popen([OPEN_COMMAND, file_location], shell=True)
