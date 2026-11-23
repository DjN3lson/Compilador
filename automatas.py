
"""
    automatas.py — Módulo de apoyo del compilador .tc (Proyecto II).

Reutiliza AFD.ipynb y AFN-v2.ipynb tal cual están.
Añade:
  - convertir_afn_a_afd(): algoritmo de subconjuntos.
  - validar(modelo, cadena): API para salida.py.

No importa el compilador. Solo stdlib.
"""
    
# AFD ORIGINAL - IPV4 con 0-255 en los 4 octetos

alfabeto = {"0", "1", "2", "3", "4",
            "5", "6", "7", "8", "9", "."}
AFD_ORIGINAL={
    "estados": set(),
    "inicial":"A0",
    "alfabeto": alfabeto,
    "aceptacion": set(),
    "delta": {}
}

for letra in ["A", "B", "C", "D"]:
    for numero in range(1,13):
        AFD_ORIGINAL["estados"].add(letra+str(numero))
AFD_ORIGINAL["estados"].add("T")
for numero in range(1,13):
    AFD_ORIGINAL["aceptacion"].add("D" + str(numero))

tabla = {
    0: {"0": 1, "1": 2, "2": 3},
    1: {}, 2: {}, 3: {"5": 7}, 4: {}, 5: {}, 6: {},
    7: {}, 8: {}, 9: {}, 10: {}, 11: {}, 12: {}
}    

for d in "3456789":
    tabla[0][d] = 4
for d in "0123456789":
    tabla[2][d] = 5
for d in "01234":
    tabla[3][d] = 6
for d in "6789":
    tabla[3][d] = 8
for d in "0123456789":
    tabla[4][d] = 9
    tabla[5][d] = 10
    tabla[6][d] = 11
for d in "012345":
    tabla[7][d] = 12

letras = ["A", "B", "C", "D"]
for i in range(4):
    letra = letras[i]
    for numero in range(13):
        estado = letra + str(numero)
        for simbolo in AFD_ORIGINAL["alfabeto"]:
            destino = "T"
            if simbolo == ".":
                if numero != 0 and i < 3:
                    destino = letras[i + 1] + "0"
            elif simbolo in tabla[numero]:
                destino = letra + str(tabla[numero][simbolo])
            AFD_ORIGINAL["delta"][(estado, simbolo)] = destino
for simbolo in AFD_ORIGINAL["alfabeto"]:
    AFD_ORIGINAL["delta"][("T", simbolo)] = "T"
    
# AFN original
alfabeto_afn = {"0", "1", "2", "3", "4",
            "5", "6", "7", "8", "9", "."}

AFN_ORIGINAL = {
    "estados": set(),
    "inicial": "A0",
    "alfabeto": alfabeto_afn,
    "aceptacion": set(),
    "delta": {}
}

_digitos = "0123456789"
def _agregar_octeto(prefijo, es_ultimo=False, siguiente_inicial=None):
    for i in range(13):
        AFN_ORIGINAL["estados"].add(f"{prefijo}{i}")
    
    def t(origen, simbolo, destinos):
        AFN_ORIGINAL["delta"][(origen, simbolo)] = set(destinos)
    
    #primer digito
    t(f"{prefijo}0", "0", [f"{prefijo}1"])
    t(f"{prefijo}0", "1", [f"{prefijo}2"])
    t(f"{prefijo}0", "2", [f"{prefijo}3"])
    for d in "3456789":
        t(f"{prefijo}0", d, [f"{prefijo}4"])
    # segundo digito
    for d in _digitos:
        t(f"{prefijo}2", d, [f"{prefijo}5"])
        t(f"{prefijo}4", d, [f"{prefijo}9"])
        t(f"{prefijo}5", d, [f"{prefijo}10"])
        t(f"{prefijo}6", d, [f"{prefijo}11"])
    for d in "01234":
        t(f"{prefijo}3", d, [f"{prefijo}6"])
    t(f"{prefijo}3", "5", [f"{prefijo}7"])
    for d in "6789":
        t(f"{prefijo}3", d, [f"{prefijo}8"])
    for d in "012345":
        t(f"{prefijo}7", d, [f"{prefijo}12"])
    # cierre del octeto
    for i in range(1, 13):
        if es_ultimo:
            AFN_ORIGINAL["aceptacion"].add(f"{prefijo}{i}")
        elif siguiente_inicial is not None:
            t(f"{prefijo}{i}", ".", [siguiente_inicial])

