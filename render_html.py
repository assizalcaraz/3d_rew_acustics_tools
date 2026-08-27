import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE, "modelo_acustico.json")) as f:
    boxes = json.load(f)

COLOR = {"panel": 0x16a2a2, "ceil": 0x3f9b5a, "trap": 0xf08c0a, "wall": 0xd0d0d0,
         "window": 0x74b6d4, "door": 0xb58b52, "desk": 0xb7b7b7, "monitor": 0x8f8f8f,
         "chair": 0xcfcfcf}
LABEL = {"panel": "Panel 50 mm · 1,20 x 0,60 m",
         "ceil": "Panel de techo colgado · 1,20 x 0,60 m (a 0,42 m del cielorraso)",
         "trap": "Trampa de esquina 100 mm · 1,20 x 0,60 m",
         "window": "Ventana (asumida) · 1,20 x 1,20 · antepecho 0,90 m",
         "door": "Puerta (asumida) · 0,80 x 2,00 m",
         "desk": "Escritorio (referencia)",
         "monitor": "Monitor (referencia)",
         "chair": "Silla (referencia)",
         "wall": "Muro"}

for b in boxes:
    b["color"] = COLOR.get(b["type"], 0x999999)
    b["opacity"] = 0.12 if b["type"] == "wall" else 1.0
    b["label"] = LABEL.get(b["type"], b["type"])

DATA = json.dumps(boxes).replace("<", "\\u003c")

