from dataclasses import dataclass

#TOKENS:
LET      = "LET"
MOSTRAR  = "MOSTRAR"
VALIDAR  = "VALIDAR"
AFD      = "AFD"
AFN      = "AFN"
IDENT    = "IDENT"
NUM      = "NUM"
CADENA   = "CADENA"
PLUS     = "PLUS"      # +
MINUS    = "MINUS"     # -
STAR     = "STAR"      # *
LPAREN   = "LPAREN"    # (
RPAREN   = "RPAREN"    # )
SEMI     = "SEMI"      # ;
EQUAL    = "EQUAL"     # =
EOF      = "EOF"       # End Of File


PALABRAS_RESERVADAS = {
    "let": LET, "mostrar": MOSTRAR, "validar": VALIDAR,
    "afd": AFD, "afn": AFN,
}


@dataclass
class Tokens:
    tipo: str
    lexema: str
    linea: int
    columna: int
    
    def __repr__(self):
        return f"Token({self.tipo}, {self.lexema!r}, {self.linea}:{self.columna})"

#Creation of lexer handler
class LexerError(Exception):
    def __init__(self, mensaje, linea=None, columna=None):
        super().__init__(mensaje)
        self.mensaje = mensaje          # ← guardar
        self.linea = linea
        self.columna = columna

    def __str__(self):
        if self.linea is not None and self.columna is not None:
            return f"Error léxico en línea {self.linea}, columna {self.columna}: {self.mensaje}"
        return f"Error léxico: {self.mensaje}"


# Tabla Ident: estado 0 = inicio, estado = 1 dentro del identificador
# Cada entrada: (estado_actual, categorica_de_caracter) -> estado_siguiente
# Categorias: "letra", "digito", "_",  "otro"
TABLA_IDENT = {
    (0, "letra"):1,
    (0, "digito"): None, #no puede iniciar con digito
    (0, "_"): None,
    (1, "letra"): 1,
    (1, "digito"): 1,
    (1, "_"): 1,
    (1, "otro"): None
}
ESTADOS_ACEPTACION_IDENT = {1}

#tabla Num: estado 0 = inicio, estado 1 = dentro del numero
TABLA_NUM = {
    (0, "digito"):1,
    (0, "otro"):None,
    (1, "digito"): 1,
    (1, "otro"): None,
    (1, "letra"): None
}
ESTADOS_ACEPTACION_NUM = {1}

# Clasificacion de caracter (fuera de candenas):
def categoria(c):
    try:
        if not isinstance(c, str) or len(c) != 1:
            raise TypeError("se esperaba un solo caracter")
        if("a" <= c <= "z") or ("A" <= c <= "Z"):
            return "letra"
        if "0" <= c <= "9":
            return "digito"
        if c == "_":
            return "_"
        return "otro"
    except TypeError as exc:
        raise LexerError("caracter invalido", linea=None, columna= None) from exc

#Funcion generica para recorrer una tabla
def recorrer_tabla(tabla, aceptacion, texto, inicio):
    """
    Recorre una tabla de transiciones de un automata finito
    para identificar si una secuencia de caracteres es aceptada
    
    Args:
        tabla (dict): Diccionario que contiene las transiciones entre
            estados del autómata según la categoría del carácter.
        aceptacion (set): Conjunto de estados finales o de aceptación
            que indican cuándo una secuencia es válida.
        texto (str): Cadena de texto que se está analizando.
        inicio (int): Posición inicial dentro del texto desde donde
            comienza el recorrido del autómata.

    Returns:
        int | None: Posición final exclusiva de la secuencia reconocida
            si se alcanza un estado de aceptación. Devuelve None si
            la secuencia no es aceptada.
            
    """
    try:
        if not isinstance(texto, str):
            raise TypeError("texto debe ser una cadena")
        if not isinstance(inicio, int) or inicio < 0 or inicio > len(texto):
            raise IndexError("posicion inicial fuera de rango")
        if not hasattr(tabla, "get"):
            raise TypeError("tabla de transiciones invalida")
        if aceptacion is None:
            raise TypeError("conjunto de estados de aceptacion invalido")

        estado = 0
        i = inicio
        while i < len(texto):
            cat = categoria(texto[i])
            siguiente = tabla.get((estado, cat))
            if siguiente is None:
                break
            estado = siguiente
            i += 1
        if estado in aceptacion and i > inicio:
            return i    #posicion final (exclusiva)
        return None
    except LexerError:
        raise
    except (TypeError, IndexError, AttributeError) as exc:
        raise LexerError("error al recorrer la tabla de transiciones") from exc

#Cadenas con escapes
ESCAPES = {'"': '"', '\\': '\\', 'n': '\n', 't': '\t', 'r': '\r'}

