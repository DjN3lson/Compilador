"""
benchmark.py — Mediciones de compilación y ejecución por separado.

Cumple Sección 7.3 del Proyecto II:
  - 3 tamaños crecientes de programas válidos de una misma familia.
  - >=5 repeticiones por tamaño y por fase.
  - Reporta mediana, mínimo y máximo.
  - Indica entorno y qué incluye cada medición.

Uso:
    py benchmark.py

Salida:
    pruebas/benchmark_salida.txt
"""
import os
import platform
import statistics
import subprocess
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
PRUEBAS = os.path.join(BASE, "ejemplos/pruebas")
BENCH = os.path.join(PRUEBAS, "benchmark")

REPETICIONES = 5
TAMANOS = [100, 1000, 5000]   # N = cantidad de declaraciones en la familia



# Familia de programas validos
def generar_programa(n):
    """
    Familia: N declaraciones seguidas de N sentencias 'mostrar'.

        let v1 = 1 + 1 * 2;
        ...
        let vN = N + N * 2;
        mostrar(v1);
        ...
        mostrar(vN);

    - Cada declaración ejercita: IDENT, NUM, '=', '+', '*', ';'.
    - Prioridad: i * 2 se calcula antes de sumar i.
    - Todas las variables se declaran antes de mostrarse.
    - Programa válido para cualquier N >= 1.
    """
    lineas = [f"let v{i} = {i} + {i} * 2;" for i in range(1, n + 1)]
    lineas += [f"mostrar(v{i});" for i in range(1, n + 1)]
    return "\n".join(lineas) + "\n"


def escribir_fuentes():
    os.makedirs(BENCH, exist_ok=True)
    rutas = {}
    for n in TAMANOS:
        ruta = os.path.join(BENCH, f"familia_{n}.tc")
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(generar_programa(n))
        rutas[n] = ruta
    return rutas



# Medición

def _correr(cmd, timeout=120):
    env = os.environ.copy()
    env["PYTHONPATH"] = BASE + os.pathsep + env.get("PYTHONPATH", "")
    t0 = time.perf_counter()
    r = subprocess.run(
        cmd, cwd=BASE, capture_output=True, text=True,
        encoding="utf-8", errors="replace",   # ← tolera em-dash, cp1252, etc.
        env=env, timeout=timeout,
    )
    t1 = time.perf_counter()
    return t1 - t0, r


def medir_compilacion(ruta_tc, ruta_py, reps):
    tiempos = []
    for _ in range(reps):
        if os.path.exists(ruta_py):
            os.remove(ruta_py)
        dt, r = _correr([sys.executable, "compilador.py", ruta_tc, "-o", ruta_py])
        if r.returncode != 0:
            raise RuntimeError(
                f"falló compilación: {(r.stdout or '') + (r.stderr or '')}"
            )
        tiempos.append(dt)
    return tiempos


def medir_ejecucion(ruta_py, reps):
    tiempos = []
    for _ in range(reps):
        dt, r = _correr([sys.executable, ruta_py])
        if r.returncode != 0:
            raise RuntimeError(
                f"falló ejecución: {(r.stdout or '') + (r.stderr or '')}"
            )
        tiempos.append(dt)
    return tiempos



# Entorno
def entorno():
    import multiprocessing
    return "\n".join([
        f"  Python:          {platform.python_version()} "
        f"({platform.python_implementation()})",
        f"  SO:              {platform.system()} {platform.release()} "
        f"({platform.machine()})",
        f"  Procesador:      {platform.processor() or 'no reportado'}",
        f"  CPUs lógicas:    {multiprocessing.cpu_count()}",
    ])


# ============================================================
# Formato del reporte
# ============================================================
def tabla_resultados(mediciones):
    lineas = [
        f"{'N':>6} {'Fase':12} {'mediana (ms)':>14} "
        f"{'min (ms)':>10} {'max (ms)':>10} {'reps':>5}"
    ]
    lineas.append("-" * 62)
    for n in TAMANOS:
        for fase in ("compilacion", "ejecucion"):
            ts = mediciones[n][fase]
            med = statistics.median(ts) * 1000
            lineas.append(
                f"{n:>6} {fase:12} {med:>14.2f} "
                f"{min(ts)*1000:>10.2f} {max(ts)*1000:>10.2f} {len(ts):>5}"
            )
    return "\n".join(lineas)


