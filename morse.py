"""
NOMBRE: [Completar]
BOLETA: [Completar]
GRUPO:  [Completar]
FECHA:  [Completar]

Proyecto Final - Teoria de la Computacion
Maquina de Turing: Traductor Texto -> Morse

Este modulo implementa, en Programacion Orientada a Objetos, el subconjunto
Q_control U Q_texto->morse de la maquina de Turing formal

    M = (Q, Sigma, Gamma, delta, q0, B, F)

descrita en el documento de definicion del proyecto, para traducir una
cadena de texto en mayusculas a su equivalente en codigo Morse.

Disposicion de la cinta (segun el modelo formal):

    [ENTRADA EN TEXTO, con letras ya leidas marcadas con ']  #  [SALIDA MORSE]

Idea de la maquina:
  - El cabezal recorre la zona de ENTRADA buscando la siguiente letra que
    no este marcada (')
  - Al encontrarla, la marca (A -> A') para registrar que ya fue leida.
  - Viaja a la derecha hasta el delimitador # (si no existe, lo crea al
    llegar al primer blanco) y hasta el final de lo ya escrito en Morse.
  - Escribe ahi la secuencia de puntos/rayas (o '/' si era un espacio),
    seguida de un espacio separador, y regresa al inicio de la cinta para
    repetir la busqueda.
  - Cuando ya no quedan letras sin marcar en la entrada, pasa a
    q_limpieza, que descarta la zona de entrada y el delimitador, dejando
    unicamente el resultado en Morse -> q_f.
"""

from enum import Enum


class Direccion(Enum):
    IZQUIERDA = "L"
    DERECHA = "R"


# ---------------------------------------------------------------------------
# Cinta
# ---------------------------------------------------------------------------
class Cinta:
    """
    Representa la cinta infinita (Gamma) de la maquina de Turing.

    Se implementa con un diccionario {posicion: simbolo} -en vez de una
    lista- para simular una cinta infinita en ambas direcciones sin
    reservar memoria de mas. Cualquier posicion no escrita se considera
    el simbolo blanco B.
    """

    BLANCO = "B"

    def __init__(self, entrada: str = ""):
        self._celdas = {i: s for i, s in enumerate(entrada)}
        self.cabezal = 0
        self._min_usado = 0
        self._max_usado = max(len(entrada) - 1, 0)

    def leer(self) -> str:
        return self._celdas.get(self.cabezal, self.BLANCO)

    def leer_en(self, posicion: int) -> str:
        return self._celdas.get(posicion, self.BLANCO)

    def escribir(self, simbolo: str) -> None:
        self._celdas[self.cabezal] = simbolo
        self._min_usado = min(self._min_usado, self.cabezal)
        self._max_usado = max(self._max_usado, self.cabezal)

    def mover(self, direccion: Direccion) -> None:
        self.cabezal += 1 if direccion is Direccion.DERECHA else -1

    def ir_a(self, posicion: int) -> None:
        self.cabezal = posicion

    def primer_blanco_desde(self, inicio: int) -> int:
        """Devuelve la primera posicion >= inicio cuyo simbolo es BLANCO."""
        pos = inicio
        while pos in self._celdas:
            pos += 1
        return pos

    def a_string(self) -> str:
        """Devuelve el contenido relevante de la cinta (sin blancos sobrantes)."""
        if self._max_usado < self._min_usado:
            return ""
        return "".join(
            self._celdas.get(i, self.BLANCO)
            for i in range(self._min_usado, self._max_usado + 1)
        )


