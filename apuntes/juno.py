#!/usr/bin/env python3
#
# Convierte cuadernos de Jupyter a PDF
# Rubén Rubio (Universidad Complutense de Madrid) 2023
#

import base64
import contextlib
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

from PIL import Image
from markdown_it import MarkdownIt
from mdit_py_plugins.attrs import attrs_plugin
from mdit_py_plugins.texmath import texmath_plugin


# Colores en el orden de las secuencias de escape ANSI 0=black, 1=red, etc.
ANSI_COLOR = ('black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white')

# Comando LaTeX para compilar los PDFs
LATEX_CMD = 'xelatex'  # 'lualatex'


def convert_ansi(texts):
	"""Remove ANSI escape codes"""

	# Output list, whether , whether in an ANSI escape and nesting level
	output, code, in_ansi, level = [], 0, False, 0
	# Whether a foreground or background color is in place
	fg, bg = False, False

	# For each line, and each character
	for text in texts:
		for c in text:
			if in_ansi:
				if c == '[':  # part of the syntax
					pass
				# ; or m indicate the end of a ANSI code
				elif c not in ';m':
					code = 10 * code + int(c)
				else:
					if code == 0:  # reset
						output.append('}' * level)
						level, bg, fg = 0, False, False
					elif code == 1:  # bold
						output.append('¤textbf{')
						level += 1
					elif code == 2:  # italic
						output.append('¤textit{')
						level += 1
					elif 30 <= code <= 37:  # foreground color
						if fg:
							output.append('}')
							level -= 1
						output.append(f'¤textcolor{{{ANSI_COLOR[code % 10]}}}{{')
						level += 1
						fg = True
					# This does not work out of the box, but it does not matter
					# elif 40 <= code <= 47:  # background color
					#	if bg:
					#		output.append('}')
					#		level -= 1
					#	output.append(f'¤colorbox{{{ANSI_COLOR[code % 10]}}}{{')
					#	level += 1
					#	bg = True

					# m (unlike ;) moves back to normal mode
					if c == 'm':
						in_ansi = False
			# Escape character
			elif c == '\x1b':
				in_ansi, code = True, 0
			else:
				output.append(c)
		output.append('\n')

	return [''.join(output)]


def svg2pdf(source_file: str, target_file: str):
	"""Convierte un archivo SVG a PDF"""
	subprocess.run(['rsvg-convert', source_file, '-f', 'pdf', '-o', target_file])