HTML_DOC = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Modelo acústico - Opción B</title>
<style>
  html,body{margin:0;height:100%;font-family:system-ui,sans-serif;background:#f4f5f7}
  #app{position:relative;height:100%}
  canvas{display:block}
  #info{position:absolute;top:12px;left:12px;background:rgba(255,255,255,.95);
        border:1px solid #dfe2e8;border-radius:10px;padding:12px 16px;font-size:13px;
        box-shadow:0 2px 8px rgba(0,0,0,.08);max-width:300px;z-index:5}
  #info h1{font-size:15px;margin:0 0 6px;color:#1f2a44}
  #info p{margin:2px 0;color:#444}
  .sw{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:6px;vertical-align:-1px}
  #views{position:absolute;top:12px;right:12px;display:flex;gap:6px;z-index:5;flex-wrap:wrap;
         justify-content:flex-end}
  #views button{background:#fff;border:1px solid #cfd4de;border-radius:8px;padding:7px 12px;
         font-size:12px;cursor:pointer;color:#1f2a44;box-shadow:0 1px 3px rgba(0,0,0,.08)}
  #views button:hover{background:#eef2fb;border-color:#9fb0d8}
  #tooltip{position:absolute;bottom:14px;left:50%;transform:translateX(-50%);
           background:rgba(31,42,68,.92);color:#fff;padding:8px 14px;border-radius:8px;
           font-size:13px;display:none;pointer-events:none;z-index:4}
  #hint{position:absolute;bottom:14px;right:14px;color:#8891a3;font-size:11px;z-index:4}
  #error{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);max-width:420px;
         background:#fff;border:1px solid #e0c;border-radius:10px;padding:20px 24px;
         color:#b00020;font-size:14px;display:none;z-index:10;box-shadow:0 4px 16px rgba(0,0,0,.15)}
  .lbl{position:absolute;pointer-events:none;font-size:12px;font-weight:600;color:#1f2a44;
       transform:translate(-50%,-50%);text-shadow:0 1px 2px #fff;z-index:3}
</style>
</head>
<body>
<div id="app">
  <div id="info">
    <h1>Modelado acústico — Opción B</h1>
    <p>Habitación <b>3,20 × 3,00 × 3,00 m</b> (alto asumido) · ejes: X largo · Y ancho · Z altura</p>
    <p><span class="sw" style="background:#16a2a2"></span>12 paneles 50 mm (1,20 × 0,60)</p>
    <p><span class="sw" style="background:#f08c0a"></span>8 trampas de esquina 100 mm</p>
    <p><span class="sw" style="background:#3f9b5a"></span>2 paneles de techo colgados</p>
    <p style="margin-top:6px;color:#8891a3">FRENTE = pared de los monitores. Rotá click-arrastre · zoom rueda · mouse sobre un panel = medidas</p>
  </div>
  <div id="views">
    <button data-v="front" title="Frente = pared de los monitores">FRENTE</button>
    <button data-v="back">ATRÁS</button>
    <button data-v="left">IZQ</button>
    <button data-v="right">DER</button>
    <button data-v="top">PLANTA</button>
    <button data-v="iso">3/4</button>
    <button data-v="zoomout" title="Alejar">−</button>
    <button data-v="zoomin" title="Acercar">+</button>
  </div>
  <div id="tooltip"></div>
  <div id="hint">Modelo paramétrico — medidas reales (sin escala)</div>
  <div id="error"></div>
</div>

<script src="https://unpkg.com/three@0.128.0/build/three.min.js"></script>
<script src="https://unpkg.com/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
<script>
const BOXES = __BOXES__;
(function () {
  const app = document.getElementById('app');
  const errEl = document.getElementById('error');
  function fail(m) {
    errEl.style.display = 'block';
    errEl.textContent = 'No se pudo iniciar el visor: ' + m;
  }
  if (!window.THREE) return fail('no se pudo cargar three.js desde la CDN. Necesita internet.');
  const test = document.createElement('canvas');
  const gl = test.getContext('webgl') || test.getContext('experimental-webgl');
  if (!gl) return fail('WebGL no disponible en este navegador.');

  const escena = new THREE.Scene();
  escena.background = new THREE.Color(0xf4f5f7);

  const cam = new THREE.PerspectiveCamera(50, innerWidth / innerHeight, 0.05, 100);
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(window.devicePixelRatio);
  renderer.setSize(innerWidth, innerHeight);
  app.appendChild(renderer.domElement);

  escena.add(new THREE.HemisphereLight(0xffffff, 0xcccccc, 0.9));
  var dl = new THREE.DirectionalLight(0xffffff, 0.8);
  dl.position.set(5, 8, 4);
  escena.add(dl);

  var grid = new THREE.GridHelper(4, 8, 0xbbbbbb, 0xe2e2e2);
  grid.position.y = -0.001;
  escena.add(grid);

  var L = 3.20, W = 3.00, H = 3.00;
  function R(c) { return [c[0], c[2], -c[1]]; }
  var ry = new THREE.Matrix4().makeRotationX(-Math.PI / 2);

  var meshes = [];
  BOXES.forEach(function (b) {
    var geo = new THREE.BoxGeometry(b.extents[0], b.extents[1], b.extents[2]);
    var mat = new THREE.MeshStandardMaterial({ color: b.color, transparent: true, opacity: b.opacity, roughness: 0.85 });
    var mesh = new THREE.Mesh(geo, mat);
    var rot = ry.clone().multiply(new THREE.Matrix4().makeRotationZ(b.rz * Math.PI / 180));
    mesh.applyMatrix4(rot);
    var c = R(b.center);
    mesh.position.set(c[0], c[1], c[2]);
    mesh.userData = { label: b.label, extents: b.extents };
    escena.add(mesh);
    meshes.push(mesh);
    if (!b.wire) {
      var edges = new THREE.LineSegments(new THREE.EdgesGeometry(geo),
        new THREE.LineBasicMaterial({ color: 0x222222, transparent: true, opacity: 0.55 }));
      edges.applyMatrix4(rot);
      edges.position.set(c[0], c[1], c[2]);
      escena.add(edges);
    }
  });

  var roomEdges = new THREE.LineSegments(
    new THREE.EdgesGeometry(new THREE.BoxGeometry(L, H, W)),
    new THREE.LineBasicMaterial({ color: 0x333333 })
  );
  roomEdges.position.set(L / 2, H / 2, -W / 2);
  escena.add(roomEdges);

  function mkLbl(text, color) {
    var el = document.createElement('div');
    el.className = 'lbl';
    el.style.color = color;
    el.textContent = text;
    app.appendChild(el);
    return el;
  }

  var ox = R([0.28, 1.05, 0.02]);
  escena.add(new THREE.ArrowHelper(new THREE.Vector3(1, 0, 0), new THREE.Vector3(ox[0], ox[1], ox[2]), 1.15, 0xcc3333, 0.16, 0.10));
  escena.add(new THREE.ArrowHelper(new THREE.Vector3(0, 0, -1), new THREE.Vector3(ox[0], ox[1], ox[2]), 1.15, 0x2a8033, 0.16, 0.10));
  escena.add(new THREE.ArrowHelper(new THREE.Vector3(0, 1, 0), new THREE.Vector3(ox[0], ox[1], ox[2]), 1.15, 0x3355cc, 0.16, 0.10));

  function px(v) { return new THREE.Vector3(v[0], v[1], v[2]); }
  var labs = [
    { el: mkLbl('X = 3,20 m (largo)', '#cc3333'), pos: px(R([0.43, 1.05, 0.02])) },
    { el: mkLbl('Y = 3,00 m (ancho)', '#2a8033'), pos: px(R([0.28, 2.30, 0.02])) },
    { el: mkLbl('Z = 3,00 m (alto)', '#3355cc'), pos: px(R([0.28, 1.05, 1.27])) },
    { el: mkLbl('3,20 m', '#1f2a44'), pos: px(R([L / 2, W - 0.6, 0])) },
    { el: mkLbl('3,00 m', '#1f2a44'), pos: px(R([L - 0.6, W / 2, 0])) },
    { el: mkLbl('3,00 m', '#1f2a44'), pos: px(R([0.1, 0.1, H / 2])) },
    { el: mkLbl('2 paneles techo · 0,42 m', '#2e7d46'), pos: px(R([L / 2, W / 2, H + 0.2])) }
  ];

  var controls = new THREE.OrbitControls(cam, renderer.domElement);
  cam.position.set(6.0, 2.8, 0.6);
  controls.target.set(2.4, H / 2, -W / 2);
  controls.update();

  function goView(v) {
    if (v === 'zoomin') { controls.dollyIn(); controls.update(); return; }
    if (v === 'zoomout') { controls.dollyOut(); controls.update(); return; }
    var t = [L / 2, H / 2, -W / 2];
    var p = {
      front: [L + 3.2, H / 2, -W / 2],
      back: [-3.2, H / 2, -W / 2],
      left: [L / 2, H / 2, 3.2],
      right: [L / 2, H / 2, -(W + 3.2)],
      top: [L / 2, H + 3.6, -W / 2],
      iso: [6.0, 2.8, 0.6]
    }[v];
    if (!p) return;
    cam.position.set(p[0], p[1], p[2]);
    controls.target.set(t[0], t[1], t[2]);
    controls.update();
  }
  document.querySelectorAll('#views button').forEach(function (b) {
    b.addEventListener('click', function () { goView(b.dataset.v); });
  });

  function refreshLabels() {
    labs.forEach(function (lb) {
      var v = lb.pos.clone().project(cam);
      if (v.z > 1) { lb.el.style.display = 'none'; return; }
      lb.el.style.display = 'block';
      lb.el.style.left = ((v.x + 1) * innerWidth / 2) + 'px';
      lb.el.style.top = ((1 - v.y) * innerHeight / 2) + 'px';
    });
  }
  controls.addEventListener('change', refreshLabels);
  refreshLabels();

  var raycaster = new THREE.Raycaster();
  var pointer = new THREE.Vector2();
  var tooltip = document.getElementById('tooltip');

  renderer.domElement.addEventListener('pointermove', function (e) {
    pointer.x = (e.clientX / innerWidth) * 2 - 1;
    pointer.y = -(e.clientY / innerHeight) * 2 + 1;
    raycaster.setFromCamera(pointer, cam);
    var hit = raycaster.intersectObjects(meshes)[0];
    if (hit) {
      var u = hit.object.userData;
      var sizes = u.extents.map(function (v) { return (Math.round(v * 100) / 100) + ' m'; }).join(' × ');
      tooltip.style.display = 'block';
      tooltip.textContent = u.label + '  ·  ' + sizes;
      meshes.forEach(function (m) { m.material.emissive.setHex(m === hit.object ? 0x223344 : 0x000000); });
    } else {
      tooltip.style.display = 'none';
      meshes.forEach(function (m) { m.material.emissive.setHex(0x000000); });
    }
  });

  addEventListener('resize', function () {
    cam.aspect = innerWidth / innerHeight;
    cam.updateProjectionMatrix();
    renderer.setSize(innerWidth, innerHeight);
    refreshLabels();
  });

  (function animate() {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(escena, cam);
  })();
})();
</script>
</body>
</html>
"""

HTML_DOC = HTML_DOC.replace("__BOXES__", DATA)
with open(os.path.join(BASE, "render.html"), "w") as f:
    f.write(HTML_DOC)

print("render.html regenerado (ejes corregidos a Y-up)")