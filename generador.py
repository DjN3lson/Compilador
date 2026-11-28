# generador.py — Generación de código Python a partir del AST
from parser import (
    NodoPrograma, NodoDeclaracion, NodoSalida, NodoValidacion,
    NodoBinOp, NodoNum, NodoIdent,
)


class GeneradorError(Exception):
    def __init__(self, mensaje):
        super().__init__(mensaje)
        self.mensaje = mensaje

    def __str__(self):
        return f"Error de generación: {self.mensaje}"


def _nombre_variable(nombre):
    return "v_" + nombre


def _expr(nodo):
    if isinstance(nodo, NodoNum):
        return str(int(nodo.valor))
    if isinstance(nodo, NodoIdent):
        return _nombre_variable(nodo.nombre)
    if isinstance(nodo, NodoBinOp):
        izq = _expr(nodo.izq)
        der = _expr(nodo.der)
        return f"({izq} {nodo.op} {der})"
    raise GeneradorError(f"nodo inesperado en expresión: {type(nodo).__name__}")


def generar(programa):
    if not isinstance(programa, NodoPrograma):
        raise GeneradorError("se esperaba NodoPrograma en la raíz del AST")

    lineas = [
        "# Archivo generado automáticamente por el compilador .tc",
        "# No editar a mano.",
        "from automatas import validar",
        "",
    ]

    for sentencia in programa.sentencias:
        if isinstance(sentencia, NodoDeclaracion):
            nombre = _nombre_variable(sentencia.nombre)
            expr = _expr(sentencia.expresion)
            lineas.append(f"{nombre} = {expr}")
        elif isinstance(sentencia, NodoSalida):
            lineas.append(f"print({_expr(sentencia.expresion)})")
        elif isinstance(sentencia, NodoValidacion):
            lineas.append(
                f"print(validar({sentencia.modelo!r}, "
                f"{repr(sentencia.cadena)}))"
            )
        else:
            raise GeneradorError(
                f"sentencia inesperada: {type(sentencia).__name__}"
            )

    lineas.append("")
    return "\n".join(lineas)