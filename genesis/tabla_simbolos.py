"""Tabla binaria sin cabecera, con registros consecutivos de 300 bytes.

Formato little-endian <I256s32sII: número u32 (bytes 0-3), lexema UTF-8
(4-259), tipo UTF-8 (260-291), línea u32 (292-295) y columna u32
(296-299). Los campos de texto se completan con bytes nulos.
"""

from dataclasses import dataclass
import os
from pathlib import Path
import struct
import tempfile

from genesis.analizador_lexico import Token
from genesis.lenguaje import PALABRAS_RESERVADAS


RUTA_TABLA = Path(__file__).resolve().parent.parent / "datos" / "Tabla de símbolos"
CAPACIDAD_LEXEMA = 256  # bytes UTF-8
CAPACIDAD_TIPO = 32  # bytes UTF-8
FORMATO_REGISTRO = struct.Struct("<I256s32sII")
TAMANO_REGISTRO = FORMATO_REGISTRO.size  # 300 bytes
MAXIMO_U32 = 2**32 - 1


class ErrorTablaSimbolos(Exception):
    """Indica un formato binario inválido o un dato que no cabe en un registro."""


@dataclass(frozen=True, slots=True)
class RegistroSimbolo:
    numero: int
    lexema: str
    tipo: str
    linea: int
    columna: int


@dataclass(frozen=True, slots=True)
class SimboloNoAlmacenado:
    lexema: str
    tipo: str
    linea: int
    columna: int
    motivo: str


def _codificar(registro: RegistroSimbolo) -> bytes:
    lexema = registro.lexema.encode("utf-8")
    tipo = registro.tipo.encode("utf-8")
    if not lexema:
        raise ErrorTablaSimbolos("El lexema está vacío.")
    if len(lexema) > CAPACIDAD_LEXEMA:
        raise ErrorTablaSimbolos(
            f"El lexema ocupa {len(lexema)} bytes; el máximo es {CAPACIDAD_LEXEMA}."
        )
    if len(tipo) > CAPACIDAD_TIPO:
        raise ErrorTablaSimbolos(
            f"El tipo ocupa {len(tipo)} bytes; el máximo es {CAPACIDAD_TIPO}."
        )
    for nombre, valor in (
        ("número de registro", registro.numero),
        ("línea", registro.linea),
        ("columna", registro.columna),
    ):
        if not isinstance(valor, int) or not 0 <= valor <= MAXIMO_U32:
            raise ErrorTablaSimbolos(f"El campo {nombre} está fuera de rango.")
    if registro.numero == 0:
        raise ErrorTablaSimbolos("El número de registro debe comenzar en 1.")
    return FORMATO_REGISTRO.pack(
        registro.numero, lexema, tipo, registro.linea, registro.columna
    )


def _decodificar(datos: bytes, numero_esperado: int) -> RegistroSimbolo:
    if len(datos) != TAMANO_REGISTRO:
        raise ErrorTablaSimbolos("El archivo contiene un registro incompleto.")
    numero, lexema, tipo, linea, columna = FORMATO_REGISTRO.unpack(datos)
    if numero != numero_esperado:
        raise ErrorTablaSimbolos("El orden físico de los registros está dañado.")
    try:
        return RegistroSimbolo(
            numero,
            lexema.rstrip(b"\0").decode("utf-8"),
            tipo.rstrip(b"\0").decode("utf-8"),
            linea,
            columna,
        )
    except UnicodeError as error:
        raise ErrorTablaSimbolos("El archivo contiene texto UTF-8 inválido.") from error


def preparar_registros(
    tokens: list[Token],
) -> tuple[list[RegistroSimbolo], list[SimboloNoAlmacenado]]:
    """Ordena símbolos y elimina duplicados mediante búsqueda secuencial."""
    registros: list[RegistroSimbolo] = []
    omitidos: list[SimboloNoAlmacenado] = []
    vistos: list[tuple[str, str]] = []

    def agregar(lexema: str, tipo: str, linea: int, columna: int) -> None:
        for lexema_visto, tipo_visto in vistos:
            if lexema == lexema_visto and tipo == tipo_visto:
                return
        vistos.append((lexema, tipo))
        registro = RegistroSimbolo(len(registros) + 1, lexema, tipo, linea, columna)
        try:
            _codificar(registro)
        except ErrorTablaSimbolos as error:
            omitidos.append(
                SimboloNoAlmacenado(lexema, tipo, linea, columna, str(error))
            )
        else:
            registros.append(registro)

    for palabra, _ in PALABRAS_RESERVADAS:
        agregar(palabra, "PALABRA_RESERVADA", 0, 0)
    for token in tokens:
        if token.clasificacion == "IDENTIFICADOR":
            agregar(token.lexema, token.clasificacion, token.linea, token.columna)
    for token in tokens:
        if token.clasificacion == "ENTERO" or token.clasificacion == "DECIMAL":
            agregar(token.lexema, token.clasificacion, token.linea, token.columna)

    return registros, omitidos


def reconstruir_tabla(
    tokens: list[Token], ruta: Path = RUTA_TABLA
) -> list[SimboloNoAlmacenado]:
    """Escribe secuencialmente un archivo nuevo y lo sustituye al finalizar."""
    registros, omitidos = preparar_registros(tokens)
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=ruta.parent, prefix=".tabla_", delete=False
        ) as archivo:
            temporal = Path(archivo.name)
            for registro in registros:
                archivo.write(_codificar(registro))
        os.replace(temporal, ruta)
    finally:
        if temporal is not None:
            try:
                temporal.unlink(missing_ok=True)
            except OSError:
                pass
    return omitidos


def _cantidad_registros(tamano_archivo: int) -> int:
    if tamano_archivo % TAMANO_REGISTRO != 0:
        raise ErrorTablaSimbolos(
            "El tamaño del archivo no coincide con registros completos."
        )
    return tamano_archivo // TAMANO_REGISTRO


def consultar_registro(numero: int, ruta: Path = RUTA_TABLA) -> RegistroSimbolo:
    """Lee solo el registro solicitado mediante seek((numero - 1) * tamaño)."""
    if isinstance(numero, bool) or not isinstance(numero, int) or numero < 1:
        raise ValueError("El número de registro debe ser un entero mayor o igual a 1.")
    with Path(ruta).open("rb") as archivo:
        archivo.seek(0, os.SEEK_END)
        cantidad = _cantidad_registros(archivo.tell())
        if numero > cantidad:
            raise IndexError(
                f"No existe el registro {numero}; la tabla tiene {cantidad} registros."
            )
        desplazamiento = (numero - 1) * TAMANO_REGISTRO
        archivo.seek(desplazamiento)
        return _decodificar(archivo.read(TAMANO_REGISTRO), numero)


def leer_registros(ruta: Path = RUTA_TABLA) -> list[RegistroSimbolo]:
    """Recupera secuencialmente los registros físicos para mostrar la tabla."""
    registros: list[RegistroSimbolo] = []
    with Path(ruta).open("rb") as archivo:
        archivo.seek(0, os.SEEK_END)
        cantidad = _cantidad_registros(archivo.tell())
        archivo.seek(0)
        for numero in range(1, cantidad + 1):
            registros.append(_decodificar(archivo.read(TAMANO_REGISTRO), numero))
    return registros