# ---------------------------------------------------------------------------
# Maquina de Turing: Texto -> Morse
# ---------------------------------------------------------------------------
class MaquinaTuringTextoMorse:
    """
    Implementa Q_control U Q_texto->morse para el sentido Texto -> Morse.
    """

    DELIMITADOR = "#"
    SEP_LETRA = " "      # separa los simbolos Morse de letras distintas
    SEP_PALABRA = "/"    # separa palabras completas en la salida Morse
    MARCA = "'"          # sufijo que indica "ya procesado"

    TABLA_MORSE = {
        "A": ".-",    "B": "-...",  "C": "-.-.",  "D": "-..",
        "E": ".",     "F": "..-.",  "G": "--.",   "H": "....",
        "I": "..",    "J": ".---",  "K": "-.-",   "L": ".-..",
        "M": "--",    "N": "-.",    "O": "---",   "P": ".--.",
        "Q": "--.-",  "R": ".-.",   "S": "...",   "T": "-",
        "U": "..-",   "V": "...-",  "W": ".--",   "X": "-..-",
        "Y": "-.--",  "Z": "--..",
    }

    # Estados de Q_control U Q_texto->morse
    Q0 = "q0"
    Q_BUSCAR = "q_buscar_letra"      # busca la siguiente letra sin marcar
    Q_FINAL_ENTRADA = "q_final_entrada"  # localiza/crea el delimitador #
    Q_ESCRIBIR = "q_escribir_morse"  # escribe la secuencia Morse
    Q_LIMPIEZA = "q_limpieza"        # descarta la entrada ya traducida
    Q_F = "q_f"                      # estado de aceptacion

    def __init__(self, texto: str, verbose: bool = False):
        texto = texto.upper().strip()
        self._validar_entrada(texto)

        self.entrada_len = len(texto)
        self.cinta = Cinta(texto)
        self.estado = self.Q0
        self.verbose = verbose
        self.pasos = 0
        self._letra_actual = None
        self._pos_busqueda = 0  # posicion donde retomar la busqueda

    # -- Validacion ---------------------------------------------------------
    def _validar_entrada(self, texto: str) -> None:
        for caracter in texto:
            if caracter != " " and caracter not in self.TABLA_MORSE:
                raise ValueError(
                    f"Simbolo '{caracter}' no pertenece al alfabeto de "
                    f"entrada (Sigma) para el sentido texto->morse."
                )
        if not texto:
            raise ValueError("La cadena de entrada no puede estar vacia.")

    # -- Ejecucion ------------------------------------------------------------
    def ejecutar(self) -> str:
        """
        Corre la maquina desde q0 hasta q_f, aplicando delta paso a paso,
        y devuelve la cadena en codigo Morse resultante.
        """
        self.estado = self.Q_BUSCAR

        limite_pasos = 100_000  # red de seguridad anti-loop-infinito
        while self.estado != self.Q_F and self.pasos < limite_pasos:
            self._delta()
            self.pasos += 1
            if self.verbose:
                self._traza()

        if self.pasos >= limite_pasos:
            raise RuntimeError("La maquina no se detuvo (posible ciclo).")

        return self._resultado_morse()

    # -- Funcion de transicion delta -------------------------------------------
    def _delta(self) -> None:
        """
        Despacha el comportamiento segun el estado actual. Cada rama
        mueve el cabezal y/o escribe en la cinta, tal como exige
        delta: Q x Gamma -> Q x Gamma x {L, R}.
        """
        despachador = {
            self.Q_BUSCAR: self._estado_buscar_letra,
            self.Q_FINAL_ENTRADA: self._estado_final_entrada,
            self.Q_ESCRIBIR: self._estado_escribir_morse,
            self.Q_LIMPIEZA: self._estado_limpieza,
        }
        funcion = despachador.get(self.estado)
        if funcion is None:
            raise RuntimeError(f"Estado no reconocido: {self.estado}")
        funcion()

    def _estado_buscar_letra(self) -> None:
        """
        q_buscar_letra: recorre la zona de entrada (posiciones
        0..entrada_len-1) buscando el primer simbolo sin marcar.
        - Si lo encuentra: lo marca y pasa a q_final_entrada para
          ir a escribir su Morse equivalente.
        - Si ya no hay simbolos sin marcar: pasa a q_limpieza.
        """
        self.cinta.ir_a(self._pos_busqueda)
        simbolo = self.cinta.leer()

        if self._pos_busqueda >= self.entrada_len:
            self.estado = self.Q_LIMPIEZA
            return

        if simbolo.endswith(self.MARCA):
            # ya procesado, seguimos buscando a la derecha
            self._pos_busqueda += 1
            return

        # Letra (o espacio) sin procesar todavia
        self._letra_actual = simbolo
        self.cinta.escribir(simbolo + self.MARCA)
        self._pos_busqueda += 1
        self.estado = self.Q_FINAL_ENTRADA

    def _estado_final_entrada(self) -> None:
        """
        q_final_entrada: ubica el delimitador #. Si todavia no existe
        (primera letra traducida), lo crea justo despues de la entrada.
        """
        pos_delim = self.entrada_len
        if self.cinta.leer_en(pos_delim) != self.DELIMITADOR:
            self.cinta.ir_a(pos_delim)
            self.cinta.escribir(self.DELIMITADOR)

        # Avanza hasta el primer blanco despues del delimitador:
        # ahi termina lo ya escrito en Morse y empieza a escribir.
        destino = self.cinta.primer_blanco_desde(pos_delim + 1)
        self.cinta.ir_a(destino)
        self.estado = self.Q_ESCRIBIR

    def _estado_escribir_morse(self) -> None:
        """
        q_escribir_morse: escribe, simbolo por simbolo, el codigo Morse
        (o '/' si la letra marcada era un espacio) correspondiente,
        seguido de un espacio separador, avanzando siempre a la derecha.
        """
        if self._letra_actual == " ":
            secuencia = self.SEP_PALABRA
        else:
            secuencia = self.TABLA_MORSE[self._letra_actual]

        for simbolo in secuencia:
            self.cinta.escribir(simbolo)
            self.cinta.mover(Direccion.DERECHA)
        self.cinta.escribir(self.SEP_LETRA)

        self.estado = self.Q_BUSCAR

    def _estado_limpieza(self) -> None:
        """
        q_limpieza: no se necesita modificar la cinta paso a paso aqui;
        basta con marcar que terminamos. El resultado se extrae en
        _resultado_morse() leyendo solo la zona posterior al delimitador.
        """
        self.estado = self.Q_F

    # -- Resultado / utilidades -------------------------------------------------
    def _resultado_morse(self) -> str:
        contenido = self.cinta.a_string()
        _, _, salida = contenido.partition(self.DELIMITADOR)
        return salida.strip()

    def cinta_completa(self) -> str:
        """Devuelve la cinta completa (entrada marcada + # + salida)."""
        return self.cinta.a_string()

    def _traza(self) -> None:
        print(f"[paso {self.pasos:>3}] estado={self.estado:<20} "
              f"cabezal={self.cinta.cabezal:<4} cinta={self.cinta.a_string()!r}")