class LaTeXWriter:
	"""LateX for MarkdownIt streams"""

	HEADINGS = {
		'h1': '',
		'h2': 'section',
		'h3': 'subsection',
	}

	def __init__(self, out, md, source_dir, build_dir):
		self.out = out  # flujo de salida (típicamente, archivo .tex)
		self.md = md  # parseador de Markdown
		self.source_dir = source_dir  # directorio fuente (para imágenes)
		self.build_dir = build_dir  # directorio de construcción
		self.needs_indent = False  # si hace falta identar el siguiente párrafo
		self.cell_metadata = None  # metadatos de la celda

		# For tables
		self.column_count = 0  # número de columnas vistas
		self.out_stack = []  # pila de flujos de salida (véase el apartado de tablas)
		self.first_col = True  # si esta es la primera columna

	def process(self, stream, metadata=None):
		"""Procesa un flujo de elemento parseados por MarkdownIt"""
		self.needs_indent = False
		if metadata is not None:
			self.cell_metadata = metadata
			# Código TeX previo indicado en los metadatos
			if pretex := metadata.get('pretex'):
				self.out.write(pretex + ' ')
		for token in stream:
			self.handle(token)

	def handle(self, token):
		# Delega en el método de la clase cuyo nombre coincide con el tipo de elemento
		getattr(self, token.type, self.unknown)(token)

	def paragraph_open(self, token):
		self.out.write('\n\\medskip ' if self.needs_indent else '\n\\noindent ')
		self.needs_indent = False

	def paragraph_close(self, token):
		self.needs_indent = True
		self.out.write('\n')

	def inline(self, token):
		self.process(token.children)

	## Texto y formato básico

	def text(self, token):
		self.out.write(token.content)

	def em_open(self, token):
		self.out.write('\\emph{')

	def em_close(self, token):
		self.out.write('}')

	def strong_open(self, token):
		self.out.write('\\textbf{')

	def strong_close(self, token):
		self.out.write('}')

	## Hiperenlaces

	def link_open(self, token):
		self.out.write(f'\\href{{{token.attrs["href"]}}}{{')

	def link_close(self, token):
		self.out.write('}')

	## Bloques de código (por defecto en Python)

	def code_inline(self, token):
		if style := token.attrs.get('class'):
			self.out.write(f'\\mintinline[breaklines]{{{style}}}£{token.content}£')
		else:
			# Jupyter no entiende la notación {.} así que se asume Python
			# (salvo indicación en contra para la celda con class, si hubiera necesidad)
			self.out.write(f'\\mintinline[breaklines, breakafter=/, breakaftersymbolpre=]{{python}}£{token.content}£')

	def code_block(self, token):
		self.out.write(r'\begin{verbatim}')
		self.out.write(token.content)
		self.out.write(r'\end{verbatim}')

	def fence(self, token):
		self.out.write(f'\\begin{{minted}}[xleftmargin=1em]{{{token.info}}}\n')
		self.out.write(token.content)
		self.out.write('\\end{minted}\n')
		self.needs_indent = False

	## Encabezados

	def heading_open(self, token):
		# El primer encabezado es el título del documento y los siguientes encabezados normales
		if token.tag == 'h1':
			self.out.write(r'\begin{center}{\bfseries\Large ' + '\n')
		else:
			variant = self.HEADINGS[token.tag]
			# notoc permite excluir secciones del índice (como las referencias)
			if self.cell_metadata.get('notoc', False):
				variant += '*'
			self.out.write(f'\\{variant}{{')

	def heading_close(self, token):
		if token.tag == 'h1':
			self.out.write(r'}\\[.5ex] Informática – Facultad de Ciencias Matemáticas (UCM) \\[.2ex]'
			               r'\small \today \end{center}\vspace{2em}')
		else:
			self.out.write('}\n')

		self.needs_indent = False

	## Etiquetas HTML para efectos especiales

	def html_inline(self, token):
		# Algunos comandos LaTeX de espaciado
		if token.content == '<hfill/>':
			self.out.write(r'\hfill ')
		elif token.content == '<bigskip/>':
			self.out.write(r'\bigskip')
		elif token.content == '<noindent/>':
			self.out.write(r'\noindent ')

		# Notas al pie
		elif token.content.startswith('<footnote'):
			# Se espera un atributo text con el texto Markdown de la nota
			try: text = ET.fromstring(token.content).get('text')
			except ET.ParseError:
				print('Error en la nota al pie', token.content)
				return

			# Hace falta el parseador Markdown para parsear este texto
			self.out.write(r'\footnote{')
			self.process(self.md.parse(text))
			self.out.write('}')

	## Imágenes

	def image(self, token):
		# Ubicación de la imagen
		src = token.attrs['src']

		# La copia al directorio de construcción
		source_file = os.path.join(self.source_dir, src)
		target_file = os.path.join(self.build_dir, src)
		os.makedirs(os.path.dirname(target_file), exist_ok=True)

		# Comprobar si el archivo ya existe (se podría haber incluido varias veces)
		if not os.path.exists(target_file) or os.getmtime(target_file) < os.getmtime(source_file):
			# Si es SVG hay que convertirlo antes de PDF para incluirlo en el documento LaTeX
			# y esto se hace con rsvg-convert, que debería estar instalado
			if src.endswith('.svg'):
				target_file = target_file[:-3] + 'pdf'
				src = src[:-3] + 'pdf'
				svg2pdf(source_file, target_file)
			# En caso contrario, se supone que la imagen está soportada por LaTeX y se pone
			# simplemente un enlace simbólico a la imagen original
			else:
				os.symlink(source_file, target_file)

		# Modificaciones a la imagen según los metadatos de la celda (anchura)
		tweaks = ''

		if width := self.cell_metadata.get('img_width'):
			tweaks = f'[width={width}]'

		self.out.write(f'\n\\begin{{center}}\\includegraphics{tweaks}{{{src}}}\\end{{center}}')

	## Citas (usa el entorno quotation)

	def blockquote_open(self, token):
		self.out.write('\\begin{quotation}')

	def blockquote_close(self, token):
		self.out.write('\\end{quotation}')

	## Texto matemático

	def math_inline(self, token):
		self.out.write(f'${token.content}$')

	def math_single(self, token):
		self.out.write(f'${token.content}$')

	def math_block(self, token):
		self.out.write(f'\\[{token.content}\\]')

	## Listas de elementos (con itemize y enumerate)

	def bullet_list_open(self, token):
		self.out.write(r'\begin{itemize}')

	def ordered_list_open(self, token):
		self.out.write(r'\begin{enumerate}')

	def list_item_open(self, token):
		self.out.write(r'\item')

	def list_item_close(self, token):
		self.needs_indent = False

	def ordered_list_close(self, token):
		self.out.write(r'\end{enumerate}')

	def bullet_list_close(self, token):
		self.out.write(r'\end{itemize}')

	def softbreak(self, token):
		self.out.write('\n')

	## Tablas (con tabular y booktabs)

	def table_open(self, token):
		self.out.write('\n\\begin{center}\\begin{tabular}')

	def table_close(self, token):
		self.out.write(r'\bottomrule')
		self.out.write('\\end{tabular}\n\\end{center}\n')

	def thead_open(self, token):
		self.column_count = 0
		# No sabremos el número de columnas hasta leer la primera fila y
		# tenemos que indicarlo ahora, así que reemplazamos out para retrasar
		# la impresión del encabezado
		self.out_stack.append(self.out)
		self.out = io.StringIO()

	def thead_close(self, token):
		header_row = self.out.getvalue()
		self.out = self.out_stack.pop()

		# Imprime la especificación de columnas
		spec = '{' + ' '.join('l' * self.column_count) + '}\\toprule\n'
		self.out.write(spec)

		# Imprime el encabezado (si no es vacío)
		if header_row.strip(' &\t \\\n'):
			self.out.write(header_row)
			self.out.write(r'\midrule')

	def tr_open(self, token):
		self.first_col = True

	def tr_close(self, token):
		self.out.write(r' \\' + '\n')

	def th_open(self, token):
		self.column_count += 1
		self.td_open(token)

	def td_open(self, token):
		# Imprime un salto de columna (&) salvo antes de la primera
		if not self.first_col:
			self.out.write(' & ')
		else:
			self.out.write('\t')
			self.first_col = False

	def th_close(self, token):
		pass

	def tbody_open(self, token):
		pass

	def tbody_close(self, token):
		pass

	def td_close(self, token):
		pass

	def unknown(self, token):
		input(f'Token desconocido: {token}')


