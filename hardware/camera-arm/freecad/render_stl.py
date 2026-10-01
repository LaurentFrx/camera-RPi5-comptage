# -*- coding: utf-8 -*-
"""
render_stl.py — rendus PNG « techniques » de fichiers STL sans OpenGL (rastériseur z-buffer numpy).

Usage :
  python3 render_stl.py <scene.json> <sortie.png>
  scene.json = {"width":1600,"height":1200,"view":"iso"|[az,el],"ortho":true,
                "parts":[{"file":"a.stl","color":[r,g,b],"alpha":1.0}, ...],
                "title":"...", "labels":[{"text":"...","at":[x,y,z]}], "scale_bar_mm":50}
Éclairage : lambertien + ambiant, arêtes vives (dièdre > 30°) et silhouettes tracées en sombre.
"""
import sys, json, math, struct
import numpy as np
from PIL import Image, ImageDraw, ImageFont


# ------------------------------------------------------------------------------------------------
def load_stl(path):
    with open(path, "rb") as f:
        data = f.read()
    if data[:5] == b"solid" and b"facet" in data[:400]:
        tris = []
        for line in data.decode("ascii", "ignore").splitlines():
            line = line.strip()
            if line.startswith("vertex"):
                tris.append([float(v) for v in line.split()[1:4]])
        V = np.array(tris, dtype=np.float64).reshape(-1, 3, 3)
    else:
        n = struct.unpack("<I", data[80:84])[0]
        rec = np.frombuffer(data[84:84 + 50 * n], dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))
        V = rec["v"].astype(np.float64)
    return V


def view_matrix(az_deg, el_deg):
    """Repère caméra : regarde vers l'origine depuis l'azimut az (autour de Z) et l'élévation el."""
    az, el = math.radians(az_deg), math.radians(el_deg)
    d = np.array([math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)])  # direction caméra→scène inversée
    up = np.array([0, 0, 1.0])
    right = np.cross(up, d); right /= np.linalg.norm(right)
    cup = np.cross(d, right)
    return np.stack([right, cup, d])  # lignes : x_écran, y_écran, profondeur (vers la caméra)


def crease_edges(V, angle_deg=30.0):
    """Arêtes vives et de bord : retourne (P0, P1) en coordonnées monde."""
    n = len(V)
    q = np.round(V.reshape(-1, 3), 2)
    _, inv = np.unique(q, axis=0, return_inverse=True)
    idx = inv.reshape(n, 3)
    e0 = np.stack([idx[:, 0], idx[:, 1]], 1); e1 = np.stack([idx[:, 1], idx[:, 2]], 1); e2 = np.stack([idx[:, 2], idx[:, 0]], 1)
    E = np.concatenate([e0, e1, e2]); F = np.concatenate([np.arange(n)] * 3)
    Es = np.sort(E, axis=1)
    key = Es[:, 0].astype(np.int64) * (idx.max() + 1) + Es[:, 1]
    order = np.argsort(key, kind="stable"); key = key[order]; F = F[order]; E = E[order]
    N = np.cross(V[:, 1] - V[:, 0], V[:, 2] - V[:, 0])
    area = np.linalg.norm(N, axis=1); N /= (area[:, None] + 1e-12)
    uniq, start, count = np.unique(key, return_index=True, return_counts=True)
    sel = []
    cosa = math.cos(math.radians(angle_deg))
    two = count == 2
    i2 = start[two]
    dots = np.einsum("ij,ij->i", N[F[i2]], N[F[i2 + 1]])
    ok_area = (area[F[i2]] > 0.02) & (area[F[i2 + 1]] > 0.02)      # ignore les triangles dégénérés (normales bruitées)
    sel.append(i2[(dots < cosa) & ok_area])
    sel = np.concatenate(sel)
    pts = V.reshape(-1, 3)[E[sel]] if False else None
    A = q[E[sel][:, 0]]; B = q[E[sel][:, 1]]
    return A, B


