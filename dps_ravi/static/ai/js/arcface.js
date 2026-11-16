window.ArcFace = (function () {
  'use strict';

  var TEMPLATE = [
    [38.2946, 51.6963], [73.5318, 51.5014], [56.0252, 71.7366],
    [41.5493, 92.3655], [70.7299, 92.2041]
  ];

  function makeCanvas(w, h) {
    var cv = document.createElement('canvas');
    cv.width = w; cv.height = h;
    return cv;
  }

  // Forward similarity: dst = s*R*src + t (closed-form complex Procrustes)
  function similarityTransform(src) {
    var n = src.length;
    var csx = 0, csy = 0, cdx = 0, cdy = 0, i;
    for (i = 0; i < n; i++) { csx += src[i][0]; csy += src[i][1]; cdx += TEMPLATE[i][0]; cdy += TEMPLATE[i][1]; }
    csx /= n; csy /= n; cdx /= n; cdy /= n;
    var numRe = 0, numIm = 0, den = 0;
    for (i = 0; i < n; i++) {
      var ux = src[i][0] - csx, uy = src[i][1] - csy;
      var vx = TEMPLATE[i][0] - cdx, vy = TEMPLATE[i][1] - cdy;
      // conj(u) * v = (ux - i*uy) * (vx + i*vy)
      numRe += ux * vx + uy * vy;
      numIm += ux * vy - uy * vx;
      den += ux * ux + uy * uy;
    }
    var cRe = numRe / den, cIm = numIm / den;
    var s = Math.sqrt(cRe * cRe + cIm * cIm);
    var theta = Math.atan2(cIm, cRe);
    var cos = Math.cos(theta), sin = Math.sin(theta);
    // t = cd - s * R * cs
    var tx = cdx - s * (cos * csx - sin * csy);
    var ty = cdy - s * (sin * csx + cos * csy);
    return { s: s, cos: cos, sin: sin, tx: tx, ty: ty };
  }

  // PIL-exact affine sampler (Pillow Image.transform AFFINE + BICUBIC).
  // Maps each output pixel centre (x+0.5, y+0.5) through the inverse
  // similarity, samples 4x4 taps with Pillow's cubic macro (BICUBIC in
  // Geometry.c: p1=t1, p2=-t0+t2, p3=2(t0-t1)+t2-t3, p4=-t0+t1-t2+t3),
  // XCLIP/YCLIP tap clamping, zero-fill for out-of-source sample points,
  // and C (UINT8) truncation after 0/255 clamping.
  function align(rgb, face) {
    var W = rgb.w, H = rgb.h, src = rgb.data;
    var f = similarityTransform(face.kps);
    // inv_r = R^T / s (same op order as numpy: element / s)
    var ir00 = f.cos / f.s, ir01 = f.sin / f.s;
    var ir10 = -f.sin / f.s, ir11 = f.cos / f.s;
    var a0 = ir00, a1 = ir01, a2 = -(ir00 * f.tx + ir01 * f.ty);
    var a3 = ir10, a4 = ir11, a5 = -(ir10 * f.tx + ir11 * f.ty);

    var out = makeCanvas(112, 112);
    var ctx = out.getContext('2d');
    var img = ctx.createImageData(112, 112);
    var dst = img.data;
    var ox, oy, p;

    for (oy = 0; oy < 112; oy++) {
      var ycen = oy + 0.5;
      for (ox = 0; ox < 112; ox++) {
        var xcen = ox + 0.5;
        var X = a0 * xcen + a1 * ycen + a2;
        var Y = a3 * xcen + a4 * ycen + a5;
        p = (oy * 112 + ox) << 2;
        if (!(X >= 0 && X < W && Y >= 0 && Y < H)) {
          dst[p] = 0; dst[p + 1] = 0; dst[p + 2] = 0; dst[p + 3] = 255;
          continue;
        }
        var u = X - 0.5, v = Y - 0.5;
        var x0 = Math.floor(u), dx = u - x0;
        var y0 = Math.floor(v), dy = v - y0;
        x0 = x0 - 1; // Pillow BICUBIC_HEAD: x-- after FLOOR (taps x0-1..x0+2)
        var x1 = x0 + 1, x2 = x0 + 2, x3 = x0 + 3;
        if (x0 < 0) x0 = 0; else if (x0 >= W) x0 = W - 1;
        if (x1 < 0) x1 = 0; else if (x1 >= W) x1 = W - 1;
        if (x2 < 0) x2 = 0; else if (x2 >= W) x2 = W - 1;
        if (x3 < 0) x3 = 0; else if (x3 >= W) x3 = W - 1;
        var ry = y0 - 1, r0 = ry < 0 ? 0 : (ry >= H ? H - 1 : ry);
        ry = y0; var r1 = ry < 0 ? 0 : (ry >= H ? H - 1 : ry);
        ry = y0 + 1; var r2 = ry < 0 ? 0 : (ry >= H ? H - 1 : ry);
        ry = y0 + 2; var r3 = ry < 0 ? 0 : (ry >= H ? H - 1 : ry);
        var b0 = r0 * W, b1 = r1 * W, b2 = r2 * W, b3 = r3 * W;
        var q0 = b0 + x0, q1 = b0 + x1, q2 = b0 + x2, q3 = b0 + x3;
        var q4 = b1 + x0, q5 = b1 + x1, q6 = b1 + x2, q7 = b1 + x3;
        var q8 = b2 + x0, q9 = b2 + x1, qa = b2 + x2, qb = b2 + x3;
        var qc = b3 + x0, qd = b3 + x1, qe = b3 + x2, qf = b3 + x3;
        var ch;
        var h0 = (q0 << 2), h1 = (q1 << 2), h2 = (q2 << 2), h3 = (q3 << 2);
        var h4 = (q4 << 2), h5 = (q5 << 2), h6 = (q6 << 2), h7 = (q7 << 2);
        var h8 = (q8 << 2), h9 = (q9 << 2), ha = (qa << 2), hb = (qb << 2);
        var hc = (qc << 2), hd = (qd << 2), he = (qe << 2), hf = (qf << 2);
        var r1v = [], r2v = [], r3v = [], r4v = [];
        for (ch = 0; ch < 3; ch++) {
          // horizontal cubic per row (macro order)
          var t0 = src[h0 + ch], t1 = src[h1 + ch], t2 = src[h2 + ch], t3 = src[h3 + ch];
          var p1 = t1, p2 = -t0 + t2, p3 = 2 * (t0 - t1) + t2 - t3, p4 = -t0 + t1 - t2 + t3;
          r1v[ch] = p1 + dx * (p2 + dx * (p3 + dx * p4));
          t0 = src[h4 + ch]; t1 = src[h5 + ch]; t2 = src[h6 + ch]; t3 = src[h7 + ch];
          p1 = t1; p2 = -t0 + t2; p3 = 2 * (t0 - t1) + t2 - t3; p4 = -t0 + t1 - t2 + t3;
          r2v[ch] = p1 + dx * (p2 + dx * (p3 + dx * p4));
          t0 = src[h8 + ch]; t1 = src[h9 + ch]; t2 = src[ha + ch]; t3 = src[hb + ch];
          p1 = t1; p2 = -t0 + t2; p3 = 2 * (t0 - t1) + t2 - t3; p4 = -t0 + t1 - t2 + t3;
          r3v[ch] = p1 + dx * (p2 + dx * (p3 + dx * p4));
          t0 = src[hc + ch]; t1 = src[hd + ch]; t2 = src[he + ch]; t3 = src[hf + ch];
          p1 = t1; p2 = -t0 + t2; p3 = 2 * (t0 - t1) + t2 - t3; p4 = -t0 + t1 - t2 + t3;
          r4v[ch] = p1 + dx * (p2 + dx * (p3 + dx * p4));
          // vertical macro
          var w1 = r1v[ch], w2 = r2v[ch], w3 = r3v[ch], w4 = r4v[ch];
          p1 = w2; p2 = -w1 + w3; p3 = 2 * (w1 - w2) + w3 - w4; p4 = -w1 + w2 - w3 + w4;
          var val = p1 + dy * (p2 + dy * (p3 + dy * p4));
          dst[p + ch] = val <= 0 ? 0 : (val >= 255 ? 255 : (val | 0));
        }
        dst[p + 3] = 255;
      }
    }
    ctx.putImageData(img, 0, 0);
    return out;
  }

  function embed(sess, alignedCanvas) {
    var ctx = alignedCanvas.getContext('2d');
    var rgba = ctx.getImageData(0, 0, 112, 112).data;
    var plane = 112 * 112;
    var blob = new Float32Array(3 * plane);
    for (var i = 0, p = 0; i < plane; i++, p += 4) {
      blob[i] = (rgba[p] - 127.5) / 127.5;
      blob[plane + i] = (rgba[p + 1] - 127.5) / 127.5;
      blob[2 * plane + i] = (rgba[p + 2] - 127.5) / 127.5;
    }
    var tensor = new ort.Tensor('float32', blob, [1, 3, 112, 112]);
    return sess.run({ data: tensor }).then(function (r) {
      var raw = r['452'].data;
      var out = new Float32Array(raw.length);
      var norm = 0, j;
      for (j = 0; j < raw.length; j++) norm += raw[j] * raw[j];
      norm = Math.sqrt(norm) + 1e-9;
      for (j = 0; j < raw.length; j++) out[j] = raw[j] / norm;
      return out;
    });
  }

  return { align: align, embed: embed, TEMPLATE: TEMPLATE };
})();
