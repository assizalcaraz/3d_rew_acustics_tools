# Instrucciones de Uso - Relevamiento y Mediciones REW

## Descripción General

Esta aplicación web combina dos funciones principales:

1. **Visualizador 3D de Tratamiento Acústico**: Modelo interactivo a escala 1:1 de la sala con paneles, clouds y trampas acústicas
2. **Panel de Relevamiento REW**: Sistema de campo para realizar mediciones acústicas con Room EQ Wizard

---

## Requisitos Previos

### Hardware Necesario
- Laptop con REW instalado
- Micrófono de medición calibrado + pie
- Interfaz de audio
- Cinta métrica o medidor láser
- Cables y conexiones

### Software
- Navegador web moderno (Chrome, Firefox, Edge)
- Room EQ Wizard (REW) instalado

---

## Acceso a la Aplicación

### Opción 1: Abrir Directamente
```bash
# Desde el directorio del proyecto, abrir en navegador:
file:///workspace/render.html
```

### Opción 2: Servidor Local
```bash
# Con Python 3:
python3 -m http.server 8000

# Luego abrir en navegador:
http://localhost:8000/render.html
```

---

## Interfaz de la Aplicación

### Botones Superiores Derechos

**Modos de Operación:**
- **Tratamiento** (🎨 modo 3D): Visualizar el diseño de tratamiento acústico
- **Relevamiento REW** (📐 modo medición): Panel de campo para mediciones

**Vistas 3D:**
- `FRENTE`: Pared de los monitores
- `ATRÁS`: Pared trasera
- `IZQ` / `DER`: Paredes laterales
- `PLANTA`: Vista desde arriba
- `3/4`: Vista isométrica
- `+` / `-`: Zoom

---

## PARTE 1: Relevamiento Inicial de Geometría

### Paso 1.1: Activar Modo REW
1. Click en botón **"Relevamiento REW"** (esquina superior derecha)
2. Se abrirán dos paneles:
   - **Panel izquierdo**: Formulario de relevamiento
   - **Panel derecho**: Plano paramétrico 2D
   - El visor 3D quedará de fondo atenuado

### Paso 1.2: Completar Geometría de la Sala

**📍 Sección: "Geometría + coords"** (expandir si está cerrada)

Medir y completar:
```
Ancho X (m):        [___] → Medir de pared izquierda a derecha
Profundidad Y (m):  [___] → Medir de frente a fondo
Alto Z (m):         [___] → Medir del piso al techo (preliminar)
```

**Sistema de Coordenadas REW:**
- Origen: esquina frontal izquierda del piso
- X → hacia la derecha
- Y → hacia el fondo
- Z → hacia el techo

✅ **Verificación:** El plano SVG de la derecha se actualiza automáticamente con las dimensiones.

### Paso 1.3: Registrar Aberturas

**📍 Sección: "Aberturas"**

Para cada abertura (puertas, ventanas):

**Abertura A01:**
```
Pared:               [derecha/izquierda/frontal/trasera]
Ancho (m):           [___]
Alto (m):            [___]
Dist. esquina A (m): [___] → Distancia desde la esquina más cercana
Dist. esquina B (m): [___] → Distancia desde la otra esquina (verificación)
```

**Abertura A02:**
```
(Repetir proceso para segunda abertura)
```

---

## PARTE 2: Posicionamiento de Monitoreo

### Paso 2.1: Configurar Monitores y Posición de Escucha

**📍 Sección: "Monitoreo + triángulo"**

#### Opción A: Usar Sugerencia Automática (Recomendado para inicio)
1. Establecer distancia objetivo del triángulo estéreo:
   ```
   Distancia objetivo triángulo (m): [1.00] → Típicamente 1.0 m para nearfield
   ```
2. Click en botón **"Aplicar sugerencia simétrica"**
3. El sistema calculará posiciones ideales basadas en:
   - Triángulo equilátero
   - Simetría respecto al eje central
   - Altura de oído estándar (1.20 m)

#### Opción B: Medir Manualmente
Medir las posiciones reales de monitores y punto de escucha:

**Monitor L (Izquierdo):**
```
X REW (m): [___] → Distancia desde pared izquierda
Y REW (m): [___] → Distancia desde pared frontal
Z REW (m): [___] → Altura del tweeter
```

**Monitor R (Derecho):**
```
X REW (m): [___]
Y REW (m): [___]
Z REW (m): [___]
```

**Operador (Posición de oído / punto M1):**
```
X REW (m): [___] → Idealmente en el centro
Y REW (m): [___] → Distancia desde pared frontal
Z REW (m): [___] → Altura de oído sentado (~1.20 m)
```

### Paso 2.2: Verificar Triángulo Estéreo

La aplicación calcula automáticamente:

