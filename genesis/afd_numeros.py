"""AFD para reconocer enteros y decimales de GENESIS."""

Q0 = "q0"
Q1 = "q1"
Q2 = "q2"
Q3 = "q3"
QE = "qE"

ESTADOS = (Q0, Q1, Q2, Q3, QE)
CATEGORIAS = ("D", "P", "OTRO")
ESTADO_INICIAL = Q0
ESTADOS_FINALES = (Q1, Q3)
ESTADO_RECHAZO = QE

# Filas: q0, q1, q2, q3, qE. Columnas: D, P, OTRO.
TRANSICIONES = (
    (Q1, QE, QE),
    (Q1, Q2, QE),
    (Q3, QE, QE),
    (Q3, QE, QE),
    (QE, QE, QE),
)


def _categoria(caracter: str) -> int:
    """Devuelve la columna D, P u OTRO de la tabla de transiciones."""
    if "0" <= caracter <= "9":
        return 0
    if caracter == ".":
        return 1
    return 2


def clasificar_numero(cadena: str) -> str:
    """Consume toda la cadena y devuelve ENTERO, DECIMAL o NUMERO_INVALIDO."""
    estado = ESTADO_INICIAL
    for caracter in cadena:
        if estado == Q0:
            fila = 0
        elif estado == Q1:
            fila = 1
        elif estado == Q2:
            fila = 2
        elif estado == Q3:
            fila = 3
        else:
            fila = 4
        estado = TRANSICIONES[fila][_categoria(caracter)]

    if estado == Q1:
        return "ENTERO"
    if estado == Q3:
        return "DECIMAL"
    return "NUMERO_INVALIDO"


def motivo_numero_invalido(cadena: str) -> str:
    """Explica un rechazo del AFD sin convertir el candidato a número."""
    if cadena and cadena[0] == ".":
        return "Falta un dígito antes del punto decimal."

    cantidad_puntos = 0
    for caracter in cadena:
        if caracter == ".":
            cantidad_puntos += 1
        elif not "0" <= caracter <= "9":
            return "Contiene caracteres no permitidos."

    if cantidad_puntos > 1:
        return "Contiene más de un punto decimal."
    if cadena and cadena[-1] == ".":
        return "Falta un dígito después del punto decimal."
    return "Formato numérico inválido."
