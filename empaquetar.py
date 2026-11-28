"""
empaquetar.py — Genera el ZIP de entrega del Proyecto II.

Uso:
    py empaquetar.py

Genera:
    EquipoPabloyUri_ProyectoII.zip en la raíz del proyecto.

Pasos:
    1. Valida precondiciones (archivos raíz, 20 programas, smoke test)
    2. Auto-repara programas/ si detecta archivos viejos o faltantes
    3. Copia archivos a staging temporal (excluye __pycache__, .pyc, notas internas)
    4. Crea el ZIP con carpeta raíz EquipoPabloyUri_ProyectoII/
    5. Extrae en carpeta temporal y corre smoke test end-to-end
    6. Limpia staging
"""
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent
NOMBRE_EQUIPO = "EquipoPabloyUri"
NOMBRE_PROYECTO = f"{NOMBRE_EQUIPO}_ProyectoII"
ZIP_PATH = BASE / f"{NOMBRE_PROYECTO}.zip"

# Archivos en la raíz que SÍ van al ZIP
ARCHIVOS_RAIZ = [
    "compilador.py", "lexer.py", "parser.py", "semantica.py", "generador.py",
    "automatas.py", "benchmark.py", "test_lexer.py", "README.md",
    ".gitignore",
    "Cambios que se hicieron en el automata AFN.txt",
    "compiler-diagram.drawio",
]

# Carpetas que SÍ van (relativas a BASE)
CARPETAS_INCLUIR = ["AFDyAFN", "ejemplos"]

# Excluidos en cualquier nivel
EXCLUIR_DIRS = {"__pycache__", ".ipynb_checkpoints", ".git", ".vscode"}
EXCLUIR_ARCHIVOS = {"Lista de Tareas.txt", "salida.py", "_smoke_test.py", "salida_test.py"}

# IDs base de los 20 programas
IDS_20 = (
    [f"v0{i}" for i in range(1, 7)]
    + [f"l0{i}" for i in range(1, 5)]
    + [f"s0{i}" for i in range(1, 5)]
    + [f"m0{i}" for i in range(1, 5)]
    + ["a01", "a02"]
)

SALIDA_DEMO_ESPERADA = "14\n20\nACEPTA\nACEPTA"


def _header(titulo):
    print("=" * 70)
    print(titulo)
    print("=" * 70)


def _run(cmd, cwd):
    return subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )


# ============================================================
# AUTO-REPARACIÓN DE programas/
# ============================================================
def _correr_runner(razon):
    print(f"        Corriendo runner ({razon})...")
    r = _run([sys.executable, "ejemplos/pruebas/ejecutar_pruebas.py"], BASE)
    if r.returncode != 0:
        print("        Runner FALLO:")
        print((r.stdout or "") + (r.stderr or ""))
        return False
    ok = "20/20 OK" in (r.stdout or "") or "Total: 20/20" in (r.stdout or "")
    print(f"        Runner OK{' (20/20)' if ok else ''}")
    return True


def asegurar_programas():
    programas = BASE / "ejemplos" / "pruebas" / "programas"
    if not programas.exists():
        return _correr_runner("no existe programas/")

    tcs = {p.stem for p in programas.glob("*.tc")}

    viejos = [t for t in tcs if t.startswith("101_") or t.startswith("so")]
    if viejos:
        print(f"        Borrando archivos viejos: {sorted(viejos)}")
        for v in viejos:
            (programas / f"{v}.tc").unlink(missing_ok=True)
            (programas / f"{v}.salida.py").unlink(missing_ok=True)
        tcs -= set(viejos)

    faltantes = []
    for base_id in IDS_20:
        if not any(t.startswith(base_id + "_") for t in tcs):
            faltantes.append(base_id)

    if faltantes:
        return _correr_runner(f"faltan {len(faltantes)}: {faltantes}")

    # Asegurar que los 8 .salida.py de válidos + fuera_alfabeto existan
    salidas_esperadas = [f"v0{i}" for i in range(1, 7)] + ["a01", "a02"]
    faltan_sal = []
    for base_id in salidas_esperadas:
        matches = list(programas.glob(f"{base_id}_*.salida.py"))
        if not matches:
            faltan_sal.append(base_id)
    if faltan_sal:
        return _correr_runner(f"faltan salidas de: {faltan_sal}")

    return True


# ============================================================
# VALIDACIONES
# ============================================================
def validar_precondiciones():
    print("[1/6] Validando precondiciones...")

    faltantes = [a for a in ARCHIVOS_RAIZ if not (BASE / a).exists()]
    if faltantes:
        print(f"      ERROR: faltan archivos en raiz: {faltantes}")
        return False

    print("      Archivos raiz: OK")

    print("      Verificando 20 programas...")
    if not asegurar_programas():
        print("      ERROR: no se pudieron preparar los 20 programas")
        return False
    print("      20 programas: OK")

    print("      Smoke test: compilar demo.tc...")
    smoke = BASE / "_smoke_test.py"
    try:
        r = _run(
            [sys.executable, "compilador.py", "ejemplos/demo.tc", "-o", "_smoke_test.py"],
            BASE,
        )
        if r.returncode != 0:
            print(f"      ERROR compilando: {(r.stdout + r.stderr)[:300]}")
            return False
        r2 = _run([sys.executable, "_smoke_test.py"], BASE)
        if r2.returncode != 0:
            print(f"      ERROR ejecutando: {(r2.stdout + r2.stderr)[:300]}")
            return False
        if r2.stdout.strip() != SALIDA_DEMO_ESPERADA:
            print(f"      ADVERTENCIA: salida inesperada: {r2.stdout!r}")
        else:
            print(f"      Smoke test: OK ({SALIDA_DEMO_ESPERADA.replace(chr(10), ' / ')})")
    finally:
        smoke.unlink(missing_ok=True)

    print()
    return True


