# Guía Rápida de Mediciones REW

## 🚀 Inicio Rápido (5 pasos)

### 1. Abrir Aplicación
```bash
# Abrir en navegador:
file:///workspace/render.html

# O servidor local:
python3 -m http.server 8000
# → http://localhost:8000/render.html
```

### 2. Activar Modo REW
- Click en botón **"Relevamiento REW"** (arriba derecha)

### 3. Medir Sala
```
Geometría + coords:
├─ Ancho X (m):       [___] (izq → der)
├─ Profundidad Y (m): [___] (frente → fondo)
└─ Alto Z (m):        [___] (piso → techo)
```

### 4. Configurar Monitoreo
```
Opción A: Click "Aplicar sugerencia simétrica"
Opción B: Medir manualmente L, R, Operador
```

### 5. Leer Posiciones de Micrófono
```
Tabla "Posiciones de mic" → coordenadas M1-M5
```

---

## 📐 Sistema de Coordenadas

```
     ┌─────────── Y (profundidad) ────────────┐
     │                                         │
     │  FRENTE                                 │
     │  ▼                                      │
     │  •─────────────────────────────────────│  ← X (ancho)
     │  │           🔵 L    M    🔵 R         │
  Z  │  │               🪑 Op                 │
  ↑  │  │                                     │
     │  │                                     │
     │  │                                     │
     │  └─────────────────────────────────────│
     │                 FONDO                   │
     └─────────────────────────────────────────┘
     
Origen (0,0,0) = esquina frontal izquierda del piso
```

---

## 📋 Checklist de Campo

### Equipamiento
```
☐ Laptop con REW
☐ Micrófono de medición calibrado
☐ Interfaz de audio
☐ Pie de micrófono
☐ Cinta métrica / láser
☐ Cables XLR/TRS
☐ Archivo de calibración (.txt)
☐ Esta guía impresa
```

### Pre-Medición
```
☐ Sala cerrada (puertas/ventanas)
☐ Ventiladores/AC apagados
☐ Monitores en posición final
☐ REW configurado (sample rate 48k)
☐ Calibración cargada
☐ Barrido de prueba OK
```

---

## 🎯 Secuencia de Medición

### Para cada posición M1 → M5:

**1. Colocar Mic**
- Buscar coordenadas X, Y, Z en tabla
- Medir con cinta/láser
- Pie ajustado a altura Z
- Micrófono apuntando al techo (omni) o monitor (direccional)

**2. Medir Monitor L**
```
REW → Measure
Nombre: 01_ACTUAL_L_M1
Click OK
Esperar barrido
Save
```

**3. Medir Monitor R**
```
REW → Measure
Nombre: 02_ACTUAL_R_M1
Click OK
Esperar barrido
Save
```

**4. Próxima posición**
```
M1 → M2 → M3 → M4 → M5
```

---

## 📊 Nomenclatura de Archivos

```
01_ACTUAL_L_M1.mdat    ← Estado actual, monitor izq, posición 1
02_ACTUAL_R_M1.mdat
03_ACTUAL_L_M2.mdat
04_ACTUAL_R_M2.mdat
05_ACTUAL_L_M3.mdat
06_ACTUAL_R_M3.mdat
07_ACTUAL_L_M4.mdat
08_ACTUAL_R_M4.mdat
09_ACTUAL_L_M5.mdat
10_ACTUAL_R_M5.mdat

Opcional:
11_ACTUAL_LR_M1.mdat   ← Stereo (ambos monitores)
12_ACTUAL_L_M6.mdat    ← Corona exterior
...
```

---

## 🔢 Matriz de Micrófonos

```
        M3
         │
         │
M5 ── M1(Op) ── M2
         │
         │
        M4

M1 = Centro (posición de oído)
M2 = +D hacia fondo
M3 = -D hacia izquierda  
M4 = +D hacia derecha
M5 = -D hacia frente

D matriz típico = 0.20 m
```

---

## ⚠️ Verificaciones Críticas

### Triángulo Estéreo
```
✅ Δ máx < 0.05 m
✅ Ángulo ∠M ≈ 60° (55-65°)
✅ L–R = L–M = R–M (±5 cm)
```

### Posiciones de Mic
```
✅ Todas "válidas" en tabla
⚠️ Evitar: "Cerca de pared"
⚠️ Evitar: "Cerca de monitor"
⚠️ Evitar: "Fuera del recinto"
```

