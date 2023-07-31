# -*- coding: utf-8 -*-
#
# Ejemplo de herencia con la jerarquía de clases de un juego
# Rubén Rubio (Universidad Complutense de Madrid) 2023
#

import random
import sys


#
# Inicio de la jerarquía de clases
#

class ObjetoJuego:
	"""Superclase común a todos los objetos del juego"""

	def turno(self, juego):
		"""
		Método que se llamará en cada turno del juego para que el objeto
		se actualice. Esta actualización podría necesitar información del
		juego o realizar cambios en él, así que lo recibe como argumento.
		El valor de retorno False indica que el objeto ha de ser destruido.
		"""

		# no hace nada a este nivel, pero documenta
		# una posibilidad para sus herederos
		return True


class ObjetoEfímero(ObjetoJuego):  # así se indica que una clase hereda de otra
	"""Objeto que desaparece pasado un tiempo"""

	def __init__(self, tiempo):
		super().__init__()  # llama al constructor de la clase madre
		self.tiempo = tiempo  # tiempo que dura el objeto

	def turno(self, juego):
		self.tiempo -= 1
		return self.tiempo > 0  # sobrevive si le queda tiempo


class ObjetoVisible(ObjetoJuego):
	"""Objeto visible en el mapa"""

	def __init__(self, x: int, y: int):
		# El constructor del objeto padre se puede invocar explícitamente
		# en lugar de usando super (de hecho aquí es necesario por
		# detalles es preferible obviar)
		ObjetoJuego.__init__(self)
		# Posición del objeto en el mapa
		self.x = x
		self.y = y

	def _pintar_icono(self, icono: str):
		"""Pinta un icono (carácter) en la posición del objeto"""

		# Esta es una función auxiliar que las subclases podrán
		# utilizar para implementar su pintar. Empieza con una
		# barra baja porque no está pensada para usarse desde fuera.

		# Para pintar el icono en la posición del objeto usa el
		# «archivo» de la salida estándar sys.stdout. El texto entre
		# \x1b y H es una secuencia de escape ANSI para colocar el
		# cursor en una posición dada. Hay múltiples de estos comandos
		# para distintas opciones del terminal, que por supuesto no
		# hace falta conocer en absoluto.
		sys.stdout.write(f'\x1b[{self.y + 1};{self.x + 1}H{icono}')

	def _mover(self, dirección: str, juego):
		"""Mueve el personaje en la dirección dada si está libre"""

		# La dirección es alguna de las letras asdw para designar
		# respectivamente izquierda, abajo, derecha, arriba

		x, y = self.x, self.y

		if dirección == 'a':
			x -= 1
		elif dirección == 's':
			y += 1
		elif dirección == 'd':
			x += 1
		elif dirección == 'w':
			y -= 1

		# Se mueve solo si es transitable
		if juego.es_transitable(x, y, self):
			self.x, self.y = x, y
			return True

		return False

	def pintar(self):
		"""Pinta el objeto en el mapa"""
		# Todo objeto visible se ha de poder pintar, así que las clases que
		# hereden de esta tienen que asegurarse de redefinir el método. Si
		# no lo hacen se mostrará el siguiente error al llamarlo.
		raise NotImplementedError('has de redefinir el método pintar')

	def activar(self, causante: ObjetoJuego):
		"""Activa el objeto y desencadena su acción"""
		# En cambio, aquí asumimos que la acción por defecto del objeto al
		# activarlo es no hacer nada (si alguna clase quiere hacer algo
		# redefinirá este método). El causante es el objeto que activa la
		# acción (en nuestro caso siempre Ash).
		pass


class Temporizador(ObjetoEfímero):
	"""Temporizador que desencadena una acción pasado un tiempo"""

	def __init__(self, tiempo, acción):
		super().__init__(tiempo)  # constructor de ObjetoEfímero
		self.acción = acción  # acción que se ejecutará

	def turno(self, juego):
		# Llama al turno de la clase madre ObjetoEfímero
		sigue_vivo = super().turno(juego)

		# Si se ha pasado el tiempo ejecuta la acción
		if not sigue_vivo:
			self.acción()

		return sigue_vivo


