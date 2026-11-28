# Proyecto II — Compilador del lenguaje `.tc`

**Curso:** LIS-3042 Teoría de la Computación  
**Equipo:** Pablo Carmona Sánchez, Uri Yael Serrano Sánchez  
**Profesor:** Dr. Edwin Montes Orozco  
**Entrega:** 4 de diciembre de 2026, 23:59 h (Blackboard)  
**Institución:** Universidad de las Américas Puebla

Compilador para un lenguaje pequeño que declara variables enteras, evalúa
expresiones aritméticas, imprime resultados y valida direcciones IPv4 con
los autómatas del Proyecto I (AFD original y AFN convertido a AFD).

El compilador hace visibles las cinco etapas: análisis léxico, análisis
sintáctico, construcción del AST, comprobaciones semánticas y generación
de código Python.

---

## 1. Requisitos

- **Python 3.12.6** (versión probada en la entrega). Funciona en 3.10+.
- Sistema probado: Windows 11 (AMD64). También funciona en Linux y macOS.
- No requiere dependencias externas. Solo biblioteca estándar.

En Windows, si `python` no está disponible pero `py` sí:

```powershell
py --version