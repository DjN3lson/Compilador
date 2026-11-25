import argparse
import sys

from lexer import tokenizar, LexerError
from parser import parsear, ast_a_texto, ParserError
from semantica import analizar, SemanticError, formato_table
from generador import generar, GeneradorError


def main():
    parser = argparse.ArgumentParser(description="Compilador .tc")
    parser.add_argument("archivo", help="archivo fuente .tc")
    parser.add_argument("--tokens", action="store_true",
                        help="imprime la lista de tokens y sale")
    parser.add_argument("--ast", action="store_true",
                        help="imprime el AST y sale")
    parser.add_argument("--tabla", action="store_true",
                        help="imprime la tabla de símbolos y sale")
    parser.add_argument("-o", "--salida", default="salida.py",
                        help="archivo Python de salida")
    args = parser.parse_args()

    # ---------- leer fuente ----------
    try:
        with open(args.archivo, encoding="utf-8") as f:
            fuente = f.read()
    except FileNotFoundError:
        print(f"Error: no se encontró el archivo {args.archivo}")
        return 1

    # ---------- 1. LEXER ----------
    try:
        tokens = tokenizar(fuente)
    except LexerError as e:
        print(e)
        return 1

    if args.tokens:
        print(f"{'TIPO':10} {'LEXEMA':20} {'LINEA':>5} {'COL':>4}")
        for t in tokens:
            print(f"{t.tipo:10} {t.lexema!r:20} {t.linea:>5} {t.columna:>4}")
        return 0

    # ---------- 2. PARSER + AST ----------
    try:
        ast = parsear(tokens)
    except ParserError as e:
        print(e)
        return 1

    if args.ast:
        print(ast_a_texto(ast))
        return 0

    # ---------- 3. SEMÁNTICA ----------
    try:
        tabla = analizar(ast)
    except SemanticError as e:
        print(e)
        return 1

    if args.tabla:
        print(formato_table(tabla))
        return 0

    # ---------- 4. GENERACIÓN ----------
    try:
        codigo = generar(ast)
    except GeneradorError as e:
        print(e)
        return 1

    # ---------- 5. ESCRIBIR SALIDA ----------
    # Solo aquí, después de que TODAS las etapas pasaron,
    # se escribe el archivo. Si algo falló antes, salida.py
    # no se crea ni se sobrescribe.
    try:
        with open(args.salida, "w", encoding="utf-8") as f:
            f.write(codigo)
    except OSError as e:
        print(f"Error al escribir {args.salida}: {e}")
        return 1

    print(f"OK — {args.salida} generado")
    return 0


if __name__ == "__main__":
    sys.exit(main())