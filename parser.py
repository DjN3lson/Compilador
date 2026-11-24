from dataclasses import dataclass
from typing import Union

from lexer import (
    Tokens, tokenizar, LexerError,
    LET, MOSTRAR, VALIDAR, AFD, AFN,
    IDENT, NUM, CADENA, PLUS, MINUS, STAR,
    LPAREN, RPAREN, SEMI, EQUAL, EOF
)


@dataclass
class NodoPrograma:
    sentencias: list


@dataclass
class NodoDeclaracion:
    nombre: str
    expresion: "Nodo"
    linea: int
    columna: int


@dataclass
class NodoSalida:
    expresion: "Nodo"
    linea: int
    columna: int


@dataclass
class NodoValidacion:
    modelo: str
    cadena: str
    linea: int
    columna: int


@dataclass
class NodoBinOp:
    op: str
    izq: "Nodo"
    der: "Nodo"
    linea: int
    columna: int


@dataclass
class NodoNum:
    valor: int
    linea: int
    columna: int


@dataclass
class NodoIdent:
    nombre: str
    linea: int
    columna: int


Nodo = Union[
    NodoPrograma, NodoDeclaracion, NodoSalida,
    NodoValidacion, NodoBinOp, NodoNum, NodoIdent
]


class ParserError(Exception):
    def __init__(self, mensaje, linea, columna):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.linea = linea
        self.columna = columna

    def __str__(self):
        return (
            f"Error sintactico en linea {self.linea}, "
            f"columna {self.columna}: {self.mensaje}"
        )


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def actual(self) -> Tokens:
        return self.tokens[self.pos]

    def avanzar(self) -> Tokens:
        tok = self.tokens[self.pos]
        if tok.tipo != EOF:
            self.pos += 1
        return tok

    def comprobar(self, tipo) -> bool:
        return self.actual().tipo == tipo

    def esperar(self, tipo, descripcion) -> Tokens:
        if self.actual().tipo != tipo:
            t = self.actual()
            raise ParserError(
                f"se esperaba {descripcion} y se encontro {t.tipo} {t.lexema!r}",
                t.linea,
                t.columna,
            )
        return self.avanzar()

    # programa = {sentencia}
    def parse_programa(self) -> NodoPrograma:
        sentencias = []
        while not self.comprobar(EOF):
            sentencias.append(self.parse_sentencia())

        if not self.comprobar(EOF):
            t = self.actual()
            raise ParserError(
                "tokens sobrantes después del final del programa",
                t.linea,
                t.columna,
            )
        return NodoPrograma(sentencias)

    # sentencia = declaracion | salida | validacion
    def parse_sentencia(self) -> Nodo:
        t = self.actual()
        if t.tipo == LET:
            return self.parse_declaracion()
        if t.tipo == MOSTRAR:
            return self.parse_salida()
        if t.tipo == VALIDAR:
            return self.parse_validacion()
        raise ParserError(
            f"se esperaba una sentencia (let | mostrar | validar) y se encontró "
            f"{t.tipo} {t.lexema!r}",
            t.linea,
            t.columna,
        )

    # declaracion = "let" IDENT "=" expresion ";"
    def parse_declaracion(self) -> NodoDeclaracion:
        let_tok = self.esperar(LET, "'let'")
        id_tok = self.esperar(IDENT, "un identificador")
        self.esperar(EQUAL, "'='")
        expr = self.parse_expresion()
        self.esperar(SEMI, "';'")
        return NodoDeclaracion(id_tok.lexema, expr, let_tok.linea, let_tok.columna)

    # salida = "mostrar" "(" expresion ")" ";"
    def parse_salida(self) -> NodoSalida:
        mostrar_tok = self.esperar(MOSTRAR, "'mostrar'")
        self.esperar(LPAREN, "'('")
        expr = self.parse_expresion()
        self.esperar(RPAREN, "')'")
        self.esperar(SEMI, "';'")
        return NodoSalida(expr, mostrar_tok.linea, mostrar_tok.columna)

    # validacion = "validar" ("afd" | "afn") CADENA ";"
    def parse_validacion(self) -> NodoValidacion:
        validar_tok = self.esperar(VALIDAR, "'validar'")
        modelo_tok = self.actual()
        if modelo_tok.tipo == AFD:
            modelo = "afd"
        elif modelo_tok.tipo == AFN:
            modelo = "afn"
        else:
            raise ParserError(
                f"se esperaba 'afd' o 'afn' y se encontró "
                f"{modelo_tok.tipo} {modelo_tok.lexema!r}",
                modelo_tok.linea,
                modelo_tok.columna,
            )
        self.avanzar()
        cadena_tok = self.esperar(CADENA, "una cadena")
        self.esperar(SEMI, "';'")
        return NodoValidacion(
            modelo,
            cadena_tok.lexema,
            validar_tok.linea,
            validar_tok.columna,
        )

    # expresion = termino { ("+" | "-") termino}
    def parse_expresion(self) -> Nodo:
        izq = self.parse_termino()
        while self.comprobar(PLUS) or self.comprobar(MINUS):
            op_tok = self.avanzar()
            der = self.parse_termino()
            izq = NodoBinOp(
                "+" if op_tok.tipo == PLUS else "-",
                izq,
                der,
                op_tok.linea,
                op_tok.columna,
            )
        return izq

    # termino = factor { "*" factor}
    def parse_termino(self) -> Nodo:
        izq = self.parse_factor()
        while self.comprobar(STAR):
            op_tok = self.avanzar()
            der = self.parse_factor()
            izq = NodoBinOp("*", izq, der, op_tok.linea, op_tok.columna)
        return izq

    def parse_factor(self) -> Nodo:
        t = self.actual()
        if t.tipo == NUM:
            self.avanzar()
            return NodoNum(int(t.lexema, 10), t.linea, t.columna)
        if t.tipo == IDENT:
            self.avanzar()
            return NodoIdent(t.lexema, t.linea, t.columna)
        if t.tipo == LPAREN:
            self.avanzar()
            expr = self.parse_expresion()
            self.esperar(RPAREN, "')'")
            return expr
        raise ParserError(
            f"se esperaba un número, un identificador o '(' y se encontró "
            f"{t.tipo} {t.lexema!r}",
            t.linea,
            t.columna,
        )