class MaquinaTuringMorseTexto:
    """
    Implementa Q_control U Q_morse->texto para el sentido Morse -> Texto.
    """

    DELIMITADOR = "#"
    SEP_LETRA = " "
    MARCA = "'"

    TABLA_MORSE = {
        "A": ".-",    "B": "-...",  "C": "-.-.",  "D": "-..",
        "E": ".",     "F": "..-.",  "G": "--.",   "H": "....",
        "I": "..",    "J": ".---",  "K": "-.-",   "L": ".-..",
        "M": "--",    "N": "-.",    "O": "---",   "P": ".--.",
        "Q": "--.-",  "R": ".-.",   "S": "...",   "T": "-",
        "U": "..-",   "V": "...-",  "W": ".--",   "X": "-..-",
        "Y": "-.--",  "Z": "--..",
    }
    TABLA_TEXTO = {codigo: letra for letra, codigo in TABLA_MORSE.items()}
    TABLA_TEXTO["/"] = " "

    # Estados de Q_control U Q_morse->texto
    Q0 = "q0"
    Q_BUSCAR = "q_buscar_codigo"
    Q_LEER = "q_leer_codigo"
    Q_FINAL_ENTRADA = "q_final_entrada"
    Q_ESCRIBIR = "q_escribir_texto"
    Q_LIMPIEZA = "q_limpieza"
    Q_F = "q_f"

    def __init__(self, morse: str, verbose: bool = False):
        morse = morse.strip()
        self._validar_entrada(morse)

        self.entrada_len = len(morse)
        self.cinta = Cinta(morse)
        self.estado = self.Q0
        self.verbose = verbose
        self.pasos = 0
        self._codigo_actual = ""
        self._pos_busqueda = 0

    # -- Validacion ---------------------------------------------------------
    def _validar_entrada(self, morse: str) -> None:
        """Valida que la entrada solo contenga simbolos Morse aceptados."""
        for caracter in morse:
            if caracter not in {".", "-", "/", " "}:
                raise ValueError(
                    f"Simbolo '{caracter}' no pertenece al alfabeto de "
                    f"entrada (Sigma) para el sentido morse->texto."
                )
        if not morse:
            raise ValueError("La cadena de entrada no puede estar vacia.")

    # -- Ejecucion ------------------------------------------------------------
    def ejecutar(self) -> str:
        """Corre la maquina hasta q_f y devuelve la traduccion a texto."""
        self.estado = self.Q_BUSCAR

        limite_pasos = 100_000  # red de seguridad anti-loop-infinito
        while self.estado != self.Q_F and self.pasos < limite_pasos:
            self._delta()
            self.pasos += 1
            if self.verbose:
                self._traza()

        if self.pasos >= limite_pasos:
            raise RuntimeError("La maquina no se detuvo (posible ciclo).")

        return self._resultado_texto()

    # -- Funcion de transicion delta -------------------------------------------
    def _delta(self) -> None:
        """Despacha el comportamiento segun el estado actual."""
        despachador = {
            self.Q_BUSCAR: self._estado_buscar_codigo,
            self.Q_LEER: self._estado_leer_codigo,
            self.Q_FINAL_ENTRADA: self._estado_final_entrada,
            self.Q_ESCRIBIR: self._estado_escribir_texto,
            self.Q_LIMPIEZA: self._estado_limpieza,
        }
        funcion = despachador.get(self.estado)
        if funcion is None:
            raise RuntimeError(f"Estado no reconocido: {self.estado}")
        funcion()

    def _estado_buscar_codigo(self) -> None:
        """
        q_buscar_codigo: recorre la entrada Morse en busca del inicio de una
        secuencia no procesada.
        """
        self.cinta.ir_a(self._pos_busqueda)

        if self._pos_busqueda >= self.entrada_len:
            self.estado = self.Q_LIMPIEZA
            return

        simbolo = self.cinta.leer()
        if simbolo == self.SEP_LETRA or simbolo == self.cinta.BLANCO:
            self._pos_busqueda += 1
            return

        if simbolo.endswith(self.MARCA):
            self._pos_busqueda += 1
            return

        self._codigo_actual = ""
        self.estado = self.Q_LEER

    def _estado_leer_codigo(self) -> None:
        """
        q_leer_codigo: acumula simbolos Morse hasta encontrar el separador
        de letra o un blanco.
        """
        simbolo = self.cinta.leer()

        if (simbolo == self.SEP_LETRA or simbolo == self.cinta.BLANCO
                or self.cinta.cabezal >= self.entrada_len):
            self.estado = self.Q_FINAL_ENTRADA
            return

        if simbolo == "/":
            self._codigo_actual = "/"
            self.cinta.escribir(simbolo + self.MARCA)
            self.cinta.mover(Direccion.DERECHA)
            self.estado = self.Q_FINAL_ENTRADA
            return

        self._codigo_actual += simbolo
        self.cinta.escribir(simbolo + self.MARCA)
        self.cinta.mover(Direccion.DERECHA)

        siguiente = self.cinta.leer()
        if (siguiente == self.SEP_LETRA or siguiente == self.cinta.BLANCO
                or self.cinta.cabezal >= self.entrada_len):
            self.estado = self.Q_FINAL_ENTRADA

    def _estado_final_entrada(self) -> None:
        """
        q_final_entrada: ubica el delimitador #. Si todavia no existe
        (primera letra traducida), lo crea justo despues de la entrada.
        """
        pos_delim = self.entrada_len
        if self.cinta.leer_en(pos_delim) != self.DELIMITADOR:
            self.cinta.ir_a(pos_delim)
            self.cinta.escribir(self.DELIMITADOR)

        destino = self.cinta.primer_blanco_desde(pos_delim + 1)
        self.cinta.ir_a(destino)
        self.estado = self.Q_ESCRIBIR

    def _estado_escribir_texto(self) -> None:
        """
        q_escribir_texto: convierte el codigo Morse acumulado a texto y lo
        escribe en la cinta de salida (zona posterior al delimitador #).
        """
        caracter = self.TABLA_TEXTO.get(self._codigo_actual)
        if caracter is None:
            raise ValueError(
                f"Codigo Morse '{self._codigo_actual}' no corresponde a ninguna letra."
            )

        self.cinta.escribir(caracter)
        self.estado = self.Q_BUSCAR

    def _estado_limpieza(self) -> None:
        """q_limpieza: finaliza la ejecucion sin modificar la cinta."""
        self.estado = self.Q_F

    # -- Resultado / utilidades -------------------------------------------------
    def _resultado_texto(self) -> str:
        contenido = self.cinta.a_string()
        _, _, salida = contenido.partition(self.DELIMITADOR)
        return salida

    def cinta_completa(self) -> str:
        """Devuelve la cinta completa (entrada Morse + # + salida texto)."""
        return self.cinta.a_string()

    def _traza(self) -> None:
        print(f"[paso {self.pasos:>3}] estado={self.estado:<20} "
              f"cabezal={self.cinta.cabezal:<4} cinta={self.cinta.a_string()!r}")