class Ash(ObjetoVisible):
	"""Ash Ketchum, de Pueblo Paleta (el protagonista)"""

	def __init__(self, x, y):
		super().__init__(x, y)  # llama al constructor de ObjetoVisible
		self.puntos = 0  # puntos que ha ganado el personaje

	def pintar(self):
		self._pintar_icono('👦' if USA_EMOJI else '\x1b[1mA\x1b[0m')

	def actúa(self, comando: str, juego):
		"""Envía un comando (tecla pulsada) al protagonista"""
		if comando in 'asdw':
			self._mover(comando, juego)


class Señora(ObjetoVisible):
	"""Personaje que se mueve aleatoriamente por el mapa"""

	def __init__(self, x, y):
		super().__init__(x, y)
		self.dirección = 'a'  # dirección de movimiento actual

	def turno(self, juego):
		# Se mueve en su turno hacia donde le viene en gana cada vez
		# aunque cambia de dirección con probabilidad 1/3
		if random.random() < 1/3:
			self.dirección = random.choice('asdw')
		self._mover(self.dirección, juego)

		return True  # es inmortal

	def pintar(self):
		self._pintar_icono('👩' if USA_EMOJI else 'S')


class Abeto(ObjetoVisible):
	"""Abeto"""

	def __init__(self, x, y):
		super().__init__(x, y)

	def pintar(self):
		self._pintar_icono('🌲' if USA_EMOJI else '\x1b[32mT\x1b[0m')


class Moneda(ObjetoVisible, ObjetoEfímero):
	"""Moneda que da puntos al capturarla"""

	# Ejemplo de herencia múltiple (sin embargo, es un ejemplo algo
	# inconveniente porque hay «herencia en diamante», es decir,
	# Moneda es ObjetoJuego por dos caminos distintos en la jerarquía
	# de clases y eso puede causar algunos problemas).

	def __init__(self, x, y, tiempo, puntos):
		# No hay una única clase madre, así que no se puede usar
		# super (sí se puede usar, pero no convenientemente)
		ObjetoEfímero.__init__(self, tiempo)
		ObjetoVisible.__init__(self, x, y)
		self.puntos = puntos  # puntos que aporta la moneda

	def pintar(self):
		self._pintar_icono('🪙' if USA_EMOJI else 'O')

	def activar(self, causante: ObjetoJuego):
		# Añade los puntos de la moneda a quien la coja
		causante.puntos += self.puntos
		# Pierde los puntos que tenía
		self.puntos = 0
		# Hace que la actualización la destruya
		self.tiempo = 0


#
# Fin de la jerarquía de clases
#

#
# Lo que sigue es código un poco enrevesado para que el juego funcione.
# La única parte interesante es Juego.juega donde se trata de forma
# polimórfica a los objetos.
#

# Activa o desactiva los emojis
USA_EMOJI = False


class Getch:
	"""
	Clase para leer un único carácter desde la consola sin bloqueo.

	Mejor no mirar esta clase porque tiene detalles irrelevantes del
	tratamiento de la terminal en distintos sistemas operativos. La
	necesidad de incluirla es que la lectura normal de consola requiere
	pulsar intro para obtener lo leído y eso es poco práctico en un juego.
	"""

	def __init__(self):
		self.extra = None

		try:
			# Para Windows
			import msvcrt
			self.module = msvcrt
			self.get = self._windows

		except ImportError:
			# Para Unix-like (Linux, macOS, etc)
			import termios, tty
			self.module = termios
			# Configura el terminal para leer caracter a caracter
			fd = sys.stdin.fileno()
			self.extra = (fd, termios.TCSADRAIN, termios.tcgetattr(fd))
			tty.setraw(fd)
			self.get = self._unix

	def _windows(self):
		return self.module.getch()

	def _unix(self):
		return sys.stdin.read(1)

	def __del__(self):
		if self.extra:
			# Devuelve el terminal a su configuración original
			self.module.tcsetattr(*self.extra)