# Preámbulo del documento LaTeX para generar (adáptese al gusto)
PREAMBLE = r'''\documentclass[a4paper]{article}
\usepackage{polyglossia}
\setmainlanguage{spanish}
\usepackage{fontspec}
\setmainfont{Nimbus Sans}
\setmonofont[Scale=MatchLowercase, Contextuals={AlternateOff}]{Fantasque Sans Mono}
\usepackage{unicode-math}
\setmathfont{XITS Math}
\usepackage[hmargin=2.25cm, vmargin=2.5cm]{geometry}
\usepackage{minted}
\usepackage{graphicx}
\usepackage[colorlinks]{hyperref}
\usepackage{booktabs}
\usepackage{fancyhdr}
'''

BEGIN_DOCUMENT = r'''\begin{document}
\thispagestyle{fancy}
\renewcommand{\headrulewidth}{0pt}
\fancyhead{}
\fancyfoot[C]{
	\lower.5ex\hbox{\includegraphics[scale=0.5]{img/cc-byncsa}} \qquad
	{\small \color{black!70} \autores, Universidad Complutense de Madrid \qquad 2023}
}
'''

EPILOGUE = r'''\end{document}'''


def make_build_dir(filename: str, use_cache=False):
	"""Prepara un directorio para construir el documento"""

	# Si la caché está activada, utiliza el subdirectorio .cache del catual
	if use_cache:
		build_path = os.path.join('.cache', filename.replace(os.pathsep, '_'))
		os.makedirs(build_path, exist_ok=True)
		return contextlib.nullcontext(build_path)
	else:
		return tempfile.TemporaryDirectory()