_agregar_octeto("A", es_ultimo=False, siguiente_inicial="B0")
_agregar_octeto("B", es_ultimo=False, siguiente_inicial="C0")
_agregar_octeto("C", es_ultimo=False, siguiente_inicial="D0")
_agregar_octeto("D", es_ultimo=True)

# SIMULADORES del AFN y AFD
def ejecutar(afd, cadenas):
    estado = afd["inicial"]
    for simbolo in cadenas:
        if simbolo not in afd["alfabeto"]:
            return False
        estado = afd["delta"][(estado,simbolo)]
    return estado in afd["aceptacion"]

def leeCadena(afn, cadena, debug=False):
    activos = {afn["inicial"]}
    for posicion, simbolo in enumerate(cadena, start=1):
        if simbolo not in afn["alfabeto"]:
            if debug:
                print(f"Simbolo fuera del alfabeto en posicion {posicion}: {simbolo!r}")
            return False
        siguiente=set()
        for estado in activos:
            siguiente.update(afn["delta"].get((estado, simbolo), set()))
        if not siguiente:
            if debug:
                print(f"Sin transicion en posicion {posicion}")
            return False
        activos = siguiente
    aceptada = bool(activos & afn["aceptacion"])
    if debug and not aceptada:
        print(f"Termino en estado(s) no finales: {sorted(activos)}")
    return aceptada

# 4 Conversion AFN -> AFD
def convertir_afn_a_afd(afn):
    """
    Construcción de subconjuntos. Sin épsilon-clausuras: el AFN del
    Proyecto I no tiene transiciones epsilon.

    Devuelve un dict compatible con `ejecutar`, más:
        "correspondencia": { nombre_AFD : frozenset(estados_AFN) }
        "tabla_subconjuntos": [(nombre, frozenset), ...] ordenado
    """

    inicial = frozenset({afn["inicial"]})
    nombres = {inicial:"S0"}
    cola = [inicial]
    siguiente_id = 1
    delta={}
    aceptacion = set()
    
    idx = 0
    while idx < len(cola):
        conjunto = cola[idx]
        idx += 1
        nombre = nombres[conjunto]
        if conjunto & afn["aceptacion"]:
            aceptacion.add(nombre)
        for simbolo in sorted(afn["alfabeto"]):
            destino = set()
            for estado in conjunto:
                destino.update(afn["delta"].get((estado, simbolo), set()))
            destino_fs = frozenset(destino)
            if destino_fs not in nombres:
                nombres[destino_fs] = f"S{siguiente_id}"
                siguiente_id += 1
                cola.append(destino_fs)
            delta[(nombre, simbolo)] = nombres[destino_fs]
    
    #Conjunto vacio es el estado trampa: renombrarlo para el reporte
    if frozenset() in nombres:
        viejo = nombres[frozenset()]
        nombres[frozenset()] = "TRAMPA"
        delta={
            (("TRAMPA" if e == viejo else e), s):
            ("TRAMPA" if d == viejo else d)
            for (e, s), d in delta.items()
        }
        aceptacion = {("TRAMPA" if a == viejo else a) for a in aceptacion}
    
    correspondencia = {nombre: conjunto for conjunto, nombre in nombres.items()}
    
    def _orden(kv):
        nombre = kv[0]
        if nombre == "TRAMPA":
            return (1,0)
        return (0, int(nombre[1:]))
    
    return{
        "estado": set(correspondencia.keys()),
        "inicial":"S0",
        "alfabeto": set(afn["alfabeto"]),
        "aceptacion": aceptacion,
        "delta": delta,
        "correspondencia": correspondencia,
        "tabla_subconjuntos": sorted(correspondencia.items(), key=_orden),
    }
    
AFD_CONVERTIDO = convertir_afn_a_afd(AFN_ORIGINAL)

#API
def validar(modelo, cadena):
    """
    modelo == "afd" --> AFD_ORIGINAL
    modelo == "afn" --> AFN_CONVERTIDO (subconjuntos del AFN)
    devuelve "ACEPTA" | "RECHAZA" | "FUERA DEL ALFABETO" 
    """
    if not isinstance(cadena, str):
        raise TypeError("cadena deber ser str")
    if modelo == "afd":
        aut = AFD_ORIGINAL
    elif modelo == "afn":
        aut = AFN_ORIGINAL
    else:
        raise ValueError(f"modelo desconocido: {modelo!r}")
    if any(s not in aut["alfabeto"] for s in cadena):
        return "FUERRA DEL ALFABETO"
    return "ACEPTA" if ejecutar(aut, cadena) else "RECHAZA"