class Juego:
	"""Clase que controla el juego"""

	# Constantes (aunque nada impide modificarlas
	# en ejecución, son atributos de la clase)
	ANCHO = 50
	ALTO = 20

	def __init__(self):
		# Protagonista del juego
		self.prota = Ash(self.ANCHO // 2, self.ALTO // 2)

		# Lista de todos los objetos del juego de tipo ObjetoVisible
		# (independientemente de su tipo particular)
		self.objs = [
			self.prota,
			Señora(self.ANCHO // 3, self.ALTO // 3),
			Moneda(self.ANCHO // 5, 4 * self.ALTO // 5, 25, 20),
		]

		self._añade_abetos()

		# Crea también objetos no visibles
		self.objs_extra = [
			Temporizador(30, self._nueva_moneda),
		]

		# Objeto para leer caracteres de la entrada
		self.getch = Getch()

	def _añade_abetos(self):
		"""Añade abetos en el perímetro del mapa"""

		for y in (0, self.ALTO - 1):
			for x in range(1, self.ANCHO - 1):
				self.objs.append(Abeto(x, y))

		for x in (0, self.ANCHO - 1):
			for y in range(self.ALTO):
				self.objs.append(Abeto(x, y))

	def _nueva_moneda(self):
		"""Añade una nueva moneda en posición aleatoria"""

		# No comprobamos si está ocupada, pero bueno...
		x = random.randint(1, self.ANCHO - 1)
		y = random.randint(1, self.ALTO - 1)

		self.objs.append(Moneda(x, y, 25, 20))

	def es_transitable(self, x, y, causante):
		"""Comprueba si una casilla es transitable o activable"""

		# Ineficientemente busca en todos los objetos del juego
		for obj in self.objs:
			if obj.x == x and obj.y == y:
				obj.activar(causante)
				return False

		return True

	def juega(self):
		"""Bucle del juego"""

		# Última tecla leída y ciclo del juego actual
		tecla, ciclo = 'x', 0

		# Se sale pulsando la q
		while tecla != 'q':
			# Limpia la pantalla entera
			sys.stdout.write('\x1b[2J')

			# Pinta los objetos del juego
			# (véase el polimorfismo, los tratamos a todos igual
			# independientemente de su tipo concreto)
			for obj in self.objs:
				obj.pintar()

			# Escribe la puntuación y otra información
			sys.stdout.write(f'\x1b[{self.ALTO + 2};0HPuntos: {self.prota.puntos}')
			sys.stdout.write(f'\n\rCiclo: {ciclo}')
			sys.stdout.write('\n\rASDW para moverse, Q para salir')

			# Refresca la pantalla
			sys.stdout.flush()

			# Lee una tecla del terminal (lo repite hasta que sea válida)
			tecla = self.getch.get()

			while tecla not in 'asdwq':
				tecla = self.getch.get()

			# Envía la tecla al personaje principal para que actúe en consecuencia
			self.prota.actúa(tecla, juego)

			# Actualiza los objetos del juego
			# (véase el polimorfismo, no nos preocupamos de su tipo particular)
			borrables = set()

			for obj in self.objs + self.objs_extra:
				if not obj.turno(self):
					borrables.add(obj)

			# Elimina los objetos que han muerto en este turno
			if borrables:
				self.objs = [obj for obj in self.objs if obj not in borrables]
				self.objs_extra = [obj for obj in self.objs_extra if obj not in borrables]

			# Aumenta el número de ciclo
			ciclo += 1


if __name__ == '__main__':
	# Crea una instancia del juego y lo ejecuta
	juego = Juego()
	juego.juega()