def analisis_escalamiento(mediciones):
    lineas = ["=" * 78, "ANÁLISIS DE ESCALAMIENTO", "=" * 78, ""]
    for fase in ("compilacion", "ejecucion"):
        lineas.append(f"Fase: {fase}")
        n0 = TAMANOS[0]
        t0 = statistics.median(mediciones[n0][fase])
        for n in TAMANOS:
            t = statistics.median(mediciones[n][fase])
            fn = n / n0
            ft = t / t0 if t0 > 0 else float("inf")
            lineas.append(
                f"  N={n:>5}  mediana={t*1000:8.2f} ms  "
                f"(factor_n={fn:5.1f}, factor_t={ft:5.2f})"
            )
        lineas.append("")
    lineas += [
        "Interpretación:",
        "  - factor_t ≈ factor_n  -> escalamiento aproximadamente lineal.",
        "  - factor_t < factor_n  -> overhead constante (arranque, I/O) domina.",
        "  - factor_t > factor_n  -> componente superlineal a documentar.",
        "",
    ]
    return "\n".join(lineas)


# MAIN
def main():
    print("Entorno:")
    print(entorno())
    print(f"\nTamaños: {TAMANOS}")
    print(f"Repeticiones por tamaño y fase: {REPETICIONES}\n")

    rutas = escribir_fuentes()
    mediciones = {}

    for n in TAMANOS:
        ruta_tc = rutas[n]
        ruta_py = os.path.join(BENCH, f"familia_{n}.salida.py")

        print(f"[N={n:>5}] midiendo compilación ...", end=" ", flush=True)
        ts_c = medir_compilacion(ruta_tc, ruta_py, REPETICIONES)
        print(f"mediana {statistics.median(ts_c)*1000:.2f} ms")

        print(f"[N={n:>5}] midiendo ejecución   ...", end=" ", flush=True)
        ts_e = medir_ejecucion(ruta_py, REPETICIONES)
        print(f"mediana {statistics.median(ts_e)*1000:.2f} ms")

        mediciones[n] = {"compilacion": ts_c, "ejecucion": ts_e}

    tabla = tabla_resultados(mediciones)
    escal = analisis_escalamiento(mediciones)

    reporte = (
        "=" * 78 + "\n"
        "BENCHMARK — COMPILACIÓN vs EJECUCIÓN\n"
        "Proyecto II: Compilador .tc (LIS-3042)\n"
        "Equipo: Pablo y Uri\n"
        "=" * 78 + "\n\n"
        "ENTORNO\n" + "-" * 78 + "\n" + entorno() + "\n\n"

        "FAMILIA DE PROGRAMAS\n" + "-" * 78 + "\n"
        "  let v1 = 1 + 1 * 2;\n"
        "  ...\n"
        "  let vN = N + N * 2;\n"
        "  mostrar(v1);\n"
        "  ...\n"
        "  mostrar(vN);\n\n"
        "  Tamaño N = cantidad de declaraciones (y de mostrar).\n"
        "  Todas las declaraciones van antes de los mostrar.\n"
        f"  Tamaños probados: {TAMANOS}\n"
        f"  Repeticiones por tamaño y fase: {REPETICIONES}\n\n"

        "QUÉ INCLUYE CADA MEDICIÓN\n" + "-" * 78 + "\n"
        "  Compilación: subprocess que ejecuta\n"
        "      py compilador.py familia_N.tc -o familia_N.salida.py\n"
        "    Incluye:\n"
        "      - arranque del intérprete Python,\n"
        "      - lectura del archivo .tc,\n"
        "      - lexer + parser + AST + análisis semántico,\n"
        "      - generación de código y escritura del .py,\n"
        "      - terminación del proceso.\n\n"
        "  Ejecución: subprocess que ejecuta\n"
        "      py familia_N.salida.py\n"
        "    Incluye:\n"
        "      - arranque del intérprete Python,\n"
        "      - import del módulo automatas.py,\n"
        "      - evaluación de expresiones y construcción\n"
        "        de cadenas para print,\n"
        "      - escritura de stdout (capturada por subprocess).\n\n"
        "  No incluye:\n"
        "      - generación de los archivos .tc (ya existen antes de medir),\n"
        "      - compilación a bytecode de Python (puede ocurrir la primera vez).\n\n"

        "RESULTADOS (mediana de {} repeticiones)\n".format(REPETICIONES)
        + "-" * 78 + "\n" + tabla + "\n\n"

        + escal

        + "=" * 78 + "\n"
        "NOTAS PARA EL REPORTE\n" + "=" * 78 + "\n"
        "  - La componente de arranque del intérprete Python (~30-50 ms) está\n"
        "    incluida en cada medición. Por eso los N pequeños pagan un costo\n"
        "    constante grande en proporción al trabajo real.\n"
        "  - Para N grandes, el trabajo del compilador y del programa generado\n"
        "    domina el arranque y el escalamiento tiende a lineal.\n"
        "  - Estas mediciones apoyan el análisis asintótico del reporte, pero\n"
        "    no lo demuestran por sí solas (Sección 7.3 del PDF).\n"
    )

    ruta_out = os.path.join(PRUEBAS, "benchmark_salida.txt")
    with open(ruta_out, "w", encoding="utf-8") as f:
        f.write(reporte)

    print()
    print(tabla)
    print()
    print(f"Reporte guardado en: {ruta_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())