def escanear_cadena(fuente, i, linea, col):
    """Funcion: leer una cadena de texto que esta escrita entre comillas dobles "abcd...",
    identifica caracteres especiales de 'ESCAPES' y los convierte en sus valores correspondientes

    Args:
        fuente ( str ): codigo fuente completo que se esta analizando
        i ( int ): posicion actual dentro del codigo fuente, donde comienza la cadena
        linea ( int ): numero de linea actual del codigo fuente
        col ( int ): numero de columna actual donde comienza la cadena

    Raises:
        LexerError: si la cadena termina con una barra invertida sin un caracter de escape
        LexerError: si se encuentra un caracter de escape no valido
        LexerError: si se encuentra un salto de linea dentor de la cadena
        LexerError: si se llega al final del codigo fuente sin encontrar la comilla de cierre

    Returns:
        tupla: una tupla con cuatro elementos:
                str: valor de la cadena despues de interpretar los caracteres de escape
                int: posicion del codigo fuente donde continua el analisis
                int: numero de linea actual
                int: numero de columna siguiente a la comilla
    """
    try:
        if not isinstance(fuente, str):
            raise TypeError("codigo fuente debe ser una cadena")
        if not isinstance(i, int) or i < 0 or i >= len(fuente):
            raise IndexError("posicion inicial invalida")
        if not isinstance(linea, int) or not isinstance(col, int):
            raise TypeError("linea y columna deben ser enteros")

        #fuente[i] == '"'
        i += 1
        col += 1
        valor = []
        while i < len(fuente):
            c = fuente[i]
            if c == '"':
                return "".join(valor), i + 1, linea, col + 1
            if c == "\\":
                if i + 1 >= len (fuente):
                    raise LexerError("cadena sin cierre", linea, col)
                e = fuente[i+1]
                if e not in ESCAPES:
                    raise LexerError(f"escape invalido: \\{e}", linea, col)
                valor.append(ESCAPES[e])
                i += 2
                col += 2
                continue
            if c == "\n":
                raise LexerError("salto de linea dentro de cadena", linea, col)
            valor.append(c)
            i += 1
            col += 1
        raise LexerError("cadena sin cierre", linea, col)
    except LexerError:
        raise
    except (TypeError, IndexError) as exc:
        raise LexerError("error interno al escanear la cadena", linea, col) from exc

#Bucle principal
def tokenizar(fuente):
    """Realiza el análisis léxico del código fuente, identificando y
    clasificando los diferentes elementos en tokens.

    Args:
        fuente (str): Cadena de texto que contiene el código fuente
            que se desea analizar.

    Raises:
        LexerError: Si se encuentra un carácter que no está permitido
            dentro del lenguaje.
        LexerError: Si se encuentra una cadena con formato incorrecto,
            como escapes inválidos, saltos de línea o falta de cierre.

    Returns:
        list: Lista de objetos Tokens que representan los elementos
            identificados en el código fuente, incluyendo un token EOF
            que indica el final del análisis.
    """
    
    
    tokens = []
    i = 0
    linea = 1
    col = 1
    n = len(fuente)
    while i < n:
        c = fuente[i]
        #espacios, tabs, saltos de linea
        if c in " \t\r":
            i += 1
            col += 1
            continue
        if c == "\n":
            i += 1
            linea += 1
            col = 1
            continue
        # cadena
        if c == '"':
            linea_inicio = linea
            col_inicio = col
            valor, i, linea, col = escanear_cadena(fuente, i, linea, col)
            tokens.append(Tokens(CADENA, valor, linea_inicio, col_inicio))
            continue
        #IDENT o palabra reservada
        fin = recorrer_tabla(TABLA_IDENT, ESTADOS_ACEPTACION_IDENT, fuente, i)
        if fin is not None:
            lexema = fuente[i:fin]
            tipo = PALABRAS_RESERVADAS.get(lexema, IDENT)
            tokens.append(Tokens(tipo, lexema, linea, col))
            col += fin - i
            i = fin
            continue
        #NUM
        fin = recorrer_tabla(TABLA_NUM, ESTADOS_ACEPTACION_NUM, fuente, i)
        if fin is not None:
            lexema = fuente[i:fin]
            tokens.append(Tokens(NUM, lexema, linea, col))
            col += fin - i
            i = fin
            continue
        # simbolos simples
        SIMBOLOS = {"+": PLUS, "-": MINUS, "*": STAR,
                    "(": LPAREN, ")": RPAREN, ";": SEMI, "=": EQUAL}
        if c in SIMBOLOS:
            tokens.append(Tokens(SIMBOLOS[c], c, linea, col))
            i += 1; col += 1; continue
        #error lexico
        raise LexerError(f"caracter no permitido: {c!r}", linea, col)
    tokens.append(Tokens(EOF, "", linea, col))
    return tokens