def convert(filename: str, outname: str, interactive=False, use_cache=False) -> bool:
	"""Convierte un cuaderno a PDF"""

	# Carga el cuaderno de Jupyter (es un JSON)
	with open(filename) as cfile:
		cuaderno = json.load(cfile)

	# Autores de los apuntes separados por comas
	autores = ', '.join(au['name'] for au in cuaderno['metadata'].get('authors', ()))

	# Crea el aparseador de Markdown con soporte para LaTeX, tablas y atributos
	md = MarkdownIt().use(texmath_plugin).use(attrs_plugin).enable('table')

	JOBNAME = 'cuaderno'  # Nombre del trabajo LaTeX

	with make_build_dir(filename, use_cache) as tmp_dir:
		tex_file = os.path.join(tmp_dir, f'{JOBNAME}.tex')
		pdf_file = os.path.join(tmp_dir, f'{JOBNAME}.pdf')

		# Copia el símbolo de CC-BYNCSA
		cc_img = os.path.join(tmp_dir, 'img', 'cc-byncsa.pdf')

		if not os.path.exists(cc_img):
			os.makedirs(os.path.dirname(cc_img), exist_ok=True)
			svg2pdf('img/cc-byncsa.svg', cc_img)

		with open(tex_file, 'w') as tex:
			tex.write(PREAMBLE)
			# El LaTeXWriter recibe el parseador de Markdown porque puede
			# necesitar hacer parseos secundarios
			lt = LaTeXWriter(tex, md, os.path.dirname(filename), tmp_dir)

			# Intenta sacar el título del primer encabezado para ponerlo como metadato
			if cuaderno['cells'] and (primera := cuaderno['cells'][0]['source']) and primera[0].startswith('#'):
				título = cuaderno['cells'][0]['source'][0][2:]
				tex.write(f'''\hypersetup{{
					pdfauthor={{{autores}}},
					pdftitle={{{título}}},
					pdfsubject={{Informática FCM-UCM}},
				}}''')

			# Define los autores como un comando
			tex.write(f'\\newcommand\\autores{{{autores}}}\n')

			tex.write(BEGIN_DOCUMENT)

			# Recorre e imprime las celdas del cuaderno, cada una según su tipo
			for celda in cuaderno['cells']:
				cell_type = celda['cell_type']
				content = ''.join(celda['source'])

				# Las celdas Markdown se convierten a LaTeX sin sorpresas
				if cell_type == 'markdown':
					lt.process(md.parse(content), celda.get('metadata', {}))

				# Y las celdas de código se copian a un entorno minted
				elif cell_type == 'code':
					lang = celda.get('metadata', {}).get('lang', 'python')
					tex.write('\\begin{minted}[breaklines=true,frame=single,rulecolor=black!30]{' + lang + '}\n')
					tex.write(content + '\n')
					tex.write('\\end{minted}\n')

				# Cada celda tiene asociada una o más salidas, que suelen ser el
				# resultado de la ejecución del código como texto, imagen, etc.
				has_display = any(out['output_type'] == 'display_data'
				                  for out in celda.get('outputs', ()))

				for output in celda.get('outputs', ()):
					output_type = output['output_type']

					highlight = False
					attrs = ['breaklines=true', 'frame=single']

					if has_display and output_type != 'display_data':
						continue

					# Se asume que la salida display_data es una imagen PNG
					if output_type == 'display_data':
						img_base = output['data']['image/png']
						img = Image.open(io.BytesIO(base64.b64decode(img_base)))
						# Se guarda en el directorio de construcción para que pueda cargarla LaTeX
						src = f'img/{hashlib.sha1(img_base.encode("ascii")).hexdigest()}.jpg'
						img.convert('L').save(os.path.join(tmp_dir, src))
						# Se puede indicar un factor de escala en los metadatos
						scale = celda.get('metadata', {}).get('scale', 0.5)
						tex.write(f'\n\\begin{{center}}\\includegraphics[scale={scale}]{{{src}}}\\end{{center}}')
						continue
					# Resultado de la ejecución del código (un objeto Python)
					elif output_type == 'execute_result':
						content = ''.join(output['data']['text/plain']) + '\n'
						highlight = True
						attrs.append('rulecolor=green!30')
					# Error de Python, se formatea el mensaje y la pila de llamadas
					elif output_type == 'error':
						content = convert_ansi(output['traceback'])
						# Usamos ¤ como iniciador del comando porque es raro que aparezca en el texto
						attrs += ['rulecolor=red!30', r'commandchars=¤\{\}', r'fontsize=\small']
					# Texto impreso por pantalla
					elif output_type == 'stream':
						content = output['text']
						if not content[-1].endswith('\n'):
							content = content + ['\n']
						attrs.append('rulecolor=blue!30')
					# Esto no debería ocurrir
					else:
						content = f'[Tipo de salida desconocido {output_type}]'
						attrs.append('rulecolor=red!30')

					# Imprime el código con las configuraciones anteriores
					attrs = ','.join(attrs)
					tex.write(f'\\begin{{minted}}[{attrs}]{{python}}\n'
					          if highlight else f'\\begin{{Verbatim}}[{attrs}]\n')
					tex.write(''.join(content))
					tex.write('\\end{minted}\n' if highlight else '\\end{Verbatim}\n')

			tex.write(EPILOGUE)

		# La salida de LaTeX no se imprime por pantalla y no se pausa cuando hay un error
		# salvo que la opción interactive esté activada
		if not interactive:
			latex_args = ['-interaction', 'nonstopmode']
			stdout_dest = subprocess.PIPE
		else:
			latex_args = []
			stdout_dest = None

		# Llama a LaTeX con -shell-escape porque lo necesita minted
		ret = subprocess.run([LATEX_CMD, '-shell-escape', *latex_args, f'{JOBNAME}.tex'],
		                     cwd=tmp_dir, stdout=stdout_dest)

		if ret.returncode != 0:
			print('Error al compilar con LaTeX:', ret.stdout.decode('utf-8'))
		else:
			# Podría hacer falta una segunda ejecución para referencias y demás
			# subprocess.run([LATEX_CMD, '-shell-escape', *latex_args, tex_file],
			#               cwd=tmp_dir, stdout=subprocess.DEVNULL)
			# Copia el archivo fuera del directorio de construcción
			shutil.copy(pdf_file, outname)

	return True


