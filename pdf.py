from subprocess import call, Popen
import os
from glob import glob
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import platform
if platform.system() == 'Windows':
    XELATEX_LOCATION = r"C:\Program Files\MiKTeX 2.9\miktex\bin\x64\miktex-xetex.exe"
    OPEN_COMMAND = r'start'
else:
    XELATEX_LOCATION = r"xelatex"
    OPEN_COMMAND = r'xdg-open'

resources_zip = os.path.join(os.path.dirname(__file__), 'mtheme.zip')

def generate_pdf(tex_src, pdf_path):
    """
    Given a source latex file, compiles this source to PDF at the given path.
    """
    pdf_path = os.path.abspath(pdf_path)
    pdf_basename = os.path.basename(pdf_path)
    file_title = os.path.splitext(pdf_basename)[0]

    old_dir = os.getcwd()
    with TemporaryDirectory() as temp_dir:
        print('Navigating to temporary directory', temp_dir)
        os.chdir(temp_dir)

        print('Extracting resources')
        with ZipFile(resources_zip) as zip_file:
            zip_file.extractall('.')

        tex_path = os.path.join(temp_dir, file_title + '.tex')
        print('Creating .tex file at', tex_path)
        with open(tex_path, 'w') as tex_file:
            tex_file.write(tex_src)

        print('Compiling...')
        # Without a second call some section titles get unaligned.
        for i in range(2):
            call([XELATEX_LOCATION, '-undump=xelatex', '-shell-escape', tex_path])

        print('Copying generated PDF to ', pdf_path)
        # This is equivalent to shutil.copy. Unfortunately the shutil
        # operations were leaving the file handle open, keeping the temporary
        # folder from being deleted.
        with open(os.path.join(temp_dir, pdf_basename), 'rb') as in_pdf_file:
            with open(pdf_path, 'wb') as out_pdf_file:
                out_pdf_file.write(in_pdf_file.read())

        print('Navigating back to', old_dir)
        os.chdir(old_dir)
        print(tex_src)

def start(file_location):
    """
    Displays a file by e.g. opening a PDF viewer, browser, etc.
    """
    Popen([OPEN_COMMAND, file_location], shell=True)
