# coding: utf-8
#
# Matriz como clase propia
# Rubén Rubio (Universidad Complutense de Madrid) 2023
#

#
# En el tema de matrices y en la hoja de problemas 4 programamos funciones
# que operaban con matrices y utilizabamos las listas de listas como si
# fueran un nuevo tipo de datos. Sin embargo, esas matrices no eran formalmente
# un tipo distinto del de las listas que usábamos para representarlas. Ahora
# formalizamos esto mediante la definición de una clase Matriz que reúna las
# operaciones que vimos en clase y conserve la representación asegurando su corrección.

class Matriz:
    """Matriz"""

    def __init__(self, elems: list[list], fiable=False):
        # Comprobamos que la lista de listas que se pasa representa
        # una matriz válida (salvo que venga de un origen fiable, como
        # de la propia clase)
        if not fiable:
            válida, error = Matriz._matriz_válida(elems)
            if not válida:
                raise ValueError(f'matriz no válida: {error}')

            # Hace una copia profunda para evitar interferencias desde el
            # exterior (pero solo de la lista de filas y de cada fila,
            # porque lo que haya en cada posición de la matriz no es de
            # interés a esta clase)
            elems = [fila.copy() for fila in elems]

        self._elems = elems

    @staticmethod
    def constante(n: int, m: int, v: int):
        return Matriz([[v] * m for _ in range(n)])

    @staticmethod
    def _matriz_válida(A):
        """Comprueba si una matriz es válida"""

        if type(A) != list:
            return False, 'el objeto no es una lista'

        if len(A) == 0:
            return False, 'el objeto es una lista vacía'

        # Usa expresiones generadores, pero podría ser un bucle
        if any(type(fila) != list for fila in A):
            return False, 'alguna de las filas no es una lista'

        if len(A[0]) == 0:
            return False, 'la primera fila está vacía'

        # Usa un bucle para variar
        for k, fila in enumerate(A):
            if len(fila) != len(A[0]):
                return False, f'la fila {k}-ésima tiene un tamaño dispar'

        # Todas las filas son objetos distintos
        if len({id(fila) for fila in A}) != len(A):
            return False, 'hay filas repetidas en A'

        return True, 'es una matriz'

    def orden(self):
        """Orden de esta matriz"""

        return len(self._elems), len(self._elems[0])

    def __add__(self, B):
        """Matriz suma de dos matrices (como objeto nuevo)"""

        alto, ancho = self.orden()

        return Matriz([[self._elems[i][j] + B._elems[i][j]
                        for j in range(ancho)]
                       for i in range(alto)], fiable=True)

    def suma_insitu(self, B):
        """Suma B sobre esta matriz"""

        alto, ancho = self.orden()

        for i in range(alto):
            for j in range(ancho):
                self._elems[i][j] += B._elems[i][j]

    # Un sinónimo para suma_insitu que permite usar el operador +=
    # (se pueden definir variables en el ámbito de la clase, aunque no es
    # buena práctica salvo que vayan a actuar como constantes, es el caso)
    __iadd__ = suma_insitu

    def __repr__(self):
        """Muestra como texto el objeto"""

        fila_str = []

        for fila in self._elems:
            fila_str.append(' '.join(map(str, fila)))

        return '\n'.join(fila_str)

    def get(self, i: int, j: int):
        """Obtiene el elemento ij"""

        return self._elems[i][j]

    def set(self, i: int, j: int, v):
        """Obtiene el elemento ij"""

        self._elems[i][j] = v

    def __getitem__(self, pos: tuple[int, int]):
        """Accede a la matriz con los corchetes"""

        return self.get(pos[0], pos[1])

    def __setitem__(self, pos: tuple[int, int], valor):
        """Asigna a la matriz con los corchetes"""

        return self.set(pos[0], pos[1], valor)

    def __eq__(self, otra):
        """Compara si dos matrices son la misma"""

	# Si no definimos esto, la comparación funciona como id(self) ==
	# id(otra), es decir, comprueba que sea exactamente el mismo objeto.
        return self._elems == otra._elems


m = Matriz.constante(3, 3, 1)

print(m)
print(m + m)
print(m[1, 1])

m[1, 1] = 5
print(m)
