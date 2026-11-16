window.YuNet = (function () {
  'use strict';

  var OUT_NAMES = ['cls_8', 'cls_16', 'cls_32', 'obj_8', 'obj_16', 'obj_32',
    'bbox_8', 'bbox_16', 'bbox_32', 'kps_8', 'kps_16', 'kps_32'];

  // PIL-equivalent separable triangle resample (support = scale on downscale,
  // uint8 quantization between passes) so detections match the validated
  // Python reference (canvas smoothing differs from PIL BILINEAR otherwise).
  function makeCoef(n, out) {
    var sc = n / out;
    var R = Math.max(sc, 1);
    var taps = new Array(out), ws = new Array(out);
    for (var x = 0; x < out; x++) {
      var c = (x + 0.5) * sc;
      var p0 = Math.floor(c - R), p1 = Math.ceil(c + R);
      var ta = [], wa = [], sum = 0;
      for (var p = p0; p <= p1; p++) {
        var t = (p + 0.5 - c) / R;
        var w = 1 - Math.abs(t);
        if (w < 0) w = 0;
        if (p < 0 || p >= n) w = 0;
        ta.push(p < 0 ? 0 : (p >= n ? n - 1 : p));
        wa.push(w);
        sum += w;
      }
      if (sum <= 0) { sum = 1; wa[0] = 1; }
      for (var k = 0; k < wa.length; k++) wa[k] /= sum;
      taps[x] = ta; ws[x] = wa;
    }
    return { taps: taps, ws: ws };
  }

  function letterboxBlob(source, srcW, srcH, size) {
    var scale = Math.min(size / srcW, size / srcH);
    var nw = Math.max(1, Math.round(srcW * scale));
    var nh = Math.max(1, Math.round(srcH * scale));
    var cv = document.createElement('canvas');
    cv.width = srcW; cv.height = srcH;
    var c0 = cv.getContext('2d');
    c0.drawImage(source, 0, 0);
    var rgba = c0.getImageData(0, 0, srcW, srcH).data;

    var coefX = makeCoef(srcW, nw);
    var hbuf = new Float64Array(srcH * nw * 3);
    for (var y = 0; y < srcH; y++) {
      var rowOff = y * srcW * 4;
      var bo = y * nw * 3;
      for (var xo = 0; xo < nw; xo++) {
        var ta = coefX.taps[xo], wa = coefX.ws[xo];
        var r = 0, g = 0, b = 0;
        for (var k = 0; k < ta.length; k++) {
          var w = wa[k];
          if (w === 0) continue;
          var p = rowOff + ta[k] * 4;
          r += rgba[p] * w; g += rgba[p + 1] * w; b += rgba[p + 2] * w;
        }
        var q = bo + xo * 3;
        hbuf[q] = Math.floor(r + 0.5);
        hbuf[q + 1] = Math.floor(g + 0.5);
        hbuf[q + 2] = Math.floor(b + 0.5);
      }
    }

    var coefY = makeCoef(srcH, nh);
    var plane = size * size;
    var blob = new Float32Array(3 * plane);  // zero-filled: letterbox padding stays black
    for (var yo = 0; yo < nh; yo++) {
      var ty = coefY.taps[yo], wy = coefY.ws[yo];
      var rowBase = yo * size;
      for (var x = 0; x < nw; x++) {
        var r2 = 0, g2 = 0, b2 = 0;
        for (var k2 = 0; k2 < ty.length; k2++) {
          var w2 = wy[k2];
          if (w2 === 0) continue;
          var s = ty[k2] * nw * 3 + x * 3;
          r2 += hbuf[s] * w2; g2 += hbuf[s + 1] * w2; b2 += hbuf[s + 2] * w2;
        }
        var px = rowBase + x;
        blob[px] = Math.floor(b2 + 0.5);
        blob[plane + px] = Math.floor(g2 + 0.5);
        blob[2 * plane + px] = Math.floor(r2 + 0.5);
      }
    }
    return { blob: blob, scale: scale };
  }

  function iou(a, b) {
    var ix = Math.max(0, Math.min(a[0] + a[2], b[0] + b[2]) - Math.max(a[0], b[0]));
    var iy = Math.max(0, Math.min(a[1] + a[3], b[1] + b[3]) - Math.max(a[1], b[1]));
    var inter = ix * iy;
    return inter / (a[2] * a[3] + b[2] * b[3] - inter + 1e-9);
  }

  function detect(sess, source, srcW, srcH) {
    var cfg = AIModels.CFG;
    var lb = letterboxBlob(source, srcW, srcH, cfg.YUNET_SIZE);
    var size = cfg.YUNET_SIZE;
    var input = new ort.Tensor('float32', lb.blob, [1, 3, size, size]);
    var outs = sess.outputNames.reduce(function (acc, n) { acc[n] = null; return acc; }, {});
    // run returns a map keyed by output name
    var results = null;
    return sess.run({ input: input }).then(function (r) {
      results = r;
      var faces = [];
      var scale = lb.scale;
      for (var si = 0; si < 3; si++) {
        var s = [8, 16, 32][si];
        var cls = results['cls_' + s].data;
        var obj = results['obj_' + s].data;
        var bbox = results['bbox_' + s].data;
        var kps = results['kps_' + s].data;
        var cols = size / s, rows = size / s;
        var stride = cols * rows;
        for (var idx = 0; idx < stride; idx++) {
          var sc = Math.sqrt(clamp01(cls[idx]) * clamp01(obj[idx]));
          if (sc < cfg.YUNET_SCORE) continue;
          var r = Math.floor(idx / cols), c = idx % cols;
          var cx = (c + bbox[idx * 4]) * s;
          var cy = (r + bbox[idx * 4 + 1]) * s;
          var bw = Math.exp(clamp(bbox[idx * 4 + 2], -8, 8)) * s;
          var bh = Math.exp(clamp(bbox[idx * 4 + 3], -8, 8)) * s;
          var x1 = (cx - bw / 2) / scale;
          var y1 = (cy - bh / 2) / scale;
          var w = bw / scale, h = bh / scale;
          var k = [];
          for (var j = 0; j < 5; j++) {
            k.push([(kps[idx * 10 + j * 2] + c) * s / scale,
                    (kps[idx * 10 + j * 2 + 1] + r) * s / scale]);
          }
          faces.push({ x: x1, y: y1, w: w, h: h, score: sc, kps: k });
        }
      }
      // greedy NMS, score descending
      faces.sort(function (a, b) { return b.score - a.score; });
      var keep = [];
      for (var i = 0; i < faces.length; i++) {
        var f = faces[i], ok = true;
        for (var j2 = 0; j2 < keep.length; j2++) {
          if (iou([f.x, f.y, f.w, f.h], [keep[j2].x, keep[j2].y, keep[j2].w, keep[j2].h]) >= cfg.YUNET_NMS) { ok = false; break; }
        }
        if (ok) keep.push(f);
      }
      return keep;
    });
  }

  function clamp(v, lo, hi) { return v < lo ? lo : (v > hi ? hi : v); }
  function clamp01(v) { return v < 0 ? 0 : (v > 1 ? 1 : v); }

  return { detect: detect };
})();
