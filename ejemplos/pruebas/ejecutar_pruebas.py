"""
ejecutar_pruebas.py -- runner de pruebas del compilador .tc
crea los 20 archivos .tc ejecuta el compilador para cada uno verifica el resultado esperado y genera un reporte
Uso desde la raiz del proyecto, donde esta el compilador.py
py ejemplos/pruebas/ejecutar_pruebas.py
"""


import os
import re
import subprocess
import sys
import unicodedata

PRUEBAS = os.path.dirname(os.path.abspath(__file__))          # <root>/ejemplos/pruebas
BASE = os.path.dirname(os.path.dirname(PRUEBAS))            
PROGRAMAS = os.path.join(PRUEBAS, "programas")

def norm(s):
    """Minusculas sin acentos para comparar mensajes robustamente
    """
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")

# 20 programas

CASOS = [
    # 6 - validos
    {
        "id": "v01_prioridad",
        "categoria": "valido",
        "fuente": "let base = 2 + 3 * 4;\nmostrar(base);\n",
        "esperado_salida": "14\n",
        "justificacion": "El producto tiene prioridad sobre la suma: 2 + (3*4) = 14.",
    },
    {
        "id": "v02_resta_izq",
        "categoria": "valido",
        "fuente": "mostrar(8 - 3 - 1);\n",
        "esperado_salida": "4\n",
        "justificacion": "Operadores de igual prioridad asociativos por izquierda: (8-3)-1 = 4.",
    },
    {
        "id": "v03_anidados",
        "categoria": "valido",
        "fuente": "mostrar(2 * (3 + (4 - 1)));\n",
        "esperado_salida": "12\n",
        "justificacion": "Paréntesis anidados: (4-1)=3, 3+3=6, 2*6=12.",
    },
    {
        "id": "v04_varias",
        "categoria": "valido",
        "fuente": (
            'let a = 10;\n'
            'let b = a * 2;\n'
            'mostrar(a + b);\n'
            'validar afd "192.168.1.1";\n'
        ),
        "esperado_salida": "30\nACEPTA\n",
        "justificacion": "Múltiples sentencias: b=20, a+b=30, IPv4 válida -> ACEPTA.",
    },
    {
        "id": "v05_cadena_vacia",
        "categoria": "valido",
        "fuente": 'validar afd "";\nvalidar afn "";\n',
        "esperado_salida": "RECHAZA\nRECHAZA\n",
        "justificacion": "La cadena vacía no es IPv4 válida (faltan 4 octetos).",
    },
    {
        "id": "v06_acepta_rechaza",
        "categoria": "valido",
        "fuente": (
            'validar afd "192.168.1.1";\n'
            'validar afd "300.1.1.1";\n'
            'validar afn "192.168.1.100";\n'
            'validar afn "300.1.2.25";\n'
        ),
        "esperado_salida": "ACEPTA\nRECHAZA\nACEPTA\nRECHAZA\n",
        "justificacion": (
            "Aceptación y rechazo de ambos validadores. "
            "AFN corregido rechaza primer octeto > 255."
        ),
    },
    
    # 4 - Lexicos
    {
        "id": "101_caracter",
        "categoria": "lexico",
        "fuente": "let x = 2 @ 3;\n",
        "esperado_etapa": "Error léxico",
        "esperado_motivo_substr": "caracter no permitido",
        "justificacion": "@ no pertenece al alfabeto del lenguaje.",
    },
    {
        "id": "l02_sin_cierre",
        "categoria": "lexico",
        "fuente": 'validar afd "abc;',
        "esperado_etapa": "Error léxico",
        "esperado_motivo_substr": "cadena sin cierre",
        "justificacion": "Comilla de apertura sin comilla de cierre.",
    },
    {
        "id": "l03_escape",
        "categoria": "lexico",
        "fuente": 'validar afd "a\\q";\n',
        "esperado_etapa": "Error léxico",
        "esperado_motivo_substr": "escape invalido",
        "justificacion": '\\q no es un escape permitido (solo \\" \\\\ \\n \\t \\r).',
    },
    {
        "id": "l04_salto",
        "categoria": "lexico",
        "fuente": 'validar afd "linea\nquebrada";\n',
        "esperado_etapa": "Error léxico",
        "esperado_motivo_substr": "salto de linea",
        "justificacion": "No se permiten saltos de línea literales dentro de cadenas.",
    },
    # 4 - Sintacticos
    {
        "id": "s01_sin_punto_coma",
        "categoria": "sintactico",
        "fuente": "let x = 2 + 3\n",
        "esperado_etapa": "Error sintáctico",
        "esperado_motivo_substr": "se esperaba ';'",
        "justificacion": "Falta el ';' al final de la declaración.",
    },
    {
        "id": "so2_operando",
        "categoria": "sintactico",
        "fuente": "let x = 2 + ;\n",
        "esperado_etapa": "Error sintáctico",
        "esperado_motivo_substr": "se esperaba un número",
        "justificacion": "el operador '+' no tiene operando derecho" 
    },
    {
        "id": "so3_operando",
        "categoria": "sintactico",
        "fuente": "let x = 1;\nmostrar((x + 1);",
        "esperado_etapa": "Error sintáctico",
        "esperado_motivo_substr": "se esperaba ')'",
        "justificacion": "Falta cerrar el paréntesis interno de (x + 1." 
    },
    {
        "id": "so4_operando",
        "categoria": "sintactico",
        "fuente": "let x = 1;\nmostrar(x) extra;\n",
        "esperado_etapa": "Error sintáctico",
        "esperado_motivo_substr": "se esperaba ';'",
        "justificacion": "Despues de mostrar(x) aparece 'extra' antes del ';'" 
    },
    # 4 - semanticos
    {
        "id": "m01_no_declarada",
        "categoria": "semantico",
        "fuente": "mostrar(x);\n",
        "esperado_etapa": "Error semántico",
        "esperado_motivo_substr": "variable no declarada",
        "justificacion": "'x' se usa sin haber sido declarada.",
    },
    {
        "id": "m02_redeclaracion",
        "categoria": "semantico",
        "fuente": "let x = 1;\nlet x = 2;\n",
        "esperado_etapa": "Error semántico",
        "esperado_motivo_substr": "redeclaración",
        "justificacion": "'x' ya existe en la tabla de símbolos.",
    },
    {
        "id": "m03_propia",
        "categoria": "semantico",
        "fuente": "let x = x + 1;\n",
        "esperado_etapa": "Error semántico",
        "esperado_motivo_substr": "variable no declarada",
        "justificacion": "'x' no está disponible en su propia declaración.",
    },
    {
        "id": "m04_anidada",
        "categoria": "semantico",
        "fuente": "let a = 1;\nmostrar(a + b);\n",
        "esperado_etapa": "Error semántico",
        "esperado_motivo_substr": "variable no declarada",
        "justificacion": "'b' no está declarada aunque 'a' sí.",
    },
    # 2 - Fuera del Alfabeto
     {
        "id": "a01_afd",
        "categoria": "fuera_alfabeto",
        "fuente": 'validar afd "192.168.A.1";\n',
        "esperado_salida": "FUERA_DEL_ALFABETO\n",
        "justificacion": (
            "Compila; al ejecutar, 'A' no pertenece al alfabeto {0-9,.} del AFD."
        ),
    },
    {
        "id": "a02_afn",
        "categoria": "fuera_alfabeto",
        "fuente": 'validar afn "192.168.A.255";\n',
        "esperado_salida": "FUERA_DEL_ALFABETO\n",
        "justificacion": (
            "Compila; al ejecutar, 'A' no pertenece al alfabeto del AFN convertido."
        ),
    },
]