### Nivel de Medición
```
✅ Peak: -12 dB a -6 dB
⚠️ Si muy bajo: subir nivel de salida REW
⚠️ Si distorsiona: bajar nivel o alejar monitors
```

---

## 💾 Exportar Datos

### Durante el Relevamiento
```
Después de completar geometría:
├─ Click "Exportar"
└─ Guardar relevamiento_v1.json

Después de mediciones:
├─ Click "Exportar"  
└─ Guardar relevamiento_final.json
```

### Al Finalizar
```
Copiar de laptop:
├─ *.mdat (archivos REW)
├─ relevamiento_final.json
├─ Captura plano SVG
└─ Notas de campo
```

---

## 🐛 Problemas Comunes

### Posiciones fuera de sala
```
→ Operador muy cerca de pared
→ Reducir "D matriz" (ej: 0.15 m)
→ Mover Operador más al centro
```

### Triángulo no equilátero
```
→ Ajustar posiciones L/R/Op
→ Verificar mediciones con cinta
→ Objetivo: diferencias < 5 cm
```

### REW no mide
```
→ Verificar interfaz en Preferences
→ Sample rate coincidente (48k)
→ Nivel de entrada adecuado
→ Cables conectados correctamente
```

### Plano SVG vacío
```
→ Completar Ancho y Profundidad
→ Refrescar navegador
→ Valores > 0
```

---

## 🎓 Tips Pro

### Eficiencia
- ✅ Pre-marcar alturas en el pie (M1, M2, M3, M4, M5)
- ✅ Usar láser si hay (más rápido que cinta)
- ✅ Segunda persona para sostener cinta/anotar

### Precisión
- ✅ Medir 2 veces cada dimensión
- ✅ Verificar triángulo con cinta física
- ✅ Repetir barridos con ruido → promediar en REW

### Documentación
- ✅ Foto de cada setup de micrófono
- ✅ Anotar hora de cada medición
- ✅ Condiciones especiales (temperatura, humedad)

---

## 📱 Interfaz Web - Recordatorio

### Paneles en Modo REW

**Panel Izquierdo (Formulario):**
```
├─ Inicio / estado
├─ Geometría + coords         ← MEDIR PRIMERO
├─ Aberturas                  ← Opcional
├─ Elementos                  ← Opcional
├─ Monitoreo + triángulo      ← CONFIGURAR SEGUNDO
├─ Modos teóricos             ← Referencia
├─ Posiciones de mic          ← LEER ANTES DE MEDIR
└─ Protocolo + checklist      ← Marcar progreso
```

**Panel Derecho (Plano):**
```
- Vista 2D de la sala
- Monitores (L/R)
- Operador (Op)
- Matriz M1-M5
- Aberturas
- Eje de simetría
```

---

## 🔄 Flujo Completo (30 min)

```
00:00 - Setup equipos (5 min)
00:05 - Medir geometría (5 min)
00:10 - Configurar monitoreo (5 min)
00:15 - Calibrar REW (5 min)
00:20 - Mediciones M1-M5 (cada una ~2 min = 10 min total)
00:30 - Exportar y respaldar
```

---

## 📞 Ayuda Rápida

### Fórmulas Útiles

**Velocidad del sonido:**
```
c ≈ 343 m/s (20°C)
c ≈ 331 + (0.6 × T°C)
```

**Modos axiales:**
```
f = c / (2 × L)
Ejemplo: 343 / (2 × 3.20) = 53.6 Hz
```

**Distancia triángulo:**
```
nearfield:  0.8 - 1.2 m
midfield:   1.2 - 2.5 m
```

---

## ✅ Antes de Irte

```
☐ 10 archivos .mdat guardados (L/R × M1-M5)
☐ relevamiento_final.json exportado
☐ Captura de plano SVG
☐ Todas las etapas marcadas en Protocolo
☐ Backup en USB/nube
☐ Equipos desconectados y guardados
```

---

**Versión:** 1.0  
**Fecha:** 2026-09-04  
**Tiempo estimado:** 30-45 minutos  

**🎯 Objetivo:** Caracterizar la respuesta acústica de la sala en 5 posiciones espaciadas alrededor del punto de escucha óptimo.
