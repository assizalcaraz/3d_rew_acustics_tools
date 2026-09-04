/**
 * Relevamiento REW — panel de campo + plano SVG paramétrico.
 * Coords UI siempre en sistema REW. Conversión a app 3D vía RewApp.rewToApp.
 */
(function (global) {
  'use strict';

  var FALTA = 'FALTA MEDIR';
  var FALTA_POS = 'Falta relevar posición.';
  var STORAGE_KEY = 'rew_relevamiento_v1';

  var DEFAULT = null; // se carga de relevamiento.json o fallback
  var state = null;
  var mode = 'tratamiento'; // tratamiento | rew
  var els = {};
  var hooks = {
    onMicsChange: null, // function(micsAppCoords) — coords app {M1:{x,y,z},...}
    onModeChange: null,
    getRoomDims: null   // function() => {L,W,H} del 3D
  };

  // ---------- utils ----------
  function num(v) {
    if (v === null || v === undefined || v === '') return null;
    var f = parseFloat(String(v).replace(',', '.'));
    return isFinite(f) ? f : null;
  }
  function fmt(v, d) {
    if (v === null || v === undefined || !isFinite(v)) return FALTA;
    d = d == null ? 2 : d;
    return v.toFixed(d).replace('.', ',');
  }
  function puntoOk(p) {
    return p && num(p.x) != null && num(p.y) != null && num(p.z) != null;
  }
  function distXY(a, b) {
    return Math.hypot(a.x - b.x, a.y - b.y);
  }
  function clone(o) {
    return JSON.parse(JSON.stringify(o));
  }
  function debounce(fn, ms) {
    var t;
    return function () {
      var args = arguments, self = this;
      clearTimeout(t);
      t = setTimeout(function () { fn.apply(self, args); }, ms);
    };
  }

  // ---------- coords ----------
  function rewToApp(x, y, z, ancho, profundidad) {
    return {
      x: profundidad - y,
      y: ancho - x,
      z: z
    };
  }

  // ---------- cálculos (espejo de rew_calculo.py) ----------
  function calcularModos(lx, ly, lz, c, ordenMax, agrHz) {
    if (!(lx > 0 && ly > 0 && lz > 0 && c > 0)) return [];
    ordenMax = ordenMax || 10;
    agrHz = agrHz == null ? 3 : agrHz;
    var modos = [];
    for (var nx = 0; nx <= ordenMax; nx++) {
      for (var ny = 0; ny <= ordenMax; ny++) {
        for (var nz = 0; nz <= ordenMax; nz++) {
          if (!nx && !ny && !nz) continue;
          var f = (c / 2) * Math.sqrt(
            Math.pow(nx / lx, 2) + Math.pow(ny / ly, 2) + Math.pow(nz / lz, 2)
          );
          var nzc = (nx > 0 ? 1 : 0) + (ny > 0 ? 1 : 0) + (nz > 0 ? 1 : 0);
          var tipo = nzc === 1 ? 'axial' : nzc === 2 ? 'tangencial' : 'oblicuo';
          modos.push({
            nx: nx, ny: ny, nz: nz,
            f_hz: Math.round(f * 100) / 100,
            tipo: tipo,
            etiqueta: nx + ',' + ny + ',' + nz,
            grupo: null
          });
        }
      }
    }
    modos.sort(function (a, b) {
      return a.f_hz - b.f_hz || a.nx - b.nx || a.ny - b.ny || a.nz - b.nz;
    });
    var gid = 0, i = 0;
    while (i < modos.length) {
      var j = i + 1;
      while (j < modos.length && modos[j].f_hz - modos[i].f_hz <= agrHz) j++;
      if (j - i >= 2) {
        gid++;
        for (var k = i; k < j; k++) modos[k].grupo = gid;
        i = j;
      } else {
        i++;
      }
    }
    return modos;
  }

  function calcularTriangulo(L, R, M, margen, distObj) {
    var out = {
      lr: FALTA, lm: FALTA, rm: FALTA,
      delta_max: FALTA, angulo_m_deg: FALTA,
      equilatero: false, aviso: null, completo: false,
      dist_objetivo: distObj
    };
    if (!puntoOk(L) || !puntoOk(R) || !puntoOk(M)) {
      out.aviso = FALTA_POS;
      return out;
    }
    var pL = { x: +L.x, y: +L.y }, pR = { x: +R.x, y: +R.y }, pM = { x: +M.x, y: +M.y };
    var lr = distXY(pL, pR), lm = distXY(pL, pM), rm = distXY(pR, pM);
    var delta = Math.max(Math.abs(lr - lm), Math.abs(lr - rm), Math.abs(lm - rm));
    var ang = FALTA;
    if (lm > 1e-9 && rm > 1e-9) {
      var cosA = (lm * lm + rm * rm - lr * lr) / (2 * lm * rm);
      cosA = Math.max(-1, Math.min(1, cosA));
      ang = Math.round(Math.acos(cosA) * 180 / Math.PI * 10) / 10;
    }
    var equi = Math.abs(lr - lm) <= margen && Math.abs(lr - rm) <= margen && Math.abs(lm - rm) <= margen;
    out.lr = Math.round(lr * 1000) / 1000;
    out.lm = Math.round(lm * 1000) / 1000;
    out.rm = Math.round(rm * 1000) / 1000;
    out.delta_max = Math.round(delta * 1000) / 1000;
    out.angulo_m_deg = ang;
    out.equilatero = equi;
    out.completo = true;
    out.aviso = equi ? 'TRIÁNGULO APROXIMADAMENTE EQUILÁTERO' : null;
    return out;
  }

  function sugerirMonitoreo(ancho, profundidad, altoOido, distObj) {
    if (!(ancho > 0 && profundidad > 0)) return null;
    altoOido = altoOido == null ? 1.2 : altoOido;
    distObj = distObj == null ? 1.0 : distObj;
    var cx = ancho / 2, yMon = 0.35, half = distObj / 2;
    var yOp = yMon + (Math.sqrt(3) / 2) * distObj;
    if (yOp >= profundidad - 0.3) yOp = Math.min(profundidad * 0.55, profundidad - 0.4);
    function r(v) { return Math.round(v * 1000) / 1000; }
    return {
      L: { x: r(cx - half), y: r(yMon), z: r(altoOido) },
      R: { x: r(cx + half), y: r(yMon), z: r(altoOido) },
      operador: { x: r(cx), y: r(yOp), z: r(altoOido) },
      aviso: 'Posición sugerida (simetría / nearfield). Validar con medición — no es verdad acústica.'
    };
  }

  function matrizMics(op, d, d2, dz) {
    var labs = {
      M1: [0, 0, 0], M2: [0, d, 0], M3: [-d, 0, 0], M4: [d, 0, 0], M5: [0, -d, 0],
      M6: [0, d2, 0], M7: [-d2, 0, 0], M8: [d2, 0, 0], M9: [0, -d2, 0],
      V1: [0, 0, 0], V2: [0, 0, dz], V3: [0, 0, -dz]
    };
    var out = {};
    var ok = puntoOk(op);
    Object.keys(labs).forEach(function (lab) {
      var o = labs[lab];
      if (!ok) {
        out[lab] = { x: null, y: null, z: null, estado: FALTA_POS };
      } else {
        out[lab] = {
          x: Math.round((+op.x + o[0]) * 1000) / 1000,
          y: Math.round((+op.y + o[1]) * 1000) / 1000,
          z: Math.round((+op.z + o[2]) * 1000) / 1000,
          estado: 'calculado'
        };
      }
      if (lab.charAt(0) === 'V') out[lab].nota = 'MEDICIÓN EXPLORATORIA — MODOS VERTICALES';
      if (/^M[6-9]$/.test(lab) || lab.charAt(0) === 'V') out[lab].opcional = true;
    });
    return out;
  }

  function aberturaGeom(ab) {
    var w = num(ab.ancho);
    var da = num(ab.dist_esquina_a);
    return w != null && w > 0 && da != null;
  }

  function centroAbertura(ab, ancho, prof) {
    if (!aberturaGeom(ab)) return null;
    var w = +ab.ancho, da = +ab.dist_esquina_a;
    var p = (ab.pared || '').toLowerCase();
    if (p === 'derecha' || p === 'right' || p === 'der')
      return { x: ancho, y: da + w / 2 };
    if (p === 'trasera' || p === 'back' || p === 'fondo')
      return { x: da + w / 2, y: prof };
    if (p === 'izquierda' || p === 'left' || p === 'izq')
      return { x: 0, y: da + w / 2 };
    if (p === 'frontal' || p === 'frente' || p === 'front')
      return { x: da + w / 2, y: 0 };
    return null;
  }

  function validarPos(p, geo, umb, mons, abs) {
    var avisos = [];
    if (!puntoOk(p)) return { valida: false, avisos: [FALTA_POS], dentro_sala: false };
    var x = +p.x, y = +p.y, z = +p.z;
    var A = geo.ancho_m, P = geo.profundidad_m, H = geo.alto_m;
    var dentro = x > 0 && x < A && y > 0 && y < P && z > 0 && z < H;
    if (!dentro) avisos.push('Fuera del recinto (o en el límite).');
    var up = umb.min_pared_m || 0.3;
    if (x < up || A - x < up) avisos.push('Cerca de pared lateral.');
    if (y < up || P - y < up) avisos.push('Cerca de pared frontal/trasera.');
    if (z < up || H - z < up) avisos.push('Cerca de piso/techo.');
    (mons || []).forEach(function (m) {
      if (puntoOk(m) && Math.hypot(x - m.x, y - m.y, z - m.z) < (umb.min_monitor_m || 0.4))
        avisos.push('Cerca de monitor.');
    });
    (abs || []).forEach(function (ab) {
      var c = centroAbertura(ab, A, P);
      if (c && Math.hypot(x - c.x, y - c.y) < (umb.min_abertura_m || 0.4))
        avisos.push('Cerca de abertura ' + (ab.id || ''));
    });
    return { valida: dentro, dentro_sala: dentro, avisos: avisos };
  }

  // ---------- persistencia ----------
  function saveLocal() {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); } catch (e) {}
  }
  var saveLocalDebounced = debounce(saveLocal, 200);

  function loadLocal() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return null;
      return JSON.parse(raw);
    } catch (e) { return null; }
  }

  function exportJson() {
    var blob = new Blob([JSON.stringify(state, null, 2)], { type: 'application/json' });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'relevamiento_rew.json';
    a.click();
    URL.revokeObjectURL(a.href);
  }

  function importJson(file) {
    var reader = new FileReader();
    reader.onload = function () {
      try {
        var data = JSON.parse(reader.result);
        if (!data.geometria || !data.monitoreo) throw new Error('JSON inválido');
        state = data;
        saveLocal();
        renderAll();
        notifyMics();
      } catch (e) {
        alert('No se pudo importar: ' + e.message);
      }
    };
    reader.readAsText(file);
  }

  // ---------- UI shell ----------
  function ensureDom() {
    if (document.getElementById('rew-root')) return;
    var root = document.createElement('div');
    root.id = 'rew-root';
    root.innerHTML =
      '<div id="rew-panel" aria-hidden="true">' +
        '<div class="rew-head">' +
          '<strong>Relevamiento REW</strong>' +
          '<div class="rew-head-actions">' +
            '<button type="button" id="rew-btn-export" title="Exportar JSON">Exportar</button>' +
            '<label class="rew-btn-file"><input type="file" id="rew-btn-import" accept="application/json,.json">Importar</label>' +
            '<button type="button" id="rew-btn-reset" title="Restaurar plantilla">Reset</button>' +
          '</div>' +
        '</div>' +
        '<div id="rew-sections"></div>' +
      '</div>' +
      '<div id="rew-plano-wrap" aria-hidden="true">' +
        '<div class="rew-plano-bar">' +
          '<span>Plano paramétrico (coords REW)</span>' +
          '<span class="rew-muted" id="rew-plano-dims"></span>' +
        '</div>' +
        '<svg id="rew-plano" viewBox="0 0 400 440" xmlns="http://www.w3.org/2000/svg"></svg>' +
        '<div class="rew-leyenda" id="rew-leyenda"></div>' +
      '</div>';
    document.body.appendChild(root);
    els.panel = document.getElementById('rew-panel');
    els.sections = document.getElementById('rew-sections');
    els.plano = document.getElementById('rew-plano');
    els.planoWrap = document.getElementById('rew-plano-wrap');
    els.planoDims = document.getElementById('rew-plano-dims');
    els.leyenda = document.getElementById('rew-leyenda');

    document.getElementById('rew-btn-export').addEventListener('click', exportJson);
    document.getElementById('rew-btn-import').addEventListener('change', function (e) {
      if (e.target.files && e.target.files[0]) importJson(e.target.files[0]);
      e.target.value = '';
    });
    document.getElementById('rew-btn-reset').addEventListener('click', function () {
      if (!confirm('¿Restaurar plantilla vacía? Se pierde el relevamiento local.')) return;
      state = clone(DEFAULT);
      saveLocal();
      renderAll();
      notifyMics();
    });
  }

  function section(title, id, open) {
    var det = document.createElement('details');
    det.className = 'rew-sec';
    det.open = !!open;
    det.id = id;
    var sum = document.createElement('summary');
    sum.textContent = title;
    det.appendChild(sum);
    var body = document.createElement('div');
    body.className = 'rew-sec-body';
    det.appendChild(body);
    return { el: det, body: body };
  }

  function fieldNum(label, value, onChange, opts) {
    opts = opts || {};
    var wrap = document.createElement('label');
    wrap.className = 'rew-field' + (opts.pending && (value === null || value === '') ? ' pending' : '');
    var span = document.createElement('span');
    span.textContent = label;
    if (opts.hint) {
      var h = document.createElement('em');
      h.className = 'rew-hint';
      h.textContent = ' ' + opts.hint;
      span.appendChild(h);
    }
    var inp = document.createElement('input');
    inp.type = 'number';
    inp.step = opts.step || '0.01';
    inp.inputMode = 'decimal';
    if (value !== null && value !== undefined && value !== '') inp.value = value;
    else inp.placeholder = opts.placeholder || '—';
    inp.addEventListener('change', function () {
      var v = inp.value === '' ? null : num(inp.value);
      onChange(v);
    });
    wrap.appendChild(span);
    wrap.appendChild(inp);
    return wrap;
  }

  function fieldText(label, value, onChange) {
    var wrap = document.createElement('label');
    wrap.className = 'rew-field';
    var span = document.createElement('span');
    span.textContent = label;
    var inp = document.createElement('input');
    inp.type = 'text';
    inp.value = value || '';
    inp.addEventListener('change', function () { onChange(inp.value); });
    wrap.appendChild(span);
    wrap.appendChild(inp);
    return wrap;
  }

  function calcBox(html, kind) {
    var d = document.createElement('div');
    d.className = 'rew-calc' + (kind ? ' ' + kind : '');
    d.innerHTML = html;
    return d;
  }

  function badge(txt, kind) {
    return '<span class="rew-badge ' + (kind || '') + '">' + txt + '</span>';
  }

  // ---------- render secciones ----------
  function renderInicio(body) {
    body.innerHTML = '';
    var g = state.geometria;
    var m = state.monitoreo;
    var rows = [
      ['Ancho sala', num(g.ancho_m) != null ? 'Sí' : 'No'],
      ['Profundidad', num(g.profundidad_m) != null ? 'Sí' : 'No'],
      ['Alto (preliminar)', num(g.alto_m) != null ? 'Sí (prelim.)' : 'No'],
      ['A01 medidas', aberturaGeom(state.aberturas[0] || {}) ? 'Sí' : 'No'],
      ['A02 medidas', aberturaGeom(state.aberturas[1] || {}) ? 'Sí' : 'No'],
      ['Monitor L', puntoOk(m.L) ? 'Sí' : 'No'],
      ['Monitor R', puntoOk(m.R) ? 'Sí' : 'No'],
      ['Operador', puntoOk(m.operador) ? 'Sí' : 'No']
    ];
    var table = document.createElement('table');
    table.className = 'rew-table';
    rows.forEach(function (r) {
      var tr = document.createElement('tr');
      tr.innerHTML = '<td>' + r[0] + '</td><td>' +
        badge(r[1], r[1].indexOf('Sí') === 0 ? 'ok' : 'no') + '</td>';
      table.appendChild(tr);
    });
    body.appendChild(table);
    body.appendChild(calcBox(
      'Coords REW: origen frontal izquierda. X→derecha, Y→fondo, Z→techo.<br>' +
      '<span class="rew-muted">Conversión interna al 3D sin rotar el modelo.</span>',
      'info'
    ));
  }

  function renderGeo(body) {
    body.innerHTML = '';
    var g = state.geometria;
    var pre = g.preliminar || {};
    var grid = document.createElement('div');
    grid.className = 'rew-grid';
    grid.appendChild(fieldNum('Ancho X (m)', g.ancho_m, function (v) {
      g.ancho_m = v; if (pre) pre.ancho_m = false; bump();
    }, { hint: pre.ancho_m ? 'preliminar' : '', pending: true }));
    grid.appendChild(fieldNum('Profundidad Y (m)', g.profundidad_m, function (v) {
      g.profundidad_m = v; if (pre) pre.profundidad_m = false; bump();
    }, { hint: pre.profundidad_m ? 'preliminar' : '', pending: true }));
    grid.appendChild(fieldNum('Alto Z (m)', g.alto_m, function (v) {
      g.alto_m = v; if (pre) pre.alto_m = false; bump();
    }, { hint: 'preliminar REW; 3D sigue en 3,00', pending: true }));
    body.appendChild(grid);
    body.appendChild(calcBox(
      (g.nota_alto || '') + '<br>Volumen ≈ ' +
      (num(g.ancho_m) && num(g.profundidad_m) && num(g.alto_m)
        ? fmt(g.ancho_m * g.profundidad_m * g.alto_m, 1) + ' m³'
        : FALTA),
      'calc'
    ));
  }

  function renderAberturas(body) {
    body.innerHTML = '';
    state.aberturas.forEach(function (ab, idx) {
      var box = document.createElement('div');
      box.className = 'rew-card';
      box.innerHTML = '<div class="rew-card-t">' + ab.id + ' · ' + (ab.nombre || '') +
        ' <em>(' + (ab.pared || '') + ')</em></div>';
      var grid = document.createElement('div');
      grid.className = 'rew-grid';
      [['ancho', 'Ancho (m)'], ['alto', 'Alto (m)'],
       ['dist_esquina_a', 'Dist. esquina A (m)'], ['dist_esquina_b', 'Dist. esquina B (m)']
      ].forEach(function (pair) {
        grid.appendChild(fieldNum(pair[1], ab[pair[0]], function (v) {
          ab[pair[0]] = v; bump();
        }, { pending: true, placeholder: 'vacío' }));
      });
      box.appendChild(grid);
      if (!aberturaGeom(ab)) {
        box.appendChild(calcBox('Geometría: ' + FALTA + ' — no se dibuja hasta medir.', 'warn'));
      } else {
        var c = centroAbertura(ab, state.geometria.ancho_m, state.geometria.profundidad_m);
        box.appendChild(calcBox(
          'Centro aprox. REW: X ' + fmt(c.x) + ' · Y ' + fmt(c.y),
          'calc'
        ));
      }
      body.appendChild(box);
    });
  }

  function renderElementos(body) {
    body.innerHTML = '';
    body.appendChild(calcBox(
      'Filas vacías a propósito. El layout 3D de referencia no se copia como “medido”.',
      'info'
    ));
    state.elementos.forEach(function (el) {
      var box = document.createElement('div');
      box.className = 'rew-card';
      box.innerHTML = '<div class="rew-card-t">' + el.id + ' · ' + el.nombre + '</div>';
      var grid = document.createElement('div');
      grid.className = 'rew-grid';
      ['x', 'y', 'z', 'ancho', 'profundidad', 'alto'].forEach(function (k) {
        grid.appendChild(fieldNum(k.toUpperCase() + ' (m)', el[k], function (v) {
          el[k] = v; bump();
        }, { pending: true, placeholder: 'vacío' }));
      });
      box.appendChild(grid);
      body.appendChild(box);
    });
  }

  function renderMonitoreo(body) {
    body.innerHTML = '';
    var m = state.monitoreo;
    var umb = state.umbrales;
    ['L', 'R', 'operador'].forEach(function (key) {
      var p = m[key];
      var box = document.createElement('div');
      box.className = 'rew-card';
      box.innerHTML = '<div class="rew-card-t">' +
        (key === 'operador' ? 'Operador (oído / M1)' : 'Monitor ' + key) + '</div>';
      var grid = document.createElement('div');
      grid.className = 'rew-grid';
      ['x', 'y', 'z'].forEach(function (k) {
        grid.appendChild(fieldNum(k.toUpperCase() + ' REW (m)', p[k], function (v) {
          p[k] = v; bump(); notifyMics();
        }, { pending: true, placeholder: 'vacío' }));
      });
      box.appendChild(grid);
      body.appendChild(box);
    });

    var actions = document.createElement('div');
    actions.className = 'rew-actions';
    var btnSug = document.createElement('button');
    btnSug.type = 'button';
    btnSug.textContent = 'Aplicar sugerencia simétrica';
    btnSug.addEventListener('click', function () {
      var s = sugerirMonitoreo(
        state.geometria.ancho_m, state.geometria.profundidad_m,
        1.2, umb.dist_objetivo_triangulo_m || 1.0
      );
      if (!s) return;
      m.L = s.L; m.R = s.R; m.operador = s.operador;
      bump(); notifyMics();
      alert(s.aviso);
    });
    actions.appendChild(btnSug);
    body.appendChild(actions);

    var distObjField = fieldNum(
      'Distancia objetivo triángulo (m)',
      umb.dist_objetivo_triangulo_m,
      function (v) { umb.dist_objetivo_triangulo_m = v || 1.0; bump(); },
      { step: '0.05' }
    );
    body.appendChild(distObjField);

    var tri = calcularTriangulo(
      m.L, m.R, m.operador,
      umb.margen_equilatero_m || 0.05,
      umb.dist_objetivo_triangulo_m || 1.0
    );
    var html =
      '<b>Triángulo</b><br>' +
      'L–R: ' + (typeof tri.lr === 'number' ? fmt(tri.lr, 3) + ' m' : FALTA) +
      ' · L–M: ' + (typeof tri.lm === 'number' ? fmt(tri.lm, 3) + ' m' : FALTA) +
      ' · R–M: ' + (typeof tri.rm === 'number' ? fmt(tri.rm, 3) + ' m' : FALTA) + '<br>' +
      'Δ máx: ' + (typeof tri.delta_max === 'number' ? fmt(tri.delta_max, 3) + ' m' : FALTA) +
      ' · ∠M: ' + (typeof tri.angulo_m_deg === 'number' ? fmt(tri.angulo_m_deg, 1) + '°' : FALTA);
    if (tri.completo && tri.aviso) html += '<br><strong class="rew-ok">' + tri.aviso + '</strong>';
    if (!tri.completo) html += '<br><span class="rew-warn">' + (tri.aviso || FALTA_POS) + '</span>';
    body.appendChild(calcBox(html, tri.equilatero ? 'ok' : (tri.completo ? 'calc' : 'warn')));
  }

  function renderModos(body) {
    body.innerHTML = '';
    var g = state.geometria, u = state.umbrales;
    var c = num(u.c_sonido_ms) || 343;
    body.appendChild(fieldNum('c (m/s)', c, function (v) {
      u.c_sonido_ms = v || 343; bump();
    }));
    body.appendChild(calcBox(
      'Los modos teóricos no sustituyen una medición REW. f = c/2 √[(nx/Lx)²+…]',
      'info'
    ));
    // En REW: Lx=ancho, Ly=profundidad, Lz=alto
    var modos = calcularModos(
      g.ancho_m, g.profundidad_m, g.alto_m,
      c, u.modos_orden_max || 10, u.modos_agrupamiento_hz || 3
    );
    if (!modos.length) {
      body.appendChild(calcBox(FALTA + ' — faltan dimensiones.', 'warn'));
      return;
    }
    var table = document.createElement('table');
    table.className = 'rew-table compact';
    table.innerHTML = '<tr><th>Hz</th><th>n</th><th>Tipo</th><th>Grp</th></tr>';
    modos.slice(0, 40).forEach(function (m) {
      var tr = document.createElement('tr');
      tr.innerHTML = '<td>' + fmt(m.f_hz, 1) + '</td><td>' + m.etiqueta +
        '</td><td>' + m.tipo + '</td><td>' + (m.grupo || '—') + '</td>';
      table.appendChild(tr);
    });
    body.appendChild(table);
    if (modos.length > 40) {
      body.appendChild(calcBox('Mostrando 40 de ' + modos.length + ' modos.', 'info'));
    }
  }

  function renderMics(body) {
    body.innerHTML = '';
    var u = state.umbrales;
    var grid = document.createElement('div');
    grid.className = 'rew-grid';
    grid.appendChild(fieldNum('D matriz (m)', u.d_matriz_m, function (v) {
      u.d_matriz_m = v || 0.2; bump(); notifyMics();
    }, { step: '0.05' }));
    grid.appendChild(fieldNum('D corona (m)', u.d_corona_m, function (v) {
      u.d_corona_m = v || 0.4; bump(); notifyMics();
    }, { step: '0.05' }));
    body.appendChild(grid);

    var mics = matrizMics(
      state.monitoreo.operador,
      u.d_matriz_m || 0.2,
      u.d_corona_m || 0.4,
      u.dz_vertical_m || 0.2
    );
    var table = document.createElement('table');
    table.className = 'rew-table compact';
    table.innerHTML = '<tr><th>ID</th><th>X</th><th>Y</th><th>Z</th><th>Estado</th></tr>';
    ['M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7', 'M8', 'M9', 'V1', 'V2', 'V3'].forEach(function (id) {
      var p = mics[id];
      var tr = document.createElement('tr');
      var val = validarPos(p, state.geometria, u, [state.monitoreo.L, state.monitoreo.R], state.aberturas);
      var est = p.estado === 'calculado'
        ? (val.avisos.length ? '⚠ ' + val.avisos[0] : 'válida')
        : p.estado;
      tr.innerHTML = '<td>' + id + (p.opcional ? '*' : '') + '</td><td>' +
        fmt(p.x) + '</td><td>' + fmt(p.y) + '</td><td>' + fmt(p.z) +
        '</td><td class="' + (p.x == null ? 'rew-warn' : '') + '">' + est + '</td>';
      table.appendChild(tr);
    });
    body.appendChild(table);
    body.appendChild(calcBox(
      'M1–M5 se recalculan al mover el operador. * = opcional. V* = modos verticales exploratorios.',
      'info'
    ));
  }

  function renderProtocolo(body) {
    body.innerHTML = '';
    var proto = state.protocolo;
    var etapas = document.createElement('div');
    etapas.className = 'rew-checklist';
    (proto.etapas || []).forEach(function (et) {
      var lab = document.createElement('label');
      lab.className = 'rew-check';
      var cb = document.createElement('input');
      cb.type = 'checkbox';
      cb.checked = !!et.hecho;
      cb.addEventListener('change', function () { et.hecho = cb.checked; saveLocalDebounced(); });
      lab.appendChild(cb);
      lab.appendChild(document.createTextNode(' ' + et.id + '. ' + et.nombre));
      etapas.appendChild(lab);
    });
    body.appendChild(etapas);

    body.appendChild(document.createElement('hr'));
    var cfgTitle = document.createElement('div');
    cfgTitle.className = 'rew-card-t';
    cfgTitle.textContent = 'Config REW (editable, sin asumir interfaz)';
    body.appendChild(cfgTitle);
    var cfg = proto.config_rew || {};
    var grid = document.createElement('div');
    grid.className = 'rew-grid';
    ['mic', 'calibracion', 'sample_rate', 'sweep', 'nivel'].forEach(function (k) {
      grid.appendChild(fieldText(k, cfg[k], function (v) {
        cfg[k] = v; proto.config_rew = cfg; saveLocalDebounced();
      }));
    });
    body.appendChild(grid);

    body.appendChild(fieldText('Nomenclatura archivos', proto.nomenclatura, function (v) {
      proto.nomenclatura = v; saveLocalDebounced();
    }));
    body.appendChild(calcBox(
      'Ejemplo: <code>01_ACTUAL_L_M1</code>, <code>02_ACTUAL_R_M1</code>, …',
      'info'
    ));

    var campoTitle = document.createElement('div');
    campoTitle.className = 'rew-card-t';
    campoTitle.textContent = 'Checklist de campo';
    body.appendChild(campoTitle);
    var campo = document.createElement('div');
    campo.className = 'rew-checklist';
    (proto.checklist_campo || []).forEach(function (it) {
      var lab = document.createElement('label');
      lab.className = 'rew-check';
      var cb = document.createElement('input');
      cb.type = 'checkbox';
      cb.checked = !!it.ok;
      cb.addEventListener('change', function () { it.ok = cb.checked; saveLocalDebounced(); });
      lab.appendChild(cb);
      lab.appendChild(document.createTextNode(' ' + it.item));
      campo.appendChild(lab);
    });
    body.appendChild(campo);
  }

  function renderAll() {
    ensureDom();
    els.sections.innerHTML = '';
    var secs = [
      ['Inicio / estado', 'rew-s-inicio', true, renderInicio],
      ['Geometría + coords', 'rew-s-geo', true, renderGeo],
      ['Aberturas', 'rew-s-ab', false, renderAberturas],
      ['Elementos', 'rew-s-el', false, renderElementos],
      ['Monitoreo + triángulo', 'rew-s-mon', true, renderMonitoreo],
      ['Modos teóricos', 'rew-s-mod', false, renderModos],
      ['Posiciones de mic', 'rew-s-mic', true, renderMics],
      ['Protocolo + checklist', 'rew-s-pro', false, renderProtocolo]
    ];
    secs.forEach(function (s) {
      var sec = section(s[0], s[1], s[2]);
      s[3](sec.body);
      els.sections.appendChild(sec.el);
    });
    drawPlano();
  }

  function bump() {
    saveLocalDebounced();
    renderAll();
  }

  // ---------- plano SVG ----------
  function drawPlano() {
    var svg = els.plano;
    if (!svg) return;
    var g = state.geometria;
    var A = num(g.ancho_m) || 3.0;
    var P = num(g.profundidad_m) || 3.2;
    els.planoDims.textContent = fmt(A) + ' × ' + fmt(P) + ' m (alto REW ' + fmt(g.alto_m) + ')';

    var pad = 48, cota = 28;
    var maxW = 360, maxH = 340;
    var scale = Math.min(maxW / A, maxH / P);
    var rw = A * scale, rh = P * scale;
    var ox = pad, oy = pad;
    var vbW = ox + rw + pad + 20;
    var vbH = oy + rh + pad + cota + 40;
    svg.setAttribute('viewBox', '0 0 ' + vbW + ' ' + vbH);
    svg.innerHTML = '';

    function sx(x) { return ox + x * scale; }
    function sy(y) { return oy + y * scale; } // Y REW hacia abajo en SVG (frente arriba)

    function el(name, attrs, text) {
      var n = document.createElementNS('http://www.w3.org/2000/svg', name);
      Object.keys(attrs).forEach(function (k) { n.setAttribute(k, attrs[k]); });
      if (text != null) n.textContent = text;
      svg.appendChild(n);
      return n;
    }

    // fondo sala
    el('rect', {
      x: ox, y: oy, width: rw, height: rh,
      fill: '#f7f8fb', stroke: '#1f2a44', 'stroke-width': 2
    });

    // eje simetría frontal
    el('line', {
      x1: sx(A / 2), y1: oy - 6, x2: sx(A / 2), y2: oy + rh,
      stroke: '#9fb0d8', 'stroke-width': 1, 'stroke-dasharray': '4 3'
    });
    el('text', {
      x: sx(A / 2), y: oy - 10, 'text-anchor': 'middle',
      fill: '#8891a3', 'font-size': 9
    }, 'eje simetría');

    // cotas
    el('line', { x1: ox, y1: oy + rh + 14, x2: ox + rw, y2: oy + rh + 14, stroke: '#1f2a44', 'stroke-width': 1 });
    el('text', {
      x: ox + rw / 2, y: oy + rh + 26, 'text-anchor': 'middle',
      fill: '#1f2a44', 'font-size': 11, 'font-weight': 600
    }, 'ancho ' + fmt(A) + ' m');
    el('line', { x1: ox - 14, y1: oy, x2: ox - 14, y2: oy + rh, stroke: '#1f2a44', 'stroke-width': 1 });
    el('text', {
      x: ox - 18, y: oy + rh / 2, 'text-anchor': 'middle',
      fill: '#1f2a44', 'font-size': 11, 'font-weight': 600,
      transform: 'rotate(-90 ' + (ox - 18) + ' ' + (oy + rh / 2) + ')'
    }, 'prof. ' + fmt(P) + ' m');

    // etiquetas paredes
    el('text', { x: ox + rw / 2, y: oy + 12, 'text-anchor': 'middle', fill: '#8891a3', 'font-size': 10 }, 'FRENTE');
    el('text', { x: ox + rw / 2, y: oy + rh - 6, 'text-anchor': 'middle', fill: '#8891a3', 'font-size': 10 }, 'FONDO');
    el('text', { x: ox + 4, y: oy + rh / 2, fill: '#8891a3', 'font-size': 10 }, 'IZQ');
    el('text', { x: ox + rw - 4, y: oy + rh / 2, 'text-anchor': 'end', fill: '#8891a3', 'font-size': 10 }, 'DER');

    // aberturas solo con dato
    (state.aberturas || []).forEach(function (ab) {
      if (!aberturaGeom(ab)) return;
      var w = +ab.ancho, da = +ab.dist_esquina_a;
      var p = (ab.pared || '').toLowerCase();
      var x1, y1, x2, y2;
      if (p === 'derecha' || p === 'der') {
        x1 = A; y1 = da; x2 = A; y2 = da + w;
      } else if (p === 'trasera' || p === 'fondo') {
        x1 = da; y1 = P; x2 = da + w; y2 = P;
      } else if (p === 'izquierda' || p === 'izq') {
        x1 = 0; y1 = da; x2 = 0; y2 = da + w;
      } else {
        x1 = da; y1 = 0; x2 = da + w; y2 = 0;
      }
      el('line', {
        x1: sx(x1), y1: sy(y1), x2: sx(x2), y2: sy(y2),
        stroke: '#b58b52', 'stroke-width': 6, 'stroke-linecap': 'butt'
      });
      var cx = (x1 + x2) / 2, cy = (y1 + y2) / 2;
      el('text', {
        x: sx(cx) + (p.indexOf('der') >= 0 || p === 'derecha' ? 10 : p.indexOf('izq') >= 0 ? -10 : 0),
        y: sy(cy) + (p.indexOf('tras') >= 0 || p === 'fondo' ? 12 : p.indexOf('frent') >= 0 ? -8 : 0),
        'text-anchor': 'middle', fill: '#8a6230', 'font-size': 10, 'font-weight': 700
      }, ab.id);
    });

    // escritorio si tiene medidas
    (state.elementos || []).forEach(function (elmt) {
      if (num(elmt.x) == null || num(elmt.y) == null || num(elmt.ancho) == null || num(elmt.profundidad) == null)
        return;
      el('rect', {
        x: sx(elmt.x - elmt.ancho / 2), y: sy(elmt.y - elmt.profundidad / 2),
        width: elmt.ancho * scale, height: elmt.profundidad * scale,
        fill: 'rgba(183,183,183,.45)', stroke: '#888', 'stroke-width': 1
      });
    });

    // monitores / operador
    function mark(p, label, color, r) {
      if (!puntoOk(p) && !(p && num(p.x) != null && num(p.y) != null)) return;
      var x = +p.x, y = +p.y;
      el('circle', { cx: sx(x), cy: sy(y), r: r || 5, fill: color, stroke: '#fff', 'stroke-width': 1.5 });
      el('text', {
        x: sx(x) + 8, y: sy(y) + 3, fill: color, 'font-size': 10, 'font-weight': 700
      }, label);
    }
    mark(state.monitoreo.L, 'L', '#cc3333', 6);
    mark(state.monitoreo.R, 'R', '#cc3333', 6);
    mark(state.monitoreo.operador, 'Op', '#3355cc', 6);

    // triángulo
    var L = state.monitoreo.L, R = state.monitoreo.R, Op = state.monitoreo.operador;
    if (puntoOk(L) && puntoOk(R) && puntoOk(Op)) {
      el('polygon', {
        points: [sx(L.x), sy(L.y), sx(R.x), sy(R.y), sx(Op.x), sy(Op.y)].join(' '),
        fill: 'rgba(51,85,204,.08)', stroke: '#3355cc', 'stroke-width': 1, 'stroke-dasharray': '3 2'
      });
    }

    // mics M1–M5
    var u = state.umbrales;
    var mics = matrizMics(Op, u.d_matriz_m || 0.2, u.d_corona_m || 0.4, u.dz_vertical_m || 0.2);
    ['M1', 'M2', 'M3', 'M4', 'M5'].forEach(function (id) {
      var p = mics[id];
      if (p.x == null) return;
      el('circle', {
        cx: sx(p.x), cy: sy(p.y), r: id === 'M1' ? 4.5 : 3.5,
        fill: id === 'M1' ? '#1f2a44' : '#16a2a2',
        stroke: '#fff', 'stroke-width': 1
      });
      el('text', {
        x: sx(p.x) - 10, y: sy(p.y) - 7,
        fill: '#0f7878', 'font-size': 9, 'font-weight': 700
      }, id);
    });

    // origen
    el('circle', { cx: sx(0), cy: sy(0), r: 3, fill: '#f08c0a' });
    el('text', { x: sx(0) + 6, y: sy(0) + 12, fill: '#f08c0a', 'font-size': 9 }, 'origen REW');

    els.leyenda.innerHTML =
      '<span class="rew-leg"><i style="background:#cc3333"></i>L/R medido</span>' +
      '<span class="rew-leg"><i style="background:#3355cc"></i>Operador</span>' +
      '<span class="rew-leg"><i style="background:#16a2a2"></i>Mics calc.</span>' +
      '<span class="rew-leg"><i style="background:#b58b52"></i>Abertura (solo si hay dato)</span>' +
      '<span class="rew-leg muted">pendiente = celda vacía · no se inventa geometría</span>';
  }

  // ---------- 3D hook ----------
  function notifyMics() {
    if (!hooks.onMicsChange) return;
    var g = state.geometria;
    var A = num(g.ancho_m), P = num(g.profundidad_m);
    var room = hooks.getRoomDims ? hooks.getRoomDims() : null;
    // Para marcadores 3D usamos dims del modelo 3D (L,W) si hay, mapeando REW→app
    var ancho = room ? room.W : A;
    var prof = room ? room.L : P;
    if (ancho == null || prof == null) return;
    var u = state.umbrales;
    var mics = matrizMics(
      state.monitoreo.operador,
      u.d_matriz_m || 0.2,
      u.d_corona_m || 0.4,
      u.dz_vertical_m || 0.2
    );
    var app = {};
    ['M1', 'M2', 'M3', 'M4', 'M5'].forEach(function (id) {
      var p = mics[id];
      if (p.x == null) { app[id] = null; return; }
      // Escalar posiciones REW del relevamiento al recinto 3D si dims difieren
      var rx = A ? (+p.x / A) * ancho : +p.x;
      var ry = P ? (+p.y / P) * prof : +p.y;
      var rz = +p.z;
      // Alto 3D es 3.00; si Z REW > H3d, clamp visual suave al oído típico
      if (room && room.H && rz > room.H - 0.05) rz = Math.min(rz, room.H - 0.05);
      app[id] = rewToApp(rx, ry, rz, ancho, prof);
    });
    hooks.onMicsChange(app);
  }

  // ---------- modo ----------
  function setMode(m) {
    mode = m === 'rew' ? 'rew' : 'tratamiento';
    ensureDom();
    var rew = mode === 'rew';
    document.documentElement.classList.toggle('rew-mode', rew);
    els.panel.setAttribute('aria-hidden', rew ? 'false' : 'true');
    els.planoWrap.setAttribute('aria-hidden', rew ? 'false' : 'true');
    document.querySelectorAll('[data-mode]').forEach(function (b) {
      b.classList.toggle('on', b.getAttribute('data-mode') === mode);
    });
    if (rew) {
      renderAll();
      notifyMics();
    }
    if (hooks.onModeChange) hooks.onModeChange(mode);
  }

  function getMode() { return mode; }

  function getMicsApp() {
    notifyMics();
  }

  // ---------- init ----------
  function mergeLoaded(base, saved) {
    if (!saved) return clone(base);
    // Preferir guardado local; rellenar claves nuevas de plantilla
    var out = clone(saved);
    Object.keys(base).forEach(function (k) {
      if (out[k] === undefined) out[k] = clone(base[k]);
    });
    return out;
  }

  function init(opts) {
    opts = opts || {};
    if (opts.onMicsChange) hooks.onMicsChange = opts.onMicsChange;
    if (opts.onModeChange) hooks.onModeChange = opts.onModeChange;
    if (opts.getRoomDims) hooks.getRoomDims = opts.getRoomDims;

    ensureDom();

    function finish(tpl) {
      DEFAULT = tpl;
      state = mergeLoaded(DEFAULT, loadLocal());
      // Botones de modo (inyectados por render_html o creados aquí)
      document.querySelectorAll('[data-mode]').forEach(function (b) {
        b.addEventListener('click', function () { setMode(b.getAttribute('data-mode')); });
      });
      setMode('tratamiento');
      notifyMics();
    }

    if (opts.template) {
      finish(opts.template);
      return;
    }
    fetch('relevamiento.json')
      .then(function (r) { return r.ok ? r.json() : Promise.reject(); })
      .then(finish)
      .catch(function () {
        finish({
          version: 1,
          geometria: { ancho_m: 3.0, profundidad_m: 3.2, alto_m: 4.0, preliminar: { ancho_m: true, profundidad_m: true, alto_m: true }, nota_alto: 'Alto preliminar 4,00 m.' },
          umbrales: { d_matriz_m: 0.2, d_corona_m: 0.4, dz_vertical_m: 0.2, dist_objetivo_triangulo_m: 1.0, margen_equilatero_m: 0.05, min_pared_m: 0.3, min_monitor_m: 0.4, min_abertura_m: 0.4, c_sonido_ms: 343, modos_orden_max: 10, modos_agrupamiento_hz: 3 },
          aberturas: [
            { id: 'A01', nombre: 'Puerta lateral doble', pared: 'derecha', ancho: null, alto: null, dist_esquina_a: null, dist_esquina_b: null },
            { id: 'A02', nombre: 'Puerta trasera simple', pared: 'trasera', ancho: null, alto: null, dist_esquina_a: null, dist_esquina_b: null }
          ],
          elementos: [
            { id: 'E01', nombre: 'Escritorio', x: null, y: null, z: null, ancho: null, profundidad: null, alto: null },
            { id: 'E02', nombre: 'Silla', x: null, y: null, z: null, ancho: null, profundidad: null, alto: null },
            { id: 'E03', nombre: 'Rack', x: null, y: null, z: null, ancho: null, profundidad: null, alto: null }
          ],
          monitoreo: { L: { x: null, y: null, z: null }, R: { x: null, y: null, z: null }, operador: { x: null, y: null, z: null } },
          protocolo: {
            etapas: [
              { id: 0, nombre: 'Preparación', hecho: false },
              { id: 1, nombre: 'Geometría', hecho: false },
              { id: 2, nombre: 'Monitoreo', hecho: false },
              { id: 3, nombre: 'Calibración REW', hecho: false },
              { id: 4, nombre: 'Barridos M1–M5', hecho: false },
              { id: 5, nombre: 'Comparativa', hecho: false },
              { id: 6, nombre: 'Cierre', hecho: false }
            ],
            config_rew: { mic: '', calibracion: '', sample_rate: '', sweep: '', nivel: '' },
            nomenclatura: '01_ACTUAL_L_M1',
            checklist_campo: [
              { item: 'Cinta / láser', ok: false },
              { item: 'Mic + pie', ok: false },
              { item: 'Interfaz', ok: false },
              { item: 'Laptop REW', ok: false }
            ]
          }
        });
      });
  }

  global.RewApp = {
    init: init,
    setMode: setMode,
    getMode: getMode,
    rewToApp: rewToApp,
    getState: function () { return state; },
    refreshMics: notifyMics,
    FALTA: FALTA
  };
})(window);