```
Triángulo
L–R:     [___] m   → Distancia entre monitores
L–M:     [___] m   → Monitor izquierdo a operador
R–M:     [___] m   → Monitor derecho a operador
Δ máx:   [___] m   → Diferencia máxima (objetivo: < 0.05 m)
∠M:      [___]°    → Ángulo en posición de escucha (objetivo: ~60°)
```

✅ **Estado óptimo:** Aparece mensaje verde **"TRIÁNGULO APROXIMADAMENTE EQUILÁTERO"**

⚠️ **Si no está equilátero:** Ajustar posiciones hasta conseguir Δ máx < 0.05 m

---

## PARTE 3: Matriz de Posiciones de Micrófono

### Paso 3.1: Configurar Parámetros de Matriz

**📍 Sección: "Posiciones de mic"**

```
D matriz (m):  [0.20] → Distancia entre micrófonos adyacentes (M1-M2, M1-M3, etc.)
D corona (m):  [0.40] → Distancia para micrófonos de corona (M6-M9, opcional)
```

### Paso 3.2: Interpretar Tabla de Posiciones

La aplicación genera automáticamente **12 posiciones de micrófono** basadas en la posición del operador:

| ID  | X      | Y      | Z      | Estado  | Notas |
|-----|--------|--------|--------|---------|-------|
| M1  | [auto] | [auto] | [auto] | válida  | Centro (posición de oído) |
| M2  | [auto] | [auto] | [auto] | válida  | +D hacia fondo |
| M3  | [auto] | [auto] | [auto] | válida  | -D hacia izquierda |
| M4  | [auto] | [auto] | [auto] | válida  | +D hacia derecha |
| M5  | [auto] | [auto] | [auto] | válida  | -D hacia frente |
| M6* | [auto] | [auto] | [auto] | válida  | Corona (opcional) |
| M7* | [auto] | [auto] | [auto] | válida  | Corona (opcional) |
| M8* | [auto] | [auto] | [auto] | válida  | Corona (opcional) |
| M9* | [auto] | [auto] | [auto] | válida  | Corona (opcional) |
| V1* | [auto] | [auto] | [auto] | válida  | Modo vertical (exploratorio) |
| V2* | [auto] | [auto] | [auto] | válida  | Modo vertical (exploratorio) |
| V3* | [auto] | [auto] | [auto] | válida  | Modo vertical (exploratorio) |

**Leyenda:**
- `*` = Posiciones opcionales
- `V*` = Mediciones exploratorias para modos verticales

⚠️ **Advertencias automáticas:** La aplicación indica si alguna posición está:
- Cerca de pared lateral
- Cerca de pared frontal/trasera
- Cerca de piso/techo
- Cerca de monitor
- Cerca de abertura

### Paso 3.3: Visualización en Plano

El **plano paramétrico** (panel derecho) muestra:
- 🔵 **L/R** (rojo): Monitores medidos
- 🔵 **Op** (azul): Posición del operador
- 🔵 **M1-M5** (verde agua): Matriz de micrófonos calculada
- 🟤 **A01/A02** (marrón): Aberturas (si hay datos)

---

## PARTE 4: Protocolo de Medición REW

### Paso 4.1: Checklist Pre-Medición

**📍 Sección: "Protocolo + checklist"**

**Checklist de campo:**
```
☐ Cinta / láser
☐ Mic + pie
☐ Interfaz
☐ Laptop REW
```

### Paso 4.2: Configuración de REW

**Config REW (editable):**
```
mic:           [___] → Modelo de micrófono
calibracion:   [___] → Archivo .txt de calibración
sample_rate:   [___] → 48000 Hz (recomendado)
sweep:         [___] → Log sweep, 20 Hz - 20 kHz
nivel:         [___] → Nivel de salida (dB)
```

### Paso 4.3: Nomenclatura de Archivos

Usar formato estándar:
```
01_ACTUAL_L_M1  → Estado actual, monitor izquierdo, posición M1
02_ACTUAL_R_M1  → Estado actual, monitor derecho, posición M1
03_ACTUAL_L_M2  → Estado actual, monitor izquierdo, posición M2
...
```

O personalizar en el campo:
```
Nomenclatura archivos: [___________________________]
```

### Paso 4.4: Etapas del Protocolo

Marcar cada etapa al completarse:

```
☐ 0. Preparación      → Setup inicial de equipos
☐ 1. Geometría        → Mediciones completadas
☐ 2. Monitoreo        → Triángulo verificado
☐ 3. Calibración REW  → Micrófono calibrado
☐ 4. Barridos M1–M5   → Mediciones realizadas
☐ 5. Comparativa      → Análisis de resultados
☐ 6. Cierre           → Documentación y respaldo
```

---

## PARTE 5: Secuencia de Medición en Campo

