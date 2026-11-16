"""
Reference validation for the in-browser AI attendance pipeline.

Validates the exact preprocessing + decoding logic that is ported to JavaScript
(see dps_ravi/static/ai/js/): YuNet detection, MiniFASNet anti-spoofing and
ArcFace (MobileFaceNet) embeddings — using the repo's student photos.

Dev-only: requires `pip install onnxruntime pillow numpy` (not in requirements.txt).
Run:  python scripts/verify_ai_models.py
"""
import math
import sys
from pathlib import Path

import numpy as np
import onnxruntime as ort
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
MODELS = ROOT / 'dps_ravi' / 'static' / 'ai' / 'models'
PHOTOS = ROOT / 'dps_ravi' / 'media' / 'students' / 'pictures'

YUNET_SIZE = 640
SCORE_THRESH = 0.6
NMS_THRESH = 0.3
ARCFACE_TEMPLATE = np.array([
    [38.2946, 51.6963], [73.5318, 51.5014], [56.0252, 71.7366],
    [41.5493, 92.3655], [70.7299, 92.2041],
], dtype=np.float64)


def session(name):
    return ort.InferenceSession(str(MODELS / name), providers=['CPUExecutionProvider'])


def letterbox(rgb, size=YUNET_SIZE):
    """Resize keeping aspect, pad bottom/right with 0 to `size` (mirrors JS)."""
    h, w = rgb.shape[:2]
    scale = min(size / w, size / h)
    nw, nh = max(1, round(w * scale)), max(1, round(h * scale))
    img = Image.fromarray(rgb).resize((nw, nh), Image.BILINEAR)
    canvas = Image.new('RGB', (size, size), (0, 0, 0))
    canvas.paste(img, (0, 0))
    return np.asarray(canvas, dtype=np.uint8), scale, 0, 0


def yunet_postprocess(outputs, scale, pad_x, pad_y, img_w, img_h):
    """Port of OpenCV face_detect.cpp postProcess + NMS (boxes back to original coords)."""
    names = ['cls_8', 'cls_16', 'cls_32', 'obj_8', 'obj_16', 'obj_32',
             'bbox_8', 'bbox_16', 'bbox_32', 'kps_8', 'kps_16', 'kps_32']
    out = {n: outputs[i][0] for i, n in enumerate(names)}  # strip batch dim

    faces = []
    for s in (8, 16, 32):
        cls, obj = out[f'cls_{s}'][:, 0], out[f'obj_{s}'][:, 0]
        bbox, kps = out[f'bbox_{s}'], out[f'kps_{s}']
        cols = YUNET_SIZE // s
        rows = YUNET_SIZE // s
        idx = np.arange(rows * cols)
        r, c = idx // cols, idx % cols
        score = np.sqrt(np.clip(cls, 0, 1) * np.clip(obj, 0, 1))
        cx = (c + bbox[:, 0]) * s
        cy = (r + bbox[:, 1]) * s
        bw = np.exp(np.clip(bbox[:, 2], -8, 8)) * s
        bh = np.exp(np.clip(bbox[:, 3], -8, 8)) * s
        x1, y1 = cx - bw / 2, cy - bh / 2
        kx = (kps[:, 0::2] + c[:, None]) * s
        ky = (kps[:, 1::2] + r[:, None]) * s
        for i in np.where(score >= SCORE_THRESH)[0]:
            # undo letterbox: subtract pad, divide by scale → original image coords
            fx1 = (x1[i] - pad_x) / scale
            fy1 = (y1[i] - pad_y) / scale
            fw, fh = bw[i] / scale, bh[i] / scale
            kp = np.stack([(kx[i] - pad_x) / scale, (ky[i] - pad_y) / scale], axis=1)
            faces.append([fx1, fy1, fw, fh, *kp.reshape(-1), score[i]])

    faces = np.array(faces, dtype=np.float64).reshape(-1, 15)
    # greedy NMS (IoU, thresh NMS_THRESH), score-descending — mirrors dnn::NMSBoxes
    keep = []
    order = np.argsort(-faces[:, 14])
    for i in order:
        if all(_iou(faces[i, :4], faces[j, :4]) < NMS_THRESH for j in keep):
            keep.append(i)
    return faces[keep] if keep else faces[:0]


