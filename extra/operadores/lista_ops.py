#!/usr/bin/env python3
#
# Genera la lista de métodos especiales
# Rubén Rubio (Universidad Complutense de Madrid) 2023
#

import os
import shutil
import subprocess
import tempfile

import yaml

PREAMBULO = r'''\documentclass[a4paper, 11pt]{article}

\usepackage{fontspec}
\usepackage[hmargin=1.9cm, vmargin=2cm]{geometry}
\setmainfont{Source Sans 3}
\setmonofont[Scale=MatchLowercase, Contextuals={AlternateOff}]{Fantasque Sans Mono}
\usepackage{minted}
\usepackage{xcolor,colortbl}
\usepackage[colorlinks]{hyperref}

\hypersetup{
	pdftitle={Tabla de nombres de método especiales en Python},
	pdfauthor={Rubén Rubio},
	pdfsubject={Informática FCM-UCM},
}

\arrayrulecolor{olive}
\pagestyle{empty}

\begin{document}
\begin{center}\Large\bfseries Tabla de nombres de método especiales\end{center}

\vspace{.5cm}

\noindent Relación incompleta de nombres de método que tienen un significado especial en Python. La
\href{https://docs.python.org/es/3/reference/datamodel.html}{lista completa} se puede encontrar en la documentación
oficial de Python. En la mayoría de los casos se usan para especializar operadores o funciones predefinidas en el tipo
en el que se declaran. La tercera columna indica la sintaxis especial que invoca cada método y la cuarta columna su
comportamiento por defecto (salvo que sea producir un error porque no está definida la operación).

\vspace{.5cm}
\noindent\hspace{4pt}\begin{tabular}{|l|l|l|l|c|} \hline
\textsc{Significado} & \textsc{Nombre} & \textsc{Sintaxis} & \textsc{Valor por defecto} & \textsc{Obs} \\ \hline
'''

EPILOGO = r'''\end{document}'''


def renombrado(texto):
	"""Renombra las psudovariables que se usan en la lista por conveniencia"""

	return texto.replace('o1', 'obj').replace('o2', 'arg')


notas = []

with tempfile.TemporaryDirectory() as tdir:
	tex_name = os.path.join(tdir, 'lista_ops.tex')
	pdf_name = os.path.join(tdir, 'lista_ops.pdf')

	# La lista de operadores es un archivo YAML
	with open('operadores.yaml') as operadores_file:
		operadores = yaml.safe_load(operadores_file)

	# El archivo LaTeX con la tabla que dará lugar al PDF
	with open(tex_name, 'w') as tex:
		tex.write(PREAMBULO)

		for op in operadores:
			safe_name = op['name']  # Nombre sin barras bajas
			safe_exam = r'\mintinline{python}{' + renombrado(op['exam']) + '}'
			safe_defs = (r'\mintinline{python}{' + renombrado(op['defs']) + '}') if 'defs' in op else ''

			# Si hay una nota añade un enlace (visual) y deja la nota para el final del documento
			if nota := op.get('nota'):
				notas.append(nota)
				nota_link = f'({len(notas)})'
			else:
				nota_link = ''

			# Imprime la fila de la tabla para este operador
			tex.write(f'{op["desc"]} & \\texttt{{\\_\\_{safe_name}\\_\\_}} & {safe_exam} & '
			          f'{safe_defs} & {nota_link} \\\\\n \\hline ')

		# Cierra la tabla, ahora vienen las notas
		tex.write(r'\end{tabular} \vspace{.75cm}')

		# Lista de notas en letra más pequeña
		for k, nota in enumerate(notas, start=1):
			print(f'\\par\\noindent ({k})', nota, file=tex)

		tex.write(EPILOGO)

	# Compila la tabla con LaTeX
	subprocess.run(['xelatex', '-shell-escape', tex_name], cwd=tdir)
	shutil.move(pdf_name, 'lista_ops.pdf')
