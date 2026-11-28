#semantica.py- analisis semantico del compilador .tc

from parser import (
    NodoPrograma, NodoDeclaracion, NodoSalida, NodoValidacion,
    NodoBinOp, NodoNum, NodoIdent,
)

class SemanticError(Exception):
    def __init__(self, mensaje, linea, columna):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.linea = linea
        self.columna = columna

    def __str__(self):
        return (
            f"Error semántico en línea {self.linea}, "
            f"columna {self.columna}: {self.mensaje}"
        )

class AnalizadorSemanticos:
    def __init__(self):
        self.tabla = {}  # {nombre: linea_de_declaracion}
        self.historial = []  # [(nombre, linea, columna)] en orden
        
    def analizar(self, programa):
        self.tabla = {}
        self.historial = []
        for sentencia in programa.sentencias:
            self._visitar_sentencia(sentencia)
        return self.tabla
    
    # sentencias
    def _visitar_sentencia(self, nodo):
        if isinstance(nodo, NodoDeclaracion):
            self._declaracion(nodo)
        elif isinstance(nodo, NodoSalida):
            self._expresion(nodo.expresion)
        elif isinstance(nodo, NodoValidacion):
            pass
        else:
            raise SemanticError(
                f"sentencia inesperada: {type(nodo).__name__}",
                getattr(nodo, "linea", 0),
                getattr(nodo, "columna", 0)
            )

    # declaracion
    def _declaracion(self, nodo):
        # 1 - redeclaracion?
        if nodo.nombre in self.tabla:
            prev = self.tabla[nodo.nombre]
            raise SemanticError(
                f"redeclaración de la variable '{nodo.nombre}' "
                f"(ya declarada en línea {prev})",
                nodo.linea, nodo.columna,
            )
        # 2 - verificar la expresion ANTES de agregagr la varibale
        # ej: 'let x = x + 1' --> falla porque x no existe
        self._expresion(nodo.expresion)
        # 3 - ahora si: registar en la tabla
        self.tabla[nodo.nombre] = nodo.linea
        self.historial.append((nodo.nombre, nodo.linea, nodo.columna))
        
# expresiones
    def _expresion(self, nodo):
        if isinstance(nodo, NodoNum):
            return
        if isinstance(nodo, NodoIdent):
            if nodo.nombre not in self.tabla:
                raise SemanticError(
                    f"variable no declarada: '{nodo.nombre}'",
                    nodo.linea, nodo.columna,
                )
            return
        if isinstance(nodo, NodoBinOp):
            self._expresion(nodo.izq)
            self._expresion(nodo.der)
            return
        raise SemanticError(
            f"nodo inesperado en expresión: {type(nodo).__name__}",
            getattr(nodo, "linea", 0),
            getattr(nodo, "columna", 0),
        )
    
# API
def analizar(programa):
    """Devuelve la tabla de símbolos {nombre: linea}. Lanza SemanticError."""
    return AnalizadorSemanticos().analizar(programa)

def formato_tabla(tabla):
    if not tabla:
        return " (vacia)"
    lineas = [f"{'Variable':15} {'tipo':18} {'linea':>6}"]
    lineas.append("-"*32)
    for nombre, linea in tabla.items():
        lineas.append(f"{nombre:15}{'int':8}{linea:>6}")
    return "\n".join(lineas)

# cli prueba
if __name__ == "__main__":
    import sys
    from lexer import tokenizar, LexerError
    from parser import parsear, ParserError

    if len(sys.argv) < 2:
        print("uso: py semantica.py ejemplos/demo.tc")
        sys.exit(2)

    with open(sys.argv[1], encoding="utf-8") as f:
        fuente = f.read()

    try:
        tokens = tokenizar(fuente)
        ast = parsear(tokens)
        tabla = analizar(ast)
        print("Tabla de símbolos:")
        print(formato_tabla(tabla))
        print()
        print(f"OK — análisis semántico sin errores ({len(tabla)} variables)")
    except LexerError as e:
        print(e)
        sys.exit(1)
    except ParserError as e:
        print(e)
        sys.exit(1)
    except SemanticError as e:
        print(e)
        sys.exit(1)