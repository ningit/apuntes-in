#!/usr/bin/env python3
#
# Comprobaciones sobre cuadernos de Jupyter
# Rubén Rubio (Universidad Complutense de Madrid) 2023
#

import subprocess
import tempfile

import nbconvert
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor


def mypy(nb, args):
	""""Comprobación de tipos con mypy"""

	# Extrae el código Python del cuaderno
	converter = nbconvert.PythonExporter(exclude_markdown=True, exclude_output=True, exclude_raw=True)
	code, _ = converter.from_notebook_node(nb)

	# Borra líneas que empiezan por get_ipython (comandos mágicos en el cuaderno)
	code = '\n'.join(line for line in code.splitlines() if not line.startswith('get_ipython'))

	# Ejecuta mypy y muestra los errores por pantalla
	with tempfile.NamedTemporaryFile(mode='w', suffix='.py') as outfile:
		outfile.write(code)
		outfile.flush()

		subprocess.run(['mypy', '--pretty', outfile.name])


def lang(nb, args):
	"""Comprobación ortográfica del texto"""

	# Extrae el código Markdown del cuaderno
	converter = nbconvert.MarkdownExporter(exclude_code_cell=True)
	code, _ = converter.from_notebook_node(nb)

	# Usa textidote para comprobar la ortografía y gramática
	with tempfile.NamedTemporaryFile(mode='w', suffix='.md') as outfile:
		outfile.write(code)
		outfile.flush()

		comando = ['textidote', '--check', 'es']

		if args.o is None:
			subprocess.run([*comando, outfile.name])
		else:
			with open(args.o, 'w') as html:
				subprocess.run([*comando, '-output', 'html', outfile.name], stdout=html)


def reduce(nb, args):
	"""Reduce el tamaño del archivo convirtiendo las imágenes"""

	import base64
	import io
	from PIL import Image

	# Considera las salidas de tipo display de cada celda
	for celda in nb['cells']:
		for out in celda.get('outputs', ()):
			if out['output_type'] == 'display_data':
				if 'image/png' in out['data']:
					png_base64 = out['data']['image/png']
					# Convierte la imagen PNG en JPG
					img = Image.open(io.BytesIO(base64.b64decode(png_base64)))
					stream = io.BytesIO()
					img.convert('RGB').save(stream, format='jpeg')
					jpg_base64 = base64.b64encode(stream.getvalue()).decode('ascii')
					# Si hay mejora de tamaño la reemplaza
					if png_base64 > jpg_base64:
						out['data'].pop('image/png')
						out['data']['image/jpeg'] = jpg_base64

	# Guarda el cuaderno reducido
	with open(args.cuaderno + '_reduced', 'w') as f:
		nbformat.write(nb, f)


def run(nb, args):
	"""Ejecuta el cuaderno y actualiza sus celdas"""

	ep = ExecutePreprocessor(timeout=600, kernel_name='python3', allow_errors=True, record_timing=False)
	ep.preprocess(nb)
	with open(args.cuaderno, 'w') as f:
		nbformat.write(nb, f)


def main():
	import argparse

	parser = argparse.ArgumentParser(description='Herramientas para cuadernos de Jupyter')
	parser.add_argument('action', choices=['mypy', 'lang', 'run', 'reduce'], default='mypy')
	parser.add_argument('cuaderno', help='Cuaderno')
	parser.add_argument('-o', help='Guarda la salida de lang como un archivo HTML')

	args = parser.parse_args()

	# Lee el cuaderno de Jupyter
	with open(args.cuaderno) as ipynb:
		nb = nbformat.read(ipynb, as_version=4)

	# Ejecuta la acción correspondiente
	acciones = dict(mypy=mypy, lang=lang, run=run, reduce=reduce)
	acciones[args.action](nb, args)
	return 0


if __name__ == '__main__':
	main()

