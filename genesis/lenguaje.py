"""Catálogo y caracteres compartidos por el resaltado y la tokenización."""


# Este orden determina los primeros registros de la tabla de símbolos.
PALABRAS_RESERVADAS = (
    ("ecosistema", "estructura"),
    ("habitat", "estructura"),
    ("especie", "estructura"),
    ("evolucionar", "evolucion"),
    ("ciclos", "evolucion"),
    ("mutar", "evolucion"),
    ("tasa", "evolucion"),
    ("seleccionar", "operaciones"),
    ("por", "operaciones"),
    ("reproducir", "operaciones"),
    ("observar", "operaciones"),
)


def es_caracter_identificador(caracter: str) -> bool:
    return (
        "a" <= caracter <= "z"
        or "A" <= caracter <= "Z"
        or "0" <= caracter <= "9"
        or caracter == "_"
    )


def recorrer_palabras_reservadas(texto: str):
    """Produce inicio, fin y categoría de cada palabra reservada completa."""
    posicion = 0
    while posicion < len(texto):
        if not es_caracter_identificador(texto[posicion]):
            posicion += 1
            continue

        inicio = posicion
        while posicion < len(texto) and es_caracter_identificador(texto[posicion]):
            posicion += 1
        lexema = texto[inicio:posicion]
        for palabra, categoria in PALABRAS_RESERVADAS:
            if lexema == palabra:
                yield inicio, posicion, categoria
                break