def parsear(tokens) -> NodoPrograma:
    p = Parser(tokens)
    return p.parse_programa()

# Pretty-printer del AST (para diagnostico y evidencia)
def ast_a_texto(nodo, nivel=0) -> str:
    sangria = " " * nivel
    if isinstance(nodo, NodoPrograma):
        lineas = [f"{sangria}Programa("]
        for s in nodo.sentencias:
            lineas.append(ast_a_texto(s, nivel + 1))
        lineas.append(f"{sangria}")
        return "\n".join(lineas)
    if isinstance(nodo, NodoDeclaracion):
        return(
            f"{sangria}Salida\n"
            f"{ast_a_texto(nodo.expresion, nivel + 1)}\n"
            f"{sangria}"
        )
    if isinstance(nodo, NodoSalida):
        return(
            f"{sangria}Salida\n"
            f"{ast_a_texto(nodo.expresion, nivel+1)}\n"
            f"{sangria}"
        )
    if isinstance(nodo, NodoValidacion):
        return f"{sangria}Validacion{nodo.modelo!r}, {nodo.cadena!r}"
    if isinstance(nodo, NodoBinOp):
        return(
            f"{sangria}BinOp({nodo.op!r},\n"
            f"{ast_a_texto(nodo.izq, nivel+1)},\n"
            f"{ast_a_texto(nodo.der, nivel+1)}\n"
            f"{sangria})"
        )
    if isinstance(nodo, NodoNum):
        return f"{sangria}Num({nodo.valor})"
    if isinstance(nodo, NodoIdent):
        return f"{sangria}Ident({nodo.nombre!r})"
    return f"{sangria}<nodo desconocido>"

# CLI de prueba rapida
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("uso: py parser.py ejemplos/demo.tc")
        sys.exit(2)
    with open(sys.argv[1], encoding="utf-8") as f:
        fuente = f.read()
    try:
        tokens = tokenizar(fuente)
        ast = parsear(tokens)
        print(ast_a_texto(ast))
    except LexerError as e:
        print(e)
        sys.exit(1)
    except ParserError as e:
        print(e)
        sys.exit(1)