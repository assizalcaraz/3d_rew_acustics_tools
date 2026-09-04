"""Cálculos de relevamiento REW: geometría, modos, triángulo, matriz de mic.

Celdas desconocidas quedan None / "FALTA MEDIR" — nunca 0 inventado ni #DIV/0.
Coordenadas REW: origen esquina frontal izquierda,
  X izquierda→derecha (ancho), Y frente→fondo (profundidad), Z piso→techo.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

FALTA = "FALTA MEDIR"
FALTA_POS = "Falta relevar posición."
C_SONIDO_DEFAULT = 343.0

# App 3D: L = profundidad (monitores en X≈L), W = ancho, H = alto tratamiento.
# REW: X = ancho, Y = profundidad, Z = alto.


def es_numero(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(float(v))


def num_o_none(v: Any) -> Optional[float]:
    if v is None or v == "" or v == FALTA:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(f):
        return None
    return f


def fmt_m(v: Optional[float], digits: int = 2) -> str:
    if v is None:
        return FALTA
    s = f"{v:.{digits}f}".replace(".", ",")
    return s


def punto_completo(p: Optional[Dict[str, Any]]) -> bool:
    if not p:
        return False
    return all(es_numero(p.get(k)) for k in ("x", "y", "z"))


def dist_xy(a: Dict[str, float], b: Dict[str, float]) -> float:
    return math.hypot(a["x"] - b["x"], a["y"] - b["y"])


def dist_xyz(a: Dict[str, float], b: Dict[str, float]) -> float:
    return math.sqrt(
        (a["x"] - b["x"]) ** 2 + (a["y"] - b["y"]) ** 2 + (a["z"] - b["z"]) ** 2
    )


# --- Conversión REW ↔ app 3D -------------------------------------------------

def rew_a_app(
    x: float, y: float, z: float,
    ancho: float, profundidad: float,
) -> Tuple[float, float, float]:
    """REW (x,y,z) → app (X,Y,Z). No rota Three.js."""
    app_x = profundidad - y  # frente Y=0 → X=L
    app_y = ancho - x        # izquierda X=0 → Y=W
    app_z = z
    return app_x, app_y, app_z


def app_a_rew(
    app_x: float, app_y: float, app_z: float,
    ancho: float, profundidad: float,
) -> Tuple[float, float, float]:
    rew_x = ancho - app_y
    rew_y = profundidad - app_x
    return rew_x, rew_y, app_z


# --- Modos de sala ------------------------------------------------------------

def clasificar_modo(nx: int, ny: int, nz: int) -> str:
    n_nonzero = sum(1 for n in (nx, ny, nz) if n > 0)
    if n_nonzero == 1:
        return "axial"
    if n_nonzero == 2:
        return "tangencial"
    return "oblicuo"


def calcular_modos(
    lx: float, ly: float, lz: float,
    c: float = C_SONIDO_DEFAULT,
    orden_max: int = 10,
    agrupamiento_hz: float = 3.0,
) -> List[Dict[str, Any]]:
    """f = c/2 √[(nx/Lx)²+(ny/Ly)²+(nz/Lz)²]. Ordenados por Hz."""
    if not all(es_numero(v) and v > 0 for v in (lx, ly, lz, c)):
        return []
    modos: List[Dict[str, Any]] = []
    for nx in range(orden_max + 1):
        for ny in range(orden_max + 1):
            for nz in range(orden_max + 1):
                if nx == 0 and ny == 0 and nz == 0:
                    continue
                if max(nx, ny, nz) > orden_max:
                    continue
                f = (c / 2.0) * math.sqrt(
                    (nx / lx) ** 2 + (ny / ly) ** 2 + (nz / lz) ** 2
                )
                modos.append({
                    "nx": nx, "ny": ny, "nz": nz,
                    "f_hz": round(f, 2),
                    "tipo": clasificar_modo(nx, ny, nz),
                    "etiqueta": f"{nx},{ny},{nz}",
                    "grupo": None,
                })
    modos.sort(key=lambda m: (m["f_hz"], m["nx"], m["ny"], m["nz"]))
    # Agrupar por proximidad en Hz
    grupo_id = 0
    i = 0
    while i < len(modos):
        j = i + 1
        while j < len(modos) and modos[j]["f_hz"] - modos[i]["f_hz"] <= agrupamiento_hz:
            j += 1
        if j - i >= 2:
            grupo_id += 1
            for k in range(i, j):
                modos[k]["grupo"] = grupo_id
        i = j if j > i + 1 else i + 1
    return modos


# --- Triángulo de monitoreo ---------------------------------------------------

def calcular_triangulo(
    L: Optional[Dict[str, Any]],
    R: Optional[Dict[str, Any]],
    M: Optional[Dict[str, Any]],
    margen_equilatero: float = 0.05,
    dist_objetivo: float = 1.0,
) -> Dict[str, Any]:
    """Distancias L–R, L–M, R–M, Δ, ángulo en M, alerta equilátero."""
    out: Dict[str, Any] = {
        "lr": FALTA, "lm": FALTA, "rm": FALTA,
        "delta_max": FALTA, "angulo_m_deg": FALTA,
        "equilatero": False, "aviso": None,
        "completo": False,
    }
    if not (punto_completo(L) and punto_completo(R) and punto_completo(M)):
        out["aviso"] = FALTA_POS
        return out

    lr = dist_xy(L, R)  # type: ignore[arg-type]
    lm = dist_xy(L, M)  # type: ignore[arg-type]
    rm = dist_xy(R, M)  # type: ignore[arg-type]
    delta = max(abs(lr - lm), abs(lr - rm), abs(lm - rm))

    # Ángulo en M (ley de cosenos)
    if lm > 1e-9 and rm > 1e-9:
        cos_a = (lm ** 2 + rm ** 2 - lr ** 2) / (2 * lm * rm)
        cos_a = max(-1.0, min(1.0, cos_a))
        ang = math.degrees(math.acos(cos_a))
    else:
        ang = None

    equi = (
        abs(lr - lm) <= margen_equilatero
        and abs(lr - rm) <= margen_equilatero
        and abs(lm - rm) <= margen_equilatero
    )
    out.update({
        "lr": round(lr, 3),
        "lm": round(lm, 3),
        "rm": round(rm, 3),
        "delta_max": round(delta, 3),
        "angulo_m_deg": round(ang, 1) if ang is not None else FALTA,
        "equilatero": equi,
        "completo": True,
        "dist_objetivo": dist_objetivo,
        "aviso": (
            "TRIÁNGULO APROXIMADAMENTE EQUILÁTERO"
            if equi else None
        ),
    })
    return out


def sugerir_monitoreo(
    ancho: float,
    profundidad: float,
    alto_oido: float = 1.20,
    dist_objetivo: float = 1.0,
    nearfield_desde_frente: Optional[float] = None,
) -> Dict[str, Any]:
    """Posición inicial sugerida (simetría / nearfield). No es verdad acústica."""
    if not all(es_numero(v) and v > 0 for v in (ancho, profundidad)):
        return {"L": None, "R": None, "operador": None, "aviso": FALTA}
    # Separación L–R ≈ dist_objetivo; operador en eje a dist_objetivo del centro LR
    cx = ancho / 2.0
    # Monitores cerca del frente
    y_mon = nearfield_desde_frente if es_numero(nearfield_desde_frente) else 0.35
    half = dist_objetivo / 2.0
    L = {"x": cx - half, "y": y_mon, "z": alto_oido}
    R = {"x": cx + half, "y": y_mon, "z": alto_oido}
    # Operador detrás, formando equilátero aproximado
    y_op = y_mon + (math.sqrt(3) / 2.0) * dist_objetivo
    if y_op >= profundidad - 0.3:
        y_op = min(profundidad * 0.55, profundidad - 0.4)
    op = {"x": cx, "y": y_op, "z": alto_oido}
    return {
        "L": {k: round(v, 3) for k, v in L.items()},
        "R": {k: round(v, 3) for k, v in R.items()},
        "operador": {k: round(v, 3) for k, v in op.items()},
        "aviso": (
            "Posición sugerida (simetría / nearfield). "
            "Validar con medición — no es verdad acústica."
        ),
    }


# --- Matriz de micrófonos -----------------------------------------------------

def matriz_mics(
    operador: Optional[Dict[str, Any]],
    d: float = 0.20,
    d2: float = 0.40,
    dz_vert: float = 0.20,
    incluir_corona: bool = True,
    incluir_verticales: bool = True,
) -> Dict[str, Any]:
    """M1 = oído; M2–M5 = Y+D, X−D, X+D, Y−D; M6–M9 corona; V1–V3 verticales."""
    result: Dict[str, Any] = {}
    labels_base = {
        "M1": (0, 0, 0),
        "M2": (0, d, 0),      # Y+D (hacia fondo)
        "M3": (-d, 0, 0),     # X−D (izquierda)
        "M4": (d, 0, 0),      # X+D (derecha)
        "M5": (0, -d, 0),     # Y−D (hacia frente)
    }
    if not punto_completo(operador):
        for lab in labels_base:
            result[lab] = {"x": None, "y": None, "z": None, "estado": FALTA_POS}
        if incluir_corona:
            for lab in ("M6", "M7", "M8", "M9"):
                result[lab] = {"x": None, "y": None, "z": None, "estado": FALTA_POS}
        if incluir_verticales:
            for lab in ("V1", "V2", "V3"):
                result[lab] = {
                    "x": None, "y": None, "z": None,
                    "estado": FALTA_POS,
                    "nota": "MEDICIÓN EXPLORATORIA — MODOS VERTICALES",
                }
        return result

    ox, oy, oz = float(operador["x"]), float(operador["y"]), float(operador["z"])  # type: ignore[index]
    for lab, (dx, dy, dz) in labels_base.items():
        result[lab] = {
            "x": round(ox + dx, 3),
            "y": round(oy + dy, 3),
            "z": round(oz + dz, 3),
            "estado": "calculado",
        }
    if incluir_corona:
        corona = {
            "M6": (0, d2, 0),
            "M7": (-d2, 0, 0),
            "M8": (d2, 0, 0),
            "M9": (0, -d2, 0),
        }
        for lab, (dx, dy, dz) in corona.items():
            result[lab] = {
                "x": round(ox + dx, 3),
                "y": round(oy + dy, 3),
                "z": round(oz + dz, 3),
                "estado": "calculado",
                "opcional": True,
            }
    if incluir_verticales:
        verts = {
            "V1": (0, 0, 0),
            "V2": (0, 0, dz_vert),
            "V3": (0, 0, -dz_vert),
        }
        for lab, (dx, dy, dz) in verts.items():
            result[lab] = {
                "x": round(ox + dx, 3),
                "y": round(oy + dy, 3),
                "z": round(oz + dz, 3),
                "estado": "calculado",
                "nota": "MEDICIÓN EXPLORATORIA — MODOS VERTICALES",
                "opcional": True,
            }
    return result


# --- Validación de posición ---------------------------------------------------

def validar_posicion(
    p: Optional[Dict[str, Any]],
    ancho: float,
    profundidad: float,
    alto: float,
    monitores: Optional[List[Dict[str, Any]]] = None,
    aberturas: Optional[List[Dict[str, Any]]] = None,
    obstaculos: Optional[List[Dict[str, Any]]] = None,
    umbral_pared: float = 0.30,
    umbral_monitor: float = 0.40,
    umbral_abertura: float = 0.40,
    umbral_obstaculo: float = 0.25,
) -> Dict[str, Any]:
    """Advertencias (no bloqueo)."""
    avisos: List[str] = []
    if not punto_completo(p):
        return {
            "valida": False,
            "avisos": [FALTA_POS],
            "dentro_sala": False,
        }
    x, y, z = float(p["x"]), float(p["y"]), float(p["z"])  # type: ignore[index]
    dentro = (
        0 < x < ancho and 0 < y < profundidad and 0 < z < alto
    )
    if not dentro:
        avisos.append("Fuera del recinto (o en el límite).")
    if x < umbral_pared or (ancho - x) < umbral_pared:
        avisos.append("Cerca de pared lateral.")
    if y < umbral_pared or (profundidad - y) < umbral_pared:
        avisos.append("Cerca de pared frontal/trasera.")
    if z < umbral_pared or (alto - z) < umbral_pared:
        avisos.append("Cerca de piso/techo.")

    for mon in monitores or []:
        if punto_completo(mon):
            if dist_xyz(p, mon) < umbral_monitor:  # type: ignore[arg-type]
                avisos.append("Cerca de monitor.")
                break

    for ab in aberturas or []:
        # Abertura con centro aproximado si hay datos; si faltan medidas, omitir
        cx = num_o_none(ab.get("centro_x"))
        cy = num_o_none(ab.get("centro_y"))
        if cx is not None and cy is not None:
            d = math.hypot(x - cx, y - cy)
            if d < umbral_abertura:
                avisos.append(f"Cerca de abertura {ab.get('id', '')}".strip())
                break

    for obs in obstaculos or []:
        if punto_completo(obs):
            if dist_xyz(p, obs) < umbral_obstaculo:  # type: ignore[arg-type]
                avisos.append("Cerca de obstáculo.")
                break

    return {
        "valida": dentro and not any("Fuera" in a for a in avisos),
        "dentro_sala": dentro,
        "avisos": avisos,
    }


# --- Estado del relevamiento --------------------------------------------------

def estado_campo(valor: Any, critico: bool = False) -> str:
    """Sí / No / parcial para checklist de inicio."""
    if valor is None or valor == "" or valor == FALTA:
        return "No" if critico else "No"
    if isinstance(valor, dict):
        nums = [num_o_none(v) for v in valor.values()]
        if all(v is not None for v in nums):
            return "Sí"
        if any(v is not None for v in nums):
            return "Parcial"
        return "No"
    if es_numero(valor):
        return "Sí"
    return "Sí"


def abertura_tiene_geometria(ab: Dict[str, Any]) -> bool:
    """Solo dibujar/usar abertura si hay medidas reales (no inventar)."""
    ancho = num_o_none(ab.get("ancho"))
    # Al menos ancho medido + una distancia de esquina
    d1 = num_o_none(ab.get("dist_esquina_a"))
    d2 = num_o_none(ab.get("dist_esquina_b"))
    return ancho is not None and ancho > 0 and (d1 is not None or d2 is not None)


def centro_abertura_en_pared(
    ab: Dict[str, Any],
    ancho_sala: float,
    profundidad_sala: float,
) -> Optional[Dict[str, float]]:
    """Centro 2D REW de una abertura si hay datos suficientes."""
    if not abertura_tiene_geometria(ab):
        return None
    pared = (ab.get("pared") or "").lower()
    w = float(ab["ancho"])
    d_a = num_o_none(ab.get("dist_esquina_a"))
    # Convención: dist_esquina_a = desde esquina "inicio" de la pared
    # derecha (X=ancho): Y desde frente (Y=0)
    # trasera (Y=profundidad): X desde izquierda (X=0)
    # izquierda (X=0): Y desde frente
    # frontal (Y=0): X desde izquierda
    if pared in ("derecha", "right", "der"):
        y0 = d_a if d_a is not None else None
        if y0 is None:
            return None
        return {"x": ancho_sala, "y": y0 + w / 2}
    if pared in ("trasera", "back", "fondo"):
        x0 = d_a if d_a is not None else None
        if x0 is None:
            return None
        return {"x": x0 + w / 2, "y": profundidad_sala}
    if pared in ("izquierda", "left", "izq"):
        y0 = d_a if d_a is not None else None
        if y0 is None:
            return None
        return {"x": 0.0, "y": y0 + w / 2}
    if pared in ("frontal", "frente", "front"):
        x0 = d_a if d_a is not None else None
        if x0 is None:
            return None
        return {"x": x0 + w / 2, "y": 0.0}
    return None


# --- Self-test ----------------------------------------------------------------

def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def self_test() -> None:
    # Vacíos no inventan
    tri = calcular_triangulo(None, None, None)
    _assert(tri["lr"] == FALTA, "tri vacío debe ser FALTA")
    _assert(tri["completo"] is False, "tri incompleto")

    mics = matriz_mics(None)
    _assert(mics["M1"]["estado"] == FALTA_POS, "M1 sin operador")
    _assert(mics["M1"]["x"] is None, "M1.x None")

    # Matriz derivada
    op = {"x": 1.5, "y": 1.2, "z": 1.2}
    mics = matriz_mics(op, d=0.2)
    _assert(mics["M1"]["x"] == 1.5 and mics["M1"]["y"] == 1.2, "M1 = operador")
    _assert(abs(mics["M2"]["y"] - 1.4) < 1e-9, "M2 Y+D")
    _assert(abs(mics["M3"]["x"] - 1.3) < 1e-9, "M3 X-D")
    _assert(abs(mics["M4"]["x"] - 1.7) < 1e-9, "M4 X+D")
    _assert(abs(mics["M5"]["y"] - 1.0) < 1e-9, "M5 Y-D")

    # Recalcula si se mueve
    op2 = {"x": 1.65, "y": 1.2, "z": 1.2}
    m2 = matriz_mics(op2, d=0.2)
    _assert(abs(m2["M1"]["x"] - 1.65) < 1e-9, "recalc M1")
    _assert(abs(m2["M4"]["x"] - 1.85) < 1e-9, "recalc M4")

    # Modos
    modos = calcular_modos(3.0, 3.2, 4.0, c=343, orden_max=2)
    _assert(len(modos) > 0, "hay modos")
    f100 = (343 / 2) * (1 / 3.0)  # axial X
    _assert(any(abs(m["f_hz"] - f100) < 0.1 for m in modos), "modo axial X")

    # Conversión coords
    ax, ay, az = rew_a_app(0, 0, 1.2, ancho=3.0, profundidad=3.2)
    _assert(abs(ax - 3.2) < 1e-9 and abs(ay - 3.0) < 1e-9, "frente-izq → L,W")
    rx, ry, rz = app_a_rew(ax, ay, az, ancho=3.0, profundidad=3.2)
    _assert(abs(rx) < 1e-9 and abs(ry) < 1e-9, "roundtrip")

    # Abertura sin medidas
    _assert(not abertura_tiene_geometria({"id": "A01", "pared": "derecha"}), "sin ancho")
    _assert(
        abertura_tiene_geometria({
            "id": "A01", "pared": "derecha", "ancho": 1.4, "dist_esquina_a": 0.8,
        }),
        "con medidas",
    )

    # Triángulo equilátero
    L = {"x": 1.0, "y": 0.5, "z": 1.2}
    R = {"x": 2.0, "y": 0.5, "z": 1.2}
    M = {"x": 1.5, "y": 0.5 + math.sqrt(3) / 2, "z": 1.2}
    t = calcular_triangulo(L, R, M, margen_equilatero=0.05)
    _assert(t["equilatero"] is True, "equilátero")
    _assert(t["aviso"] and "EQUILÁTERO" in t["aviso"], "aviso equi")

    print("rew_calculo self_test OK")


if __name__ == "__main__":
    self_test()
