# -*- coding: utf-8 -*-
#
# Fracción
# Rubén Rubio (Universidad Complutense de Madrid) 2023
#

import math


class Fracción:
    """Fracción de números enteros"""

    # Enumera los atributos con __slots__ para evitar erratas
    # desapercibidas (no es necesario usar __slots__ ni siquiera
    # conocerlo, pero puede venir bien para evitar esos errores)
    __slots__ = ('_numerador', '_denominador')

    def __init__(self, numerador: int, denominador: int=1):

        # El divisor no puede ser cero
        if denominador == 0:
            raise ZeroDivisionError

        # Los atributos (la representación interna) de la Fracción son
        # un numerador y un denominador. Indicamos con la barra baja que
        # no queremos que se acceda a esos atributos desde fuera porque
        # queremos mantener la irreducibilidad de la fracción que no es
        # compatible con modificaciones arbitrarias de estos atributos.
        self._numerador = numerador
        self._denominador = denominador

        # Normaliza la fracción en forma irreducible
        self._normalizar()

    def _normalizar(self):
        """Normaliza la fracción en forma irreducible"""

        # El denominador siempre es positivo, el numerador lleva el signo
        if self._denominador < 0:
            self._denominador = -self._denominador
            self._numerador = -self._numerador

        # Numerador y denominador son coprimos, i.e. la fracción es irreducible
        mcd = math.gcd(self._numerador, self._denominador)
        self._numerador //= mcd
        self._denominador //= mcd

    def __eq__(self, otra):
        """Compara si dos Fracciónes son iguales"""

        # Como la fracción está siempre en forma irreducible con el
        # denominador positivo, que es única, la comparación es trivial
        return isinstance(otra, Fracción) and \
               self._denominador == otra._denominador and \
               self._numerador == otra._numerador

    def get_denominador(self) -> int:  # el clásico getter
        return self._denominador

    def get_numerador(self) -> int:
        return self._numerador

    def set_denominador(self, n: int):
        # No deja poner el denominador a cero
        if n == 0:
            raise ZeroDivisionError
        # Asigna el denominador, pero luego normaliza
        self._denominador = n
        self._normalizar()

    def set_numerador(self, n: int):
        # Asigna el numerador, pero luego normaliza
        self._numerador = n
        self._normalizar()

    def a_float(self) -> float:
        return self._numerador / self._denominador

    def suma(self, otra: 'Fracción') -> 'Fracción':
        """Suma esta fracción con otra"""
        nuevo_numerador = self._numerador * otra._denominador + otra._numerador * self._denominador
        nuevo_denominador = self._denominador * otra._denominador

        return Fracción(nuevo_numerador, nuevo_denominador)

    def suma2(self, otra: 'Fracción') -> 'Fracción':
        """Suma esta fracción con otra (más inteligentemente)"""
        # Tomando el máximo común múltiplo no es necesario obtener
        # un número tan grande como el producto de denominadores
        mcm = math.lcm(self._denominador, otra._denominador)
        numerador_resultado = self._numerador * (mcm // self._denominador) + \
                              otra._numerador * (mcm // otra._denominador)
        denominador_resultado = mcm
        return Fracción(numerador_resultado, denominador_resultado)

    def inversa(self) -> 'Fracción':
        """Inversa de la fracción actual"""
        return Fracción(self._denominador, self._numerador)

    def producto(self, otra: 'Fracción') -> 'Fracción':
        """Producto de la fracción actual con otra"""
        return Fracción(self._numerador * otra.get_numerador(),  # usamos get_numerador para variar
                        self._denominador * otra.get_denominador())

    def cociente(self, otra: 'Fracción') -> 'Fracción':
        """Cociente de esta fracción entre otra"""
        return self.producto(otra.inversa())

        # Otra posibilidad (que reutiliza menos, pero es válida)
        # return Fracción(self.numerador * otra.get_denominador(),
        #                 self.denominador * otra.get_numerador())

    def __repr__(self):  # lo que sale con repr(fracción) y en la consola de Python
        """Representación textual del objeto (invertible)"""
        return f'Fracción({self._numerador}, {self._denominador})'

    def __str__(self):  # lo que sale con str(fracción) y con print
        """Representación textual del objeto (más legible)"""
        if self._denominador == 1:
            return str(self._numerador)
        else:
            return f'{self._numerador}/{self._denominador}'

    # Asigna nombres de método especiales de Python para poder usar
    # los operadores aritméticos habituales (podríamos haber usado
    # estos nombres directamente en la definición del método)
    __add__ = suma2
    __mul__ = producto
    __truediv__ = cociente
    __float__ = a_float

    # [Extra] Una alternativa más elegante a los métodos getter y setter
    # utilizada en muchos lenguajes de programación modernos (Python, C#,
    # Kotlin, Object Pascal, Scala, Swift, Vala, etc) son las propiedades.
    # No es necesario conocerlas ni usarlas, pero las usaremos aquí como
    # anécdota. Una propiedad se utiliza como un atributo, pero su lectura
    # implica la llamada a un método getter y su asignación la llamada a un
    # método setter. El método de lectura se indica con el decorador
    # @property y el de asignación con @<nombre de la propiedad>.setter.

    @property
    def denominador(self):
        return self._denominador

    @denominador.setter
    def denominador(self, valor):
        # Si hubiéramos definido la propiedad desde el principio,
        # el código de set_denominador iría aquí
        self.set_denominador(valor)


# Ejemplos
if __name__ == '__main__':
    x = Fracción(4, 6)
    y = Fracción(7, 12)

    print(x)
    print(x.get_numerador())
    print(x.denominador)  # [extra] propiedad
    print(x._denominador)  # no deberíamos acceder así
    print(x.a_float())
    print(float(x))

    print('Operaciones aritméticas')
    print(x.suma(y))
    print(x + y)
    print(x.producto(y))
    print(x * y)
    print(x.inversa())
    print(x.cociente(y))
    print(x / y)

    print('Igualdad de fracciones')
    print(Fracción(2, 3) == Fracción(4, 6))

    print('Asignación de atributos')

    y.set_numerador(8)
    print(y)
    y.denominador = 2  # [extra] propiedad (no se está asignando directamente el atributo)
    print(y)