### Paso 5.1: Setup Inicial
1. Conectar interfaz de audio a laptop
2. Conectar micrófono de medición a interfaz
3. Conectar monitores a interfaz (output)
4. Abrir REW y configurar entrada/salida

### Paso 5.2: Calibración
1. Cargar archivo de calibración del micrófono en REW
2. Verificar niveles (aim for -12 dB to -6 dB peak)
3. Realizar barrido de prueba

### Paso 5.3: Mediciones por Posición

**Para cada posición M1 a M5:**

1. **Colocar micrófono:**
   - Usar las coordenadas X, Y, Z de la tabla
   - Verificar altura con cinta métrica
   - Micrófono apuntando hacia el techo (omnidireccional) o hacia monitor (direccional)

2. **Medición Monitor L:**
   ```
   REW → Measure
   Archivo: 01_ACTUAL_L_M1.mdat
   Guardar
   ```

3. **Medición Monitor R:**
   ```
   REW → Measure
   Archivo: 02_ACTUAL_R_M1.mdat
   Guardar
   ```

4. **Medición Stereo (opcional):**
   ```
   REW → Measure (ambos monitores)
   Archivo: 03_ACTUAL_LR_M1.mdat
   Guardar
   ```

5. **Repetir para M2, M3, M4, M5**

### Paso 5.4: Mediciones Opcionales

Si hay tiempo y se desea mayor detalle:
- **M6-M9**: Corona exterior
- **V1-V3**: Modos verticales exploratorios

---

## PARTE 6: Análisis de Modos Teóricos

**📍 Sección: "Modos teóricos"**

La aplicación calcula automáticamente los modos acústicos teóricos:

```
c (m/s): [343] → Velocidad del sonido
```

**Tabla de modos:**
| Hz    | n     | Tipo        | Grp |
|-------|-------|-------------|-----|
| 53.6  | 1,0,0 | axial       | 1   |
| 57.2  | 0,1,0 | axial       | 1   |
| 57.2  | 0,0,1 | axial       | 1   |
| ...   | ...   | ...         | ... |

**Interpretación:**
- **Axial** (1 dimensión): Más problemáticos, mayor energía
- **Tangencial** (2 dimensiones): Energía media
- **Oblicuo** (3 dimensiones): Menor energía
- **Grp**: Modos agrupados (< 3 Hz de diferencia) → zona crítica

⚠️ **Importante:** Los modos teóricos **NO sustituyen** las mediciones REW reales. Son solo referencia inicial.

---

## PARTE 7: Gestión de Datos

### Exportar Relevamiento
```
Click en botón "Exportar" → Descarga relevamiento_rew.json
```

Este archivo contiene:
- Geometría medida
- Posiciones de monitores y operador
- Matriz de micrófonos calculada
- Configuración REW
- Estado del protocolo

### Importar Relevamiento
```
Click en botón "Importar" → Seleccionar archivo .json
```

### Restaurar Plantilla
```
Click en botón "Reset" → Confirmar
```
⚠️ **Advertencia:** Borra todos los datos locales guardados.

### Persistencia Automática
Los datos se guardan automáticamente en `localStorage` del navegador cada vez que se modifica un campo.

---

## PARTE 8: Visualización 3D con Micrófonos

### Modo Híbrido
1. Completar posiciones en modo REW
2. Click en botón **"Tratamiento"** para volver al visor 3D
3. Los **marcadores M1-M5** aparecen como esferas en el modelo 3D:
   - 🔵 **M1** (azul oscuro): Posición central
   - 🔵 **M2-M5** (verde agua): Posiciones cardinales

### Conversión de Coordenadas
La aplicación convierte automáticamente entre:
- **Coordenadas REW** (formularios): Origen frontal-izquierda
- **Coordenadas 3D App** (visualización): Sistema rotado para rendering

---

## PARTE 9: Plano Paramétrico SVG

### Elementos del Plano
- **Rectángulo gris**: Perímetro de la sala
- **Línea punteada azul**: Eje de simetría
- **Cotas negras**: Dimensiones (ancho, profundidad)
- **Etiquetas paredes**: FRENTE, FONDO, IZQ, DER
- **Marcadores L/R**: Monitores (rojo)
- **Marcador Op**: Operador (azul)
- **Triángulo**: Zona de escucha óptima (sombreado azul)
- **Círculos M1-M5**: Posiciones de micrófono (verde agua)
- **Líneas marrones**: Aberturas con datos

### Leyenda
```
🔴 L/R medido       → Monitores
🔵 Operador         → Punto de escucha / M1
🔵 Mics calc.       → Matriz de micrófonos
🟤 Abertura         → Solo si hay datos
```

---

## PARTE 10: Consejos y Mejores Prácticas

