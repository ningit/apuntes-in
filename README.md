## Apuntes de Informática

Apuntes de la asignatura *Informática* (segundo cuatrimestre) de la Facultad de Ciencias Matemáticas de la Universidad Complutense de Madrid.

Los apuntes son cuadernos de [Jupyter](https://jupyter.org/) incluidos en el directorio [apuntes](apuntes). Otro material auxiliar se encuentra en la carpeta [extra](extra).

### Generar PDF de los cuadernos de Jupyter

Es posible generar versiones en PDF de los apuntes con el script `juno.py`, que requiere tener instalado [markdown-it-py](https://github.com/executablebooks/markdown-it-py), [Pillow](https://python-pillow.org/), [librsvg](https://wiki.gnome.org/Projects/LibRsvg), [Pygments](https://pygments.org/) y una distribución moderna de LaTeX. Se utilizan por defecto las tipografías Nimbus Sans, [Fantasque Sans Mono](https://github.com/belluzj/fantasque-sans) y [XITS Math](https://github.com/aliftype/xits), pero estas se pueden cambiar en la constante `PREAMBLE` del script.

La manera más sencilla de generar los PDF es ejecutar `make` en la carpeta `apuntes` del repositorio. Aparecerán todos en la subcarpeta `pdf`.

El script `nbcheck.py` permite ejecutar y actualizar el cuaderno sin abrirlo en Jupyter, hacer comprobación de tipos con [mypy](https://mypy-lang.org), comprobar la ortografía y gramática con [textidote](https://github.com/sylvainhalle/textidote) o reducir las imágenes del cuaderno. Es necesario tener instalado el paquete [nbconvert](https://github.com/jupyter/nbconvert) de Jupyter además de las herramientas citadas en cada caso. La forma de usarlo se describe pasando la opción `--help`.

### Licencia

Los apuntes están sujetos a la licencia [Creative Commons BY-NC-SA](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.es) y el código Python a la licencia [GPLv3](https://www.gnu.org/licenses/gpl-3.0.txt).