def main():
	import argparse

	parser = argparse.ArgumentParser(description='Convierte cuadernos de Jupyter a PDF')
	parser.add_argument('cuaderno', help='Cuaderno')
	parser.add_argument('--interactive', '-i', help='Modo interactivo de LaTeX', action='store_true')
	parser.add_argument('--cache', help='Usa una caché para ahorrar tiempo de compilación', action='store_true')
	parser.add_argument('-o', help='Destino del archivo generado (si es carpeta existente, genera un archivo en ella)')

	args = parser.parse_args()

	# Determina el nombre del archivo de salida
	outname = os.path.splitext(os.path.basename(args.cuaderno))[0] + '.pdf'

	if args.o:
		# Si es un directorio, guarda el archivo en él
		if os.path.isdir(args.o):
			outname = os.path.join(args.o, outname)
		# Si la ruta no existe y no acaba en .pdf, asume que es un directorio y lo crea
		elif not os.path.exists(args.o) and not args.o.endswith('.pdf'):
			os.makedirs(args.o)
			outname = os.path.join(args.o, outname)
		# En otro caso, guarda el archivo en la ruta indicada
		else:
			outname = args.o

	return 0 if convert(args.cuaderno, outname, interactive=args.interactive, use_cache=args.cache) else 1


if __name__ == '__main__':
	sys.exit(main())
