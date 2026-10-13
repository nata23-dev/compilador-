"""AFD para validar identificadores de GENESIS."""

Q0 = "q0"
Q1 = "q1"
QE = "qE"

ESTADOS = (Q0, Q1, QE)
CATEGORIAS = ("L", "D", "_", "OTRO")
ESTADO_INICIAL = Q0
ESTADOS_FINALES = (Q1,)
ESTADO_RECHAZO = QE

# Filas: q0, q1, qE. Columnas: L, D, _, OTRO.
TRANSICIONES = (
    (Q1, QE, QE, QE),
    (Q1, Q1, Q1, QE),
    (QE, QE, QE, QE),
)


def _categoria(caracter: str) -> int:
    """Devuelve la columna de la tabla correspondiente al carácter."""
    if "A" <= caracter <= "Z" or "a" <= caracter <= "z":
        return 0
    if "0" <= caracter <= "9":
        return 1
    if caracter == "_":
        return 2
    return 3  # OTRO


def acepta_identificador(cadena: str) -> bool:
    """Acepta solo si, tras consumir toda la cadena, el estado es q1."""
    estado = ESTADO_INICIAL
    for caracter in cadena:
        if estado == Q0:
            fila = 0
        elif estado == Q1:
            fila = 1
        else:
            fila = 2
        estado = TRANSICIONES[fila][_categoria(caracter)]
    return estado in ESTADOS_FINALES