# ============================================================
# COPIAR A STAGING
# ============================================================
def _iter_archivos(raiz):
    for actual, dirs, files in os.walk(raiz):
        dirs[:] = [d for d in dirs if d not in EXCLUIR_DIRS]
        for f in files:
            if f in EXCLUIR_ARCHIVOS or f.endswith(".pyc"):
                continue
            yield Path(actual) / f


def copiar_proyecto(staging):
    print("[2/6] Copiando archivos a staging...")
    staging.mkdir(parents=True, exist_ok=True)

    for a in ARCHIVOS_RAIZ:
        src = BASE / a
        if src.exists():
            shutil.copy2(src, staging / a)

    for carpeta in CARPETAS_INCLUIR:
        src = BASE / carpeta
        if not src.exists():
            continue
        for archivo in _iter_archivos(src):
            rel = archivo.relative_to(BASE)
            target = staging / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(archivo, target)

    n = sum(1 for _ in staging.rglob("*") if _.is_file())
    print(f"      OK - {n} archivos copiados")
    print()


# ============================================================
# CREAR ZIP
# ============================================================
def crear_zip(staging):
    print("[3/6] Creando ZIP...")
    ZIP_PATH.unlink(missing_ok=True)
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for archivo in staging.rglob("*"):
            if archivo.is_file():
                rel = archivo.relative_to(staging).as_posix()
                zf.write(archivo, f"{NOMBRE_PROYECTO}/{rel}")
    kb = ZIP_PATH.stat().st_size / 1024
    print(f"      OK - {ZIP_PATH.name} ({kb:.1f} KB)")
    print()


# ============================================================
# VERIFICAR ZIP (extraer + smoke test)
# ============================================================
def verificar_zip():
    print("[4/6] Verificando ZIP (extraer en carpeta temporal)...")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        with zipfile.ZipFile(ZIP_PATH, "r") as zf:
            zf.extractall(tmp_path)

        proyecto = tmp_path / NOMBRE_PROYECTO
        if not proyecto.exists():
            print(f"      ERROR: no existe {NOMBRE_PROYECTO}/ dentro del ZIP")
            return False

        print(f"      Extraido en: {NOMBRE_PROYECTO}/")

        faltantes = [f for f in ["compilador.py", "automatas.py", "README.md"]
                     if not (proyecto / f).exists()]
        if faltantes:
            print(f"      ERROR: faltan {faltantes} en el ZIP")
            return False

        print("      Smoke test desde carpeta nueva...")
        r = _run(
            [sys.executable, "compilador.py", "ejemplos/demo.tc", "-o", "salida_test.py"],
            proyecto,
        )
        if r.returncode != 0:
            print(f"      ERROR compilando: {(r.stdout + r.stderr)[:300]}")
            return False
        r2 = _run([sys.executable, "salida_test.py"], proyecto)
        if r2.returncode != 0:
            print(f"      ERROR ejecutando: {(r2.stdout + r2.stderr)[:300]}")
            return False
        if r2.stdout.strip() != SALIDA_DEMO_ESPERADA:
            print(f"      ADVERTENCIA: salida inesperada: {r2.stdout!r}")
        else:
            print(f"      Smoke test: OK ({SALIDA_DEMO_ESPERADA.replace(chr(10), ' / ')})")

        (proyecto / "salida_test.py").unlink(missing_ok=True)

    print()
    return True


# ============================================================
# CIERRE
# ============================================================
def reporte_final(staging):
    print("[5/6] Limpieza del staging...")
    shutil.rmtree(staging, ignore_errors=True)
    print("      OK")
    print()

    print("[6/6] Resultado final:")
    kb = ZIP_PATH.stat().st_size / 1024
    print(f"      ZIP:    {ZIP_PATH.name} ({kb:.1f} KB)")
    print(f"      Ruta:   {ZIP_PATH}")
    print()
    print("      Sube este ZIP a Blackboard en la actividad:")
    print("      'Proyecto II - Compilador (equipo)'")
    print()


def main():
    _header("EMPAQUETAR - Proyecto II")
    print(f"Proyecto: {BASE}")
    print()

    if not validar_precondiciones():
        print("\nCorrige los errores y vuelve a correr.")
        return 1

    staging = BASE / f"_staging_{NOMBRE_PROYECTO}"
    if staging.exists():
        shutil.rmtree(staging, ignore_errors=True)

    try:
        copiar_proyecto(staging)
        crear_zip(staging)
        if not verificar_zip():
            print("Verificacion del ZIP fallo.")
            return 1
        reporte_final(staging)
    except Exception as exc:
        print(f"\nERROR inesperado: {exc}")
        shutil.rmtree(staging, ignore_errors=True)
        return 1

    _header("LISTO")
    return 0


if __name__ == "__main__":
    sys.exit(main())