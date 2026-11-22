# test_lexer.py
from lexer import (
    tokenizar, LexerError,
    LET, IDENT, EQUAL, NUM, PLUS, MINUS, STAR,
    LPAREN, RPAREN, SEMI, MOSTRAR, VALIDAR, AFD, AFN, CADENA, EOF,
)

# ---------- Casos válidos: (fuente, lista de tipos esperados) ----------
CASOS_OK = [
    ("let x = 2 + 3 * 4;",
     [LET, IDENT, EQUAL, NUM, PLUS, NUM, STAR, NUM, SEMI, EOF]),
    ("mostrar((x - 1) * (x + 1));",
     [MOSTRAR, LPAREN, LPAREN, IDENT, MINUS, NUM, RPAREN, STAR,
      LPAREN, IDENT, PLUS, NUM, RPAREN, RPAREN, SEMI, EOF]),
    ('validar afd "192.168.1.1";',
     [VALIDAR, AFD, CADENA, SEMI, EOF]),
    ('validar afn "";',
     [VALIDAR, AFN, CADENA, SEMI, EOF]),
    ("let letx = 007;",
     [LET, IDENT, EQUAL, NUM, SEMI, EOF]),      # letx es IDENT, no LET
    ('validar afd "a\\"b\\\\c\\nd\\te\\rf";',
     [VALIDAR, AFD, CADENA, SEMI, EOF]),
    ("variable_1 Variable",
     [IDENT, IDENT, EOF]),                       # case-sensitive
]

# ---------- Casos de error: (fuente, fragmento esperado en el mensaje) ----------
CASOS_ERR = [
    ("let x = 2 @ 3;",
     "caracter no permitido: '@'"),
    ('validar afd "abc;',
     "cadena sin cierre"),
    ('validar afd "a\\q";',
     "escape invalido: \\q"),
    ('validar afd "linea\nquebrada";',
     "salto de linea dentro de cadena"),
]

def correr_validos():
    print("=== CASOS VÁLIDOS ===")
    fallos = 0
    for fuente, esperado in CASOS_OK:
        try:
            obtenido = [t.tipo for t in tokenizar(fuente)]
        except LexerError as e:
            print(f"[FAIL] {fuente!r}")
            print(f"   esperado: {esperado}")
            print(f"   obtenido: LexerError -> {e}")
            fallos += 1
            continue
        if obtenido == esperado:
            print(f"[OK]   {fuente!r}")
        else:
            print(f"[FAIL] {fuente!r}")
            print(f"   esperado: {esperado}")
            print(f"   obtenido: {obtenido}")
            fallos += 1
    return fallos

def correr_errores():
    print("\n=== CASOS DE ERROR LÉXICO ===")
    fallos = 0
    for fuente, fragmento in CASOS_ERR:
        try:
            tokenizar(fuente)
            print(f"[FAIL] {fuente!r} -> no lanzó LexerError")
            fallos += 1
        except LexerError as e:
            msg = str(e)
            if fragmento in msg and "Error léxico" in msg:
                print(f"[OK]   {fuente!r}")
                print(f"       -> {msg}")
            else:
                print(f"[FAIL] {fuente!r}")
                print(f"   esperaba mensaje con: {fragmento!r} y 'Error léxico'")
                print(f"   obtenido: {msg}")
                fallos += 1
    return fallos

if __name__ == "__main__":
    fallos = correr_validos() + correr_errores()
    print("\n=== RESUMEN ===")
    total = len(CASOS_OK) + len(CASOS_ERR)
    if fallos == 0:
        print(f"OK — {total}/{total} casos pasaron")
    else:
        print(f"FALLOS: {fallos} de {total}")
    raise SystemExit(0 if fallos == 0 else 1)