# Utilidades
def _ruta_tc(caso):
    return os.path.join(PROGRAMAS, caso["id"] + ".tc")

def _ruta_py(caso):
    return os.path.join(PROGRAMAS, caso["id"] + ".salida.py")

def escribir_fuentes():
    os.makedirs(PROGRAMAS, exist_ok=True)
    for caso in CASOS:
        with open(_ruta_tc(caso), "w", encoding="utf-8") as f: f.write(caso["fuente"])

def correr(cmd, cwd=BASE):
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = BASE if not pythonpath else BASE + os.pathsep + pythonpath
    return subprocess.run(
        cmd, cwd=cwd, env=env, capture_output=True, text=True,
        encoding="utf-8", timeout=30,
    )
    
def limpiar_salida(caso):
    if os.path.exists(_ruta_py(caso)):
        os.remove(_ruta_py(caso))

def compilar(caso):
    limpiar_salida(caso)
    return correr([
        sys.executable, "compilador.py", _ruta_tc(caso), "-o", _ruta_py(caso)
    ])

def ejecutar_generado(caso):
    return correr([sys.executable, _ruta_py(caso)])

# verificacion
def verificar(caso):
    r = compilar(caso)
    categoria = caso["categoria"]
    salida_comp = (r.stdout or "") + (r.stderr or "")
    if categoria in ("lexico", "sintactico","semantico"):
        if r.returncode == 0:
            return False, f"se esperaba error pero compilo: {salida_comp}"
        ns = norm(salida_comp)
        if norm(caso["esperado_etapa"]) not in ns:
            return False, f"falta etapa {caso['esperado_etapa']!r}: {salida_comp!r}"
        if not re.search(r"linea\s+\d+", ns):
            return False, f"falta 'línea N': {salida_comp!r}"
        if not re.search(r"columna\s+\d+", ns):
            return False, f"falta 'columna N': {salida_comp!r}"
        if norm(caso["esperado_motivo_substr"]) not in ns:
            return False, f"falta motivo{caso['esperado_motivo_substr']!r}: {salida_comp!r}"
        if os.path.exists(_ruta_py(caso)):
            return False, "se genero salida.py pese al error"
        return True, salida_comp.strip()
    
    # valido o fuera del alfabeto
    if r.returncode != 0:
        return False, f"no compilo: {salida_comp!r}"
    if not os.path.exists(_ruta_py(caso)):
        return False, "no se genero salida.py"
    e = ejecutar_generado(caso)
    if e.returncode != 0:
        return False, f"ejecución falló: {e.stderr!r}"
    if e.stdout != caso["esperado_salida"]:
        return False, (
            f"salida difiere: esp={caso['esperado_salida']!r} "
            f"obt={e.stdout!r}"
        )
    return True, e.stdout

