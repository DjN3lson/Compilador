# generador.py - generacion de codigo python a partir del ast
from parser import(
    NodoPrograma, NodoDeclaracion, NodoSalida, NodoValidacion,
    NodoBinOp, NodoNum, NodoIdent,
)

class GeneradorError(Exception):
    def __init__(self, mensaje):
        super().__init__(mensaje)
        self.mensaje = mensaje
        
    def __str__(self):
        return f"Error de generacion: {self.mensaje}"

def _nombre_variables(nombre):
    return "v_"+nombre

def _expr(nodo):
    if isinstance(nodo, NodoNum):
        return str(int(nodo.valor))
    if isinstance(nodo, NodoIdent):
        return _nombre_variables(nodo.nombre)
    if isinstance(nodo, NodoBinOp):
        izq = _expr(nodo.izq)
        der = _expr(nodo.der)
        return f"{izq} {nodo.op} {der}"
    raise GeneradorError(f"nodo inseperado en expresion: {type(nodo).__name__}")

def generar(programa):
    """
    Recorre el AST y devuelve el código Python como string.
    NO escribe archivos: el compilador decide tras éxito de todas las etapas.
    """
    if not isinstance(programa, NodoPrograma):
        raise GeneradorError("se esperaba NodoPrograma en la raiz del AST")
    
    lineas = [
        "# Archivo generado automaticamente por el compilador .tc",
        "# No editar a mano.",
        "from automatas import validar",
        "",
    ]
    for sentencia in programa.sentencias:
        if isinstance(sentencia, NodoDeclaracion):
            lineas.append(
                f"{_nombre_variables(sentencia.nombre)}"
                f"{_expr(sentencia.expresion)}"
            )
        elif isinstance(sentencia, NodoSalida):
            lineas.append(f"print({_expr(sentencia.expresion)})")
        elif isinstance(sentencia, NodoValidacion):
            lineas.append(
                f"print(validar({sentencia.modelo!r},"
                f"{repr(sentencia.cadena)}))"
            )
        else:
            raise GeneradorError(
                f"sentencia inesperada: {type(sentencia).__name__}"
            )
    lineas.append("")
    return "\n".join(lineas)