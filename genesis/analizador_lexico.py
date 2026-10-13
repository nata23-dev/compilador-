"""Análisis léxico manual del código fuente GENESIS."""

from dataclasses import dataclass

from genesis.afd_identificadores import acepta_identificador
from genesis.afd_numeros import clasificar_numero
from genesis.lenguaje import PALABRAS_RESERVADAS, es_caracter_identificador


@dataclass(frozen=True, slots=True)
class Token:
    lexema: str
    clasificacion: str
    linea: int
    columna: int


def tokenizar(codigo: str) -> list[Token]:
    """Recorre el código carácter por carácter, sin validar candidatos con AFD."""
    tokens: list[Token] = []
    posicion = 0
    linea = 1
    columna = 1

    while posicion < len(codigo):
        caracter = codigo[posicion]

        if caracter == "\r" or caracter == "\n":
            if (
                caracter == "\r"
                and posicion + 1 < len(codigo)
                and codigo[posicion + 1] == "\n"
            ):
                posicion += 2
            else:
                posicion += 1
            linea += 1
            columna = 1
            continue

        if caracter == " " or caracter == "\t":
            posicion += 1
            columna += 1
            continue

        inicio = posicion
        columna_inicial = columna

        if ("a" <= caracter <= "z") or ("A" <= caracter <= "Z") or caracter == "_":
            posicion += 1
            while (
                posicion < len(codigo)
                and es_caracter_identificador(codigo[posicion])
            ):
                posicion += 1
            lexema = codigo[inicio:posicion]
            clasificacion = "IDENTIFICADOR_CANDIDATO"
            for palabra, _ in PALABRAS_RESERVADAS:
                if lexema == palabra:
                    clasificacion = "PALABRA_RESERVADA"
                    break

        elif ("0" <= caracter <= "9") or (
            caracter == "." and posicion + 1 < len(codigo)
            and "0" <= codigo[posicion + 1] <= "9"
        ):
            posicion += 1
            while posicion < len(codigo) and (
                es_caracter_identificador(codigo[posicion]) or codigo[posicion] == "."
            ):
                posicion += 1
            lexema = codigo[inicio:posicion]
            clasificacion = "NUMERO_CANDIDATO"

        elif (
            caracter == ":"
            and posicion + 1 < len(codigo)
            and codigo[posicion + 1] == "="
        ):
            posicion += 2
            lexema = ":="
            clasificacion = "OPERADOR_ASIGNACION"

        elif caracter in "{};(),":
            posicion += 1
            lexema = caracter
            clasificacion = "SEPARADOR"

        else:
            posicion += 1
            lexema = caracter
            clasificacion = "TOKEN_DESCONOCIDO"

        tokens.append(Token(lexema, clasificacion, linea, columna_inicial))
        columna += posicion - inicio

    return tokens


def analizar_identificadores(codigo: str) -> list[Token]:
    """Valida únicamente los candidatos a identificador, conservando el orden."""
    resultado: list[Token] = []
    for token in tokenizar(codigo):
        if token.clasificacion == "IDENTIFICADOR_CANDIDATO":
            clasificacion = (
                "IDENTIFICADOR" if acepta_identificador(token.lexema)
                else "IDENTIFICADOR_INVALIDO"
            )
            token = Token(token.lexema, clasificacion, token.linea, token.columna)
        resultado.append(token)
    return resultado


def analizar_codigo(codigo: str) -> list[Token]:
    """Valida los números después de los identificadores, sin cambiar otros tokens."""
    resultado: list[Token] = []
    for token in analizar_identificadores(codigo):
        if token.clasificacion == "NUMERO_CANDIDATO":
            token = Token(
                token.lexema,
                clasificar_numero(token.lexema),
                token.linea,
                token.columna,
            )
        resultado.append(token)
    return resultado
