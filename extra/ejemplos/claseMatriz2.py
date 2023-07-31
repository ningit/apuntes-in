# coding: utf-8
#
# Matriz como clase propia (representación aplanada)
# Rubén Rubio (Universidad Complutense de Madrid) 2023
#


class Matriz:
    """Matriz como lista plana"""

    def __init__(self, elems, ancho):
        # Lista plana de todos los elementos
        self._elems = list(elems)
        # Ancho de cada fila
        self._ancho = ancho

        if len(self._elems) % ancho != 0:
            raise ValueError('el ancho dado no es divisor del número total de elementos')

    @staticmethod
    def constante(n, m, v):
        return Matriz([v] * (n * m), m)

    def orden(self):
        """Orden de una matriz"""

        return len(self._elems) // self._ancho, self._ancho

    def __add__(self, B):
        """Matriz suma de dos matrices"""

        alto, ancho = self.orden()

        if B.orden() != (alto, ancho):
            raise ValueError('matrices de dimensiones distintas en la suma (se esperaba {alto}x{ancho})')

        return Matriz([self._elems[i] + B._elems[i] for i in range(len(self._elems))], ancho)

    def suma_insitu(self, B):
        """Suma B sobre esta matriz"""

        alto, ancho = self.orden()

        if B.orden() != (alto, ancho):
            raise ValueError('matrices de dimensiones distintas en la suma (se esperaba {alto}x{ancho})')

        for k, elem in enumerate(B._elems):
            self._elems[k] += elem

        return self

    # Un sinónimo para suma_insitu que permite usar el operador +=
    __iadd__ = suma_insitu

    def __repr__(self):
        """Muestra como texto el objeto"""

        matriz_str = ''

        for k, elem in enumerate(self._elems):
            if k > 0 and k % self._ancho == 0:
                matriz_str += '\n'

            matriz_str += str(elem) + ' '

        return matriz_str

    def get(self, i, j):
        """Obtiene el elemento ij"""

        return self._elems[i * self._ancho + j]

    def set(self, i, j, v):
        """Obtiene el elemento ij"""

        self._elems[i * self._ancho + j] = v

    def __getitem__(self, pos):
        """Accede a la matriz con los corchetes"""

        return self.get(pos[0], pos[1])

    def __setitem__(self, pos, valor):
        """Asigna a la matriz con los corchetes"""

        return self.set(pos[0], pos[1], valor)

    def __eq__(self, otra):
        """Compara si dos matrices son la misma"""

        return self._ancho == otra._ancho and self._elems == otra._elems

    @property
    def ancho(self):
        return self._ancho

    @ancho.setter
    def ancho(self, valor):
        if len(self._elems) % valor != 0:
            raise ValueError('el ancho dado no es divisor del número total de elementos')
        self._ancho = valor

m = Matriz.constante(3, 3, 1)

print(m)
print(m + m)
print(m[1, 1])

m[1, 1] = 5
print(m)