def render(scene, out_png):
    W, H = scene.get("width", 1600), scene.get("height", 1200)
    view = scene.get("view", "iso")
    if view == "iso":
        az, el = -60.0, 30.0
    elif view == "front":
        az, el = -90.0, 0.0
    elif view == "side":
        az, el = 0.0, 0.0
    elif view == "top":
        az, el = -90.0, 89.9
    else:
        az, el = view
    M = view_matrix(az, el)
    parts = []
    for p in scene["parts"]:
        V = load_stl(p["file"])
        if "transform" in p:
            T = np.array(p["transform"], dtype=float)  # 4x4
            Vh = np.concatenate([V.reshape(-1, 3), np.ones((V.shape[0] * 3, 1))], 1) @ T.T
            V = Vh[:, :3].reshape(-1, 3, 3)
        parts.append((V, np.array(p.get("color", [0.7, 0.7, 0.7])), p.get("edges", True)))
    allV = np.concatenate([p[0].reshape(-1, 3) for p in parts])
    C = allV @ M.T
    lo, hi = C.min(0), C.max(0)
    center = (lo + hi) / 2
    span = (hi - lo)[:2]
    margin = scene.get("margin", 0.08)
    scale = min(W * (1 - 2 * margin) / max(span[0], 1e-6), H * (1 - 2 * margin) / max(span[1], 1e-6))
    if scene.get("scale_px_per_mm"):
        scale = scene["scale_px_per_mm"]

    def to_px(P):
        c = P @ M.T
        x = (c[..., 0] - center[0]) * scale + W / 2
        y = H / 2 - (c[..., 1] - center[1]) * scale
        return x, y, c[..., 2]

    zbuf = np.full((H, W), -np.inf)
    img = np.ones((H, W, 3)) * np.array(scene.get("bg", [1, 1, 1]))
    light = np.array(scene.get("light", [-0.4, -0.6, 1.0])); light /= np.linalg.norm(light)
    light = light @ np.linalg.inv(M) if scene.get("light_in_camera", True) else light
    # rasterisation
    for V, col, _ in parts:
        N = np.cross(V[:, 1] - V[:, 0], V[:, 2] - V[:, 0])
        nl = np.linalg.norm(N, axis=1); keep = nl > 1e-9
        V, N = V[keep], N[keep] / nl[keep][:, None]
        x, y, z = to_px(V)
        lam = np.clip(N @ light, 0, 1)
        # face arrière : normale opposée à la caméra → ombrer quand même (rendu double face)
        shade = 0.35 + 0.65 * lam
        cols = np.clip(col[None, :] * shade[:, None], 0, 1)
        xmin = np.floor(x.min(1)).astype(int); xmax = np.ceil(x.max(1)).astype(int)
        ymin = np.floor(y.min(1)).astype(int); ymax = np.ceil(y.max(1)).astype(int)
        for i in range(len(V)):
            x0, x1 = max(xmin[i], 0), min(xmax[i], W - 1)
            y0, y1 = max(ymin[i], 0), min(ymax[i], H - 1)
            if x1 < x0 or y1 < y0:
                continue
            xs = np.arange(x0, x1 + 1) + 0.5; ys = np.arange(y0, y1 + 1) + 0.5
            gx, gy = np.meshgrid(xs, ys)
            ax, ay = x[i, 0], y[i, 0]; bx, by = x[i, 1], y[i, 1]; cx, cy = x[i, 2], y[i, 2]
            det = (bx - ax) * (cy - ay) - (cx - ax) * (by - ay)
            if abs(det) < 1e-9:
                continue
            l1 = ((bx - gx) * (cy - gy) - (cx - gx) * (by - gy)) / det
            l2 = ((cx - gx) * (ay - gy) - (ax - gx) * (cy - gy)) / det
            l3 = 1 - l1 - l2
            eps = -0.002
            inside = (l1 >= eps) & (l2 >= eps) & (l3 >= eps)
            if not inside.any():
                continue
            zz = l1 * z[i, 0] + l2 * z[i, 1] + l3 * z[i, 2]
            sub = zbuf[y0:y1 + 1, x0:x1 + 1]
            upd = inside & (zz > sub)
            sub[upd] = zz[upd]
            img[y0:y1 + 1, x0:x1 + 1][upd] = cols[i]
    # arêtes
    for V, col, edges in parts:
        if not edges:
            continue
        A, B = crease_edges(V, scene.get("crease_deg", 30.0))
        ax_, ay_, az_ = to_px(A); bx_, by_, bz_ = to_px(B)
        ec = np.array(scene.get("edge_color", [0.12, 0.12, 0.14]))
        for k in range(len(A)):
            n = int(max(abs(bx_[k] - ax_[k]), abs(by_[k] - ay_[k]))) + 1
            t = np.linspace(0, 1, n)
            px = np.round(ax_[k] + (bx_[k] - ax_[k]) * t).astype(int)
            py = np.round(ay_[k] + (by_[k] - ay_[k]) * t).astype(int)
            pz = az_[k] + (bz_[k] - az_[k]) * t
            ok = (px >= 0) & (px < W) & (py >= 0) & (py < H)
            px, py, pz = px[ok], py[ok], pz[ok]
            vis = pz >= zbuf[py, px] - scene.get("edge_bias", 0.35)
            img[py[vis], px[vis]] = ec
    im = Image.fromarray((img * 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
        fontb = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
    except Exception:
        font = fontb = ImageFont.load_default()
    if scene.get("title"):
        d.text((16, 12), scene["title"], fill=(20, 20, 20), font=fontb)
    for lab in scene.get("labels", []):
        x, y, _ = to_px(np.array(lab["at"], dtype=float)[None, :])
        tx, ty = lab.get("offset", [24, -24])
        d.line([(x[0], y[0]), (x[0] + tx, y[0] + ty)], fill=(30, 30, 30), width=2)
        d.ellipse([x[0] - 4, y[0] - 4, x[0] + 4, y[0] + 4], fill=(30, 30, 30))
        d.text((x[0] + tx + (6 if tx >= 0 else -6 - d.textlength(lab["text"], font=font)), y[0] + ty - 12),
               lab["text"], fill=(20, 20, 20), font=font)
    sb = scene.get("scale_bar_mm")
    if sb:
        L = sb * scale
        x0, y0 = W - 40 - L, H - 40
        d.line([(x0, y0), (x0 + L, y0)], fill=(20, 20, 20), width=3)
        d.line([(x0, y0 - 8), (x0, y0 + 8)], fill=(20, 20, 20), width=3)
        d.line([(x0 + L, y0 - 8), (x0 + L, y0 + 8)], fill=(20, 20, 20), width=3)
        d.text((x0 + L / 2 - 30, y0 - 34), f"{sb} mm", fill=(20, 20, 20), font=font)
    if scene.get("subtitle"):
        d.text((16, H - 40), scene["subtitle"], fill=(70, 70, 70), font=font)
    im.save(out_png)
    return out_png


if __name__ == "__main__":
    scene = json.load(open(sys.argv[1], encoding="utf-8"))
    print(render(scene, sys.argv[2]))
