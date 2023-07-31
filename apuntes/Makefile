#
# Construye el PDF de todos los apuntes
#

all: pdf/Archivos.pdf pdf/Diccionarios.pdf pdf/Ordenación.pdf pdf/Recursión.pdf \
     pdf/Referencia.pdf pdf/Estructurados.pdf pdf/Matrices.pdf pdf/Anotaciones.pdf

pdf/%.pdf: %.ipynb juno.py
	./juno.py --cache -o pdf $<