# ---------------------------------------------------------------------------
# Interfaz de alto nivel (la usara el modulo de integracion / main)
# ---------------------------------------------------------------------------
def texto_a_morse(texto: str, verbose: bool = False) -> str:
    """Funcion de conveniencia: traduce una cadena de texto a Morse."""
    maquina = MaquinaTuringTextoMorse(texto, verbose=verbose)
    return maquina.ejecutar()


def morse_a_texto(morse: str, verbose: bool = False) -> str:
    """Funcion de conveniencia: traduce una cadena en Morse a texto."""
    maquina = MaquinaTuringMorseTexto(morse, verbose=verbose)
    return maquina.ejecutar()


# ---------------------------------------------------------------------------
# Pruebas rapidas (ejemplo del enunciado: SOS -> ... --- ...)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    casos_prueba = [
        "SOS",
        "HOLA MUNDO",
        "IPN",
    ]

    for caso in casos_prueba:
        resultado = texto_a_morse(caso)
        print(f"Texto:  {caso}")
        print(f"Morse:  {resultado}")
        print("-" * 40)

    print("\nPruebas inversas:")
    casos_morse = [
        "... --- ...",
        ".... --- .-.. .- / -- ..- -. -.. ---",
        ".. .--. -.",
    ]

    for caso in casos_morse:
        resultado = morse_a_texto(caso)
        print(f"Morse:  {caso}")
        print(f"Texto:  {resultado}")
        print("-" * 40)