#EVIDENCIA
def _tabla_subconjuntos():
    print("=" * 78)
    print("TABLA DE SUBCONJUNTOS ALCANZABLES (AFN -> AFD)")
    print("=" * 78)
    print(f"Inicial: {AFD_CONVERTIDO['inicial']}")
    print(f"Finales: {sorted(AFD_CONVERTIDO['aceptacion'])}")
    print()
    print(f"{'Nuevo':8} {'Conjunto del AFN':48} {'Acepta?'}")
    print("-" * 78)
    for nombre, conjunto in AFD_CONVERTIDO["tabla_subconjuntos"]:
        etiqueta = "vacio (trampa)" if not conjunto else "{" + ", ".join(sorted(conjunto)) + "}"
        acepta = "Si" if nombre in AFD_CONVERTIDO["aceptacion"] else "No"
        print(f"{nombre:8} {etiqueta:48} {acepta}")
    print()
    print(f"Resumen: {len(AFD_CONVERTIDO['estados'])} estados, "
          f"{len(AFD_CONVERTIDO['aceptacion'])} de aceptacion, "
          f"{len(AFD_CONVERTIDO['delta'])} transiciones")
    print()

def _regresion():
    casos_afd = [
        ("10.0.0.1", "ACEPTA"),
        ("172.16.0.1", "ACEPTA"),
        ("192.168.1.10", "ACEPTA"),
        ("224.0.0.1", "ACEPTA"),
        ("255.255.255.255", "ACEPTA"),
        ("256.1.1.1", "RECHAZA"),
        ("192.168.1", "RECHAZA"),
        ("192..1.10", "RECHAZA"),
        ("01.2.3.4", "RECHAZA"),
        ("192.168.1.999", "RECHAZA"),
        ("", "RECHAZA"),
        ("192.168.A.1", "FUERA_DEL_ALFABETO"),
    ]
    casos_afn =[
        ("192.168.1.100", "ACEPTA"),
        ("10.0.0.255", "ACEPTA"),
        ("172.16.0.50", "ACEPTA"),
        ("224.1.2.0", "ACEPTA"),
        ("255.255.255.255", "ACEPTA"),
        ("300.1.2.25", "RECHAZA"),
        ("192.168.1.256", "RECHAZA"),
        ("10.0.0.999", "RECHAZA"),
        ("172.16.1.01", "RECHAZA"),
        ("192.168.1", "RECHAZA"),
        ("", "RECHAZA"),
        ("192.168.A.255", "FUERA_DEL_ALFABETO")
    ]
    fallos = 0
    print("="*78)
    print("REGRESION AFD ORIGINAL (12 casos)")
    print("="*78)
    for cadena, esperado in casos_afd:
        obtenido = validar("afd", cadena)
        ok = obtenido == esperado
        fallos += 0 if ok else 1
        marca ="OK " if ok else "FAIL"
        print(f"marca={marca} cadena={cadena!r:25} esp={esperado:20} obt={obtenido}")
    print()
    
    print("=" * 78)
    print("REGRESION AFN ORIGINAL vs AFD CONVERTIDO (12 casos)")
    print("=" * 78)
    print(f"{'':4} {'Cadena':22} {'Esperado':20} {'AFN orig':12} {'AFD conv':12}")
    print("-" * 78)
    for cadena, esperado in casos_afn:
        if any(s not in AFN_ORIGINAL["alfabeto"] for s in cadena):
            res_afn = "FUERA DEL ALFABETO"
        else:
            res_afn = "ACEPTA" if leeCadena(AFN_ORIGINAL, cadena) else "RECHAZA"
        res_conv = validar("afn", cadena)
        ok = (res_afn == esperado == res_conv)
        fallos += 0 if ok else 1
        marca = "OK " if ok else "FAIL"
        print(f"marca={marca} cadena={cadena!r:23} esp={esperado:20} res_afn={res_afn:12} res_conv={res_conv:12}")
    print()
    
    print("="*78)
    if fallos == 0:
        print("OK - regresion completa sin fallos")
    else:
        print(f"Fallos: {fallos}")
    
    if __name__ == "__main__":
        _tabla_subconjuntos()
        raise SystemExit(_regresion())