# DEMO COMPLETO
def demo_completo():
    caso = next(c for c in CASOS if c["id"] == "v04_varias")
    ruta_tc = _ruta_tc(caso)
    ruta_py = _ruta_py(caso)
    limpiar_salida(caso)
    
    sec = ["=" * 78,
           "SECUENCIA COMPLETA — " + caso["id"],
           "=" * 78, "",
           "--- FUENTE (.tc) ---",
           caso["fuente"].rstrip(), ""]

    for opt, titulo in [
        ("--tokens", "TOKENS"),
        ("--ast", "AST"),
        ("--tabla", "TABLA DE SIMBOLOS"),
    ]:
        r = correr([sys.executable, "compilador.py", ruta_tc, opt])
        sec += [f"--- {titulo} ---", (r.stdout or r.stderr).rstrip(), ""]
    
    correr([sys.executable, "compilador.py", ruta_tc, "-o", ruta_py])
    sec+= ["--- CODIGO GENERADO (salida.py) ---"]
    if os.path.exists(ruta_py):
        with open(ruta_py, encoding="utf-8") as f:
            sec.append(f.read().rstrip())
    sec.append("")
    
    e = ejecutar_generado(caso)
    sec += ["---SALIDA (py salida.py) -- ", (e.stdout or e.stderr).rstrip(), ""]
    return "\n".join(sec)

# MAIN

def main():
    print(f"Generando {len(CASOS)} archivos .tc en ejemplos/pruebas/programas/...")
    escribir_fuentes()

    resultados = []
    for caso in CASOS:
        try:
            exito, detalle = verificar(caso)
        except Exception as exc:
            exito, detalle = False, f"excepción: {exc}"
        resultados.append((caso, exito, detalle))
        print(f"[{'OK  ' if exito else 'FAIL'}] {caso['id']:22} ({caso['categoria']})")

    ok = sum(1 for _, e, _ in resultados if e)
    print(f"\nTotal: {ok}/{len(CASOS)} OK\n")

    ruta_rep = os.path.join(PRUEBAS, "reporte_pruebas.txt")
    with open(ruta_rep, "w", encoding="utf-8") as f:
        f.write("=" * 78 + "\nREPORTE DE PRUEBAS — COMPILADOR .tc\n" + "=" * 78 + "\n\n")
        f.write(f"Total: {ok}/{len(CASOS)} OK\n\n")
        for caso, exito, detalle in resultados:
            f.write(f"[{'OK' if exito else 'FAIL'}] {caso['id']}\n")
            f.write(f"  Categoría: {caso['categoria']}\n")
            f.write(f"  Fuente:\n{caso['fuente']}\n")
            f.write(f"  Justificación: {caso['justificacion']}\n")
            if exito:
                label = "Resultado obtenido" if caso["categoria"] in (
                    "lexico", "sintactico", "semantico"
                ) else "Salida obtenida"
                f.write(f"  {label}: {detalle!r}\n")
            else:
                f.write(f"  FALLO: {detalle}\n")
            f.write("\n")
        f.write("\n" + demo_completo() + "\n")

    print(f"Reporte escrito en: {ruta_rep}")
    return 0 if ok == len(CASOS) else 1


if __name__ == "__main__":
    sys.exit(main())