### Geometría
- ✅ Medir varias veces para verificar
- ✅ Restar grosor de rodapiés/marcos si es relevante
- ✅ Anotar irregularidades (columnas, desniveles)

### Triángulo Estéreo
- ✅ Objetivo: Δ máx < 5 cm
- ✅ Ángulo ideal: 55-65°
- ✅ Distancia típica nearfield: 0.8-1.2 m
- ⚠️ Evitar posiciones muy cerca de paredes (< 30 cm)

### Mediciones
- ✅ Apagar ventiladores, AC, fuentes de ruido
- ✅ Cerrar puertas y ventanas
- ✅ Nivel de medición consistente (-12 dB peak)
- ✅ Realizar al menos 2 barridos por posición para promediado
- ⚠️ No mover monitores entre mediciones

### Matriz de Micrófonos
- ✅ Comenzar siempre por M1 (referencia)
- ✅ M2-M5 obligatorios para caracterización básica
- ⚠️ M6-M9 opcionales (si hay tiempo)
- ⚠️ V1-V3 solo si se sospecha problemas verticales severos

### Documentación
- ✅ Exportar JSON después de completar geometría
- ✅ Exportar JSON después de completar mediciones
- ✅ Captura de pantalla del plano paramétrico
- ✅ Notas de campo en papel (backup)

---

## PARTE 11: Solución de Problemas

### El plano SVG no se dibuja
- Verificar que `Ancho X` y `Profundidad Y` tienen valores válidos
- Refrescar la página

### Las posiciones de micrófono salen inválidas
- Revisar que la posición del Operador está dentro de la sala
- Alejar Operador de paredes (mínimo 30 cm)
- Reducir `D matriz` si las posiciones quedan fuera

### Los marcadores 3D no aparecen
- Asegurarse de haber completado posición del Operador
- Cambiar a modo "Tratamiento" para ver marcadores
- Verificar que el checkbox "Etiquetas" está activado

### Los datos no se guardan
- Verificar que el navegador permite localStorage
- Probar en modo normal (no incógnito)
- Exportar JSON manualmente como respaldo

### REW no detecta la interfaz
- Verificar conexiones físicas
- En REW: Preferences → Soundcard → Seleccionar interfaz
- Verificar sample rate coincide (48000 Hz recomendado)

---

## PARTE 12: Flujo Completo Resumido

### Fase 1: Preparación (5-10 min)
1. Abrir `render.html` en navegador
2. Activar modo "Relevamiento REW"
3. Medir sala con cinta/láser
4. Completar sección "Geometría"
5. Completar sección "Aberturas"

### Fase 2: Monitoreo (10-15 min)
6. Medir posiciones reales de L, R, Operador
7. Completar sección "Monitoreo"
8. Verificar triángulo equilátero
9. Ajustar si es necesario
10. **Exportar JSON** (checkpoint)

### Fase 3: Setup REW (10 min)
11. Conectar micrófono e interfaz
12. Abrir REW
13. Cargar calibración
14. Configurar entrada/salida
15. Barrido de prueba

### Fase 4: Mediciones (30-45 min)
16. Para cada posición M1-M5:
    - Colocar micrófono según coordenadas
    - Medir Monitor L
    - Medir Monitor R
    - Guardar archivos `.mdat`

### Fase 5: Cierre (5 min)
17. Marcar todas las etapas completadas
18. **Exportar JSON** (versión final)
19. Respaldar archivos `.mdat` de REW
20. Captura de plano paramétrico

---

## PARTE 13: Archivos de Referencia

### Archivos del Proyecto
```
render.html              → Aplicación web principal
rew.js                   → Lógica del relevamiento REW
relevamiento.json        → Plantilla de datos
rew_calculo.py          → Cálculos Python (modos, triángulo)
geometria.py            → Geometría 3D Python
modelo_acustico.glb     → Modelo 3D exportado
PRESUPUESTO.md          → Presupuesto del proyecto
```

### Datos Guardados
```
localStorage             → Navegador (automático)
relevamiento_rew.json    → Exportación manual
*.mdat                   → Archivos de medición REW (externo)
```

---

## Contacto y Soporte

Para dudas o problemas con la aplicación, referirse a:
- Documentación REW oficial: https://www.roomeqwizard.com/
- Manual de usuario de tu micrófono de medición
- README.md del proyecto

---

## Notas Importantes

⚠️ **Esta herramienta es para relevamiento de campo.** El análisis detallado de las mediciones REW se realiza posteriormente en el software REW Desktop.

✅ **Los datos se guardan automáticamente** en el navegador, pero se recomienda exportar JSON periódicamente como respaldo.

🎯 **La precisión de los resultados depende** de la exactitud de las mediciones geométricas y la calibración del micrófono.

---

*Última actualización: 2026-09-04*
*Versión del sistema: 1.0*
