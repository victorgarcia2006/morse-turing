# Máquina de Turing — Traductor Texto ↔ Morse

Proyecto Final · **Teoría de la Computación** · Unidad III
UPIIZ — Instituto Politécnico Nacional

> Implementación orientada a objetos de una Máquina de Turing transductora que traduce mensajes en lenguaje natural a código Morse, y realiza el proceso inverso.

---

## 📋 Tabla de contenidos

- [Descripción](#-descripción)
- [Fundamento teórico](#-fundamento-teórico)
- [Definición formal de la máquina](#-definición-formal-de-la-máquina)
- [Estructura del proyecto](#-estructura-del-proyecto)
- [Uso](#-uso)
- [Ejemplos](#-ejemplos)
- [Diseño orientado a objetos](#-diseño-orientado-a-objetos)
- [Autores](#-autores)

---

## 📖 Descripción

Una **Máquina de Turing (MT)** es un modelo matemático de computación propuesto por Alan Turing en 1936. Aunque es un dispositivo sencillo, define los límites de lo que una computadora física puede o no calcular.

Este proyecto implementa una MT de tipo **transductor**: utiliza la cinta para modificar la información de entrada y escribir un resultado, el enfoque exacto que requiere un traductor de código Morse.

La máquina puede operar en dos sentidos:

| Sentido | Entrada | Salida |
|---|---|---|
| Texto → Morse | `SOS` | `... --- ...` |
| Morse → Texto | `... --- ...` | `SOS` |

---

## 🧠 Fundamento teórico

La MT se puede imaginar a través de **tres componentes principales**:

1. **Una cinta infinita** — dividida en casillas, cada una con un símbolo de un alfabeto predefinido. Sirve como memoria de entrada, de trabajo y de salida.
2. **Un cabezal de lectura/escritura** — se posiciona sobre una sola casilla a la vez. Puede leer el símbolo actual, escribir uno nuevo encima, y moverse una posición a la izquierda o a la derecha.
3. **Un registro de estado** — almacena el estado interno actual. La función de transición decide qué hacer según el estado actual y el símbolo leído.

---

## 🔢 Definición formal de la máquina

Se define formalmente la máquina como una **7-tupla**:

```
M = (Q, Σ, Γ, δ, q₀, B, F)
```

### Conjunto de estados (Q)

Se subdivide en tres bloques lógicos:

```
Q = Q_control ∪ Q_texto→morse ∪ Q_morse→texto
```

| Bloque | Función |
|---|---|
| `Q_control` | Inicialización, navegación general, limpieza de cinta y parada. `Q_control = {q0, q_retorno, q_limpieza, q_f}` |
| `Q_texto→morse` | Lee un carácter de texto, viaja al final de la cinta para escribir su secuencia Morse equivalente, e inserta los espacios necesarios. |
| `Q_morse→texto` | Ramas que actúan como un árbol de decisión binario: acumulan puntos (`.`) y rayas (`-`) hasta encontrar un espacio, determinando la letra final a escribir. |

### Alfabeto de entrada (Σ)

Caracteres del alfabeto latino en mayúsculas, el espacio (separador de palabras), los símbolos Morse y la barra `/` (separador de palabras en Morse):

```
Σ = {A, B, C, ..., Z, ·, –, ' ', /}
```

### Alfabeto de la cinta (Γ)

Incluye todo Σ, más el símbolo blanco, un delimitador temporal y las versiones "marcadas" de cada carácter:

```
Γ = Σ ∪ {B, #, A', B', ..., Z', ·', –'}
```

> Las versiones marcadas (como `A'`) le permiten a la máquina saber qué caracteres ya procesó. El delimitador `#` separa físicamente la zona de entrada de la zona de salida durante la traducción.

### Estado inicial (q₀)

Estado de arranque desde el cual el cabezal lee el primer símbolo de la cinta para determinar, de forma determinista, si traducirá Texto → Morse o Morse → Texto.

### Símbolo blanco (B)

Representa una casilla vacía. La cinta está infinitamente llena de símbolos `B` hacia la derecha y la izquierda, fuera de la entrada inicial.

### Conjunto de estados finales (F)

```
F = {q_f}
```

Estado de aceptación donde la máquina se detiene exitosamente tras completar la traducción.

### Función de transición (δ)

```
δ : Q × Γ → Q × Γ × {L, R}
```

Define el comportamiento completo de la máquina: dado un estado y un símbolo leído, determina el nuevo estado, el símbolo a escribir, y la dirección de movimiento del cabezal.

---

## 📁 Estructura del proyecto

```
proyecto_turing/
├── README.md                  # Este documento
├── cinta.py                    # Clase Cinta (memoria infinita, Γ)
├── texto_a_morse.py            # Q_control ∪ Q_texto→morse
├── morse_a_texto.py            # Q_control ∪ Q_morse→texto
├── maquina_turing.py           # Integración de ambos sentidos + menú
└── tests/
    └── test_maquina.py         # Pruebas unitarias
```

---

## ▶️ Uso

```bash
python maquina_turing.py
```

El programa solicitará:

1. El sentido de traducción (Texto → Morse o Morse → Texto).
2. La cadena a traducir.

También puede usarse cada módulo de forma independiente:

```python
from texto_a_morse import texto_a_morse
from morse_a_texto import morse_a_texto

texto_a_morse("SOS")        # -> "... --- ..."
morse_a_texto("... --- ...")  # -> "SOS"
```

---

## 🧪 Ejemplos

| Entrada | Sentido | Salida |
|---|---|---|
| `SOS` | Texto → Morse | `... --- ...` |
| `... --- ...` | Morse → Texto | `SOS` |
| `HOLA MUNDO` | Texto → Morse | `.... --- .-.. .- / -- ..- -. -.. ---` |
| `IPN` | Texto → Morse | `.. .--. -.` |

> El separador `/` indica un espacio entre palabras en la cadena Morse.

---

## 🏗️ Diseño orientado a objetos

- **`Cinta`**: encapsula la memoria infinita de la MT usando un diccionario `{posición: símbolo}`, evitando límites artificiales de tamaño. Expone `leer()`, `escribir()`, `mover()` — análogos directos a las operaciones permitidas por δ.
- **`MaquinaTuringTextoMorse`** / **`MaquinaTuringMorseTexto`**: cada una encapsula su propio subconjunto de estados (`Q_texto→morse` o `Q_morse→texto`) y su tabla de transición, despachando el comportamiento según el estado actual — una traducción directa de δ a código.
- **Separación de responsabilidades**: la lógica de "qué hacer en cada estado" vive en métodos privados de la clase, manteniendo la función de transición legible y trazable paso a paso (modo `verbose=True` disponible para depuración).

---

## 👥 Autores

| Nombre | Boleta | Grupo |
|---|---|---|
| _Completar_ | _Completar_ | _Completar_ |
| _Completar_ | _Completar_ | _Completar_ |
| _Completar_ | _Completar_ | _Completar_ |

**Fecha:** _Completar_
**Materia:** Teoría de la Computación
**Docente:** Mtra. Karina Rodríguez Mejía
**Institución:** UPIIZ — Instituto Politécnico Nacional