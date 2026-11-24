import argparse
import sys
from lexer import tokenizar, LexerError
from parser import parsear, ast_a_texto, ParserError


def main():
    parser = argparse.ArgumentParser(description="Compilador .tc")
    parser.add_argument("archivo", help="archivo fuente .tc")
    parser.add_argument("--tokens", action="store_true",
                        help="imprime la lista de tokens y sale")
    parser.add_argument("-o", "--salida", default="salida.py",
                        help="archivo Python de salida")
    parser.add_argument("--ast,", action="store_true",
                        help="imprime el AST y sale")
    args = parser.parse_args()

    try:
        with open(args.archivo, encoding="utf-8") as f:
            fuente = f.read()
    except FileNotFoundError:
        print(f"Error: no se encontró el archivo {args.archivo}")
        return 1

    try:
        tokens = tokenizar(fuente)
    except LexerError as e:
        print(e)          # ya formatea etapa/línea/columna si aplicaste el parche
        return 1

    if args.tokens:
        print(f"{'TIPO':10} {'LEXEMA':20} {'LINEA':>5} {'COL':>4}")
        for t in tokens:
            print(f"{t.tipo:10} {t.lexema!r:20} {t.linea:>5} {t.columna:>4}")
        return 0
    if args.ast:
        try:
            ast = parsear(tokens)
        except ParserError as e:
            print(e)
            return 1
        print(ast_a_texto(ast))
        return 0

    # aquí irá parser, semántica, generación...
    print("Compilación pendiente de integrar parser y generador.")
    return 0

if __name__ == "__main__":
    sys.exit(main())