def _iou(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ix = max(0.0, min(ax + aw, bx + bw) - max(ax, bx))
    iy = max(0.0, min(ay + ah, by + bh) - max(ay, by))
    inter = ix * iy
    return inter / (aw * ah + bw * bh - inter + 1e-9)


def detect(sess, rgb):
    boxed, scale, px, py = letterbox(rgb)
    # YuNet expects BGR, 0-255, NCHW
    bgr = boxed[:, :, ::-1].astype(np.float32)
    blob = bgr.transpose(2, 0, 1)[None]
    outs = sess.run(None, {'input': blob})
    return yunet_postprocess(outs, scale, px, py, rgb.shape[1], rgb.shape[0])


def minifasnet_prob(sess, rgb, box_xywh):
    """Silent-face crop (scale 2.7), 80x80, BGR raw 0-255 (validated: T1=0.999 real, F1/F2=fake)."""
    x, y, w, h = box_xywh
    src_h, src_w = rgb.shape[:2]
    scale = min((src_h - 1) / h, (src_w - 1) / w, 2.7)
    nw, nh = w * scale, h * scale
    cx, cy = x + w / 2, y + h / 2
    x1, y1 = cx - nw / 2, cy - nh / 2
    x2, y2 = cx + nw / 2, cy + nh / 2
    x1, y1 = max(0, int(x1)), max(0, int(y1))
    x2, y2 = min(src_w - 1, int(x2)), min(src_h - 1, int(y2))
    crop = rgb[y1:y2 + 1, x1:x2 + 1]
    crop = np.asarray(Image.fromarray(crop).resize((80, 80), Image.BILINEAR), dtype=np.float32)
    bgr = crop[:, :, ::-1].astype(np.float32)  # raw 0-255 BGR — validated on T1/F1/F2
    blob = bgr.transpose(2, 0, 1)[None]
    logits = sess.run(None, {'input': blob})[0][0]
    e = np.exp(logits - logits.max())
    probs = e / e.sum()
    return float(probs[1])  # index 1 = real


def similarity_align(rgb, kps5):
    """Similarity warp of 5 detected landmarks to the 112x112 ArcFace template."""
    src = np.asarray(kps5, dtype=np.float64)
    cs, cd = src.mean(0), ARCFACE_TEMPLATE.mean(0)
    u = (src - cs)[:, 0] + 1j * (src - cs)[:, 1]
    v = (ARCFACE_TEMPLATE - cd)[:, 0] + 1j * (ARCFACE_TEMPLATE - cd)[:, 1]
    c = (np.conj(u) * v).sum() / (np.abs(u) ** 2).sum()  # dst = c * src + t
    s, theta = abs(c), math.atan2(c.imag, c.real)
    rot = np.array([[math.cos(theta), -math.sin(theta)],
                    [math.sin(theta), math.cos(theta)]])
    t = cd - s * (rot @ cs)
    # inverse map: src = inv_rot/s * (dst - t)  — for PIL affine (output→input)
    inv_r = rot.T / s
    inv_t = -(inv_r @ t)
    coeffs = (inv_r[0, 0], inv_r[0, 1], inv_t[0],
              inv_r[1, 0], inv_r[1, 1], inv_t[1])
    pil = Image.fromarray(rgb).transform((112, 112), Image.AFFINE, coeffs, resample=Image.BICUBIC)
    return np.asarray(pil, dtype=np.uint8)


def embed(sess, face112_rgb):
    """ArcFace mbf: RGB, (x-127.5)/127.5, NCHW 112x112 → 512-d."""
    x = face112_rgb.astype(np.float32)
    x = (x - 127.5) / 127.5
    blob = x.transpose(2, 0, 1)[None]
    feat = sess.run(None, {'data': blob})[0][0]
    return feat / (np.linalg.norm(feat) + 1e-9)


def cosine(a, b):
    return float(np.dot(a, b))


def main():
    yu = session('yunet_2023mar.onnx')
    fas = session('minifasnet_v2.onnx')
    arc = session('arcface_mbf.onnx')

    photos = sorted(p for p in PHOTOS.iterdir() if p.suffix.lower() in ('.jpg', '.jpeg', '.png'))
    if not photos:
        print('No photos found in', PHOTOS)
        return 1

    results = []
    for p in photos:
        rgb = np.asarray(Image.open(p).convert('RGB'))
        faces = detect(yu, rgb)
        print(f'\n== {p.name} ({rgb.shape[1]}x{rgb.shape[0]}) -> {len(faces)} face(s)')
        if len(faces) == 0:
            print('   !! no face detected')
            continue
        f = faces[0]
        box, kps, score = f[:4], f[4:14].reshape(5, 2), f[14]
        print(f'   box=({box[0]:.0f},{box[1]:.0f},{box[2]:.0f}x{box[3]:.0f}) score={score:.3f}')

        # geometric sanity: eyes above nose above mouth, box contains landmarks
        ok = (kps[0][1] < kps[2][1] < kps[3][1] and kps[1][1] < kps[2][1] < kps[4][1]
              and box[0] - 20 <= kps[:, 0].min() and kps[:, 0].max() <= box[0] + box[2] + 20
              and 0.5 < box[2] / (box[3] + 1e-9) < 1.6)
        print(f'   geometry ok: {ok}')

        real_p = minifasnet_prob(fas, rgb, box)
        print(f'   MiniFASNet P(real) = {real_p:.3f}')

        aligned = similarity_align(rgb, kps)
        feat = embed(arc, aligned)
        print(f'   embedding norm=1 (by construction), first5={[round(float(v),3) for v in feat[:5]]}')
        results.append((p.name, feat))

        # augmentation sanity: horizontal flip of the aligned crop must still match
        flipped = embed(arc, aligned[:, ::-1])
        print(f'   flip-consistency cos = {cosine(feat, flipped):.3f}')

    if len(results) >= 2:
        print('\n== Pairwise cosine similarity (RGB, (x-127.5)/127.5 alignment) ==')
        for i, (ni, _) in enumerate(results):
            for j, (nj, _) in enumerate(results):
                if j <= i:
                    continue
                print(f'   {ni[:34]:34s} vs {nj[:34]:34s} = {cosine(results[i][1], results[j][1]):+.3f}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
