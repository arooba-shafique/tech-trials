window.Spoof = (function () {
  'use strict';

  function cropBox(rgb, box) {
    var x = box.x, y = box.y, w = box.w, h = box.h;
    var srcW = rgb.w, srcH = rgb.h;
    var scale = Math.min((srcH - 1) / h, (srcW - 1) / w, 2.7);
    var nw = w * scale, nh = h * scale;
    var cx = x + w / 2, cy = y + h / 2;
    var x1 = Math.max(0, Math.round(cx - nw / 2));
    var y1 = Math.max(0, Math.round(cy - nh / 2));
    var x2 = Math.min(srcW - 1, Math.round(cx + nw / 2));
    var y2 = Math.min(srcH - 1, Math.round(cy + nh / 2));
    var cw = Math.max(1, x2 - x1 + 1), ch = Math.max(1, y2 - y1 + 1);

    var src = document.createElement('canvas');
    src.width = srcW; src.height = srcH;
    src.getContext('2d').putImageData(new ImageData(new Uint8ClampedArray(rgb.data), srcW, srcH), 0, 0);
    var out = document.createElement('canvas');
    out.width = 80; out.height = 80;
    var ctx = out.getContext('2d');
    ctx.imageSmoothingQuality = 'high';
    ctx.drawImage(src, x1, y1, cw, ch, 0, 0, 80, 80);
    var rgba = ctx.getImageData(0, 0, 80, 80).data;

    var plane = 6400;
    var blob = new Float32Array(3 * plane);
    for (var i = 0, p = 0; i < plane; i++, p += 4) {
      blob[i] = rgba[p + 2];          // B, raw 0-255
      blob[plane + i] = rgba[p + 1];  // G
      blob[2 * plane + i] = rgba[p];  // R
    }
    return blob;
  }

  // Returns P(real) in [0,1]. Validated: real selfie 0.999, replay/photo attacks <=0.02.
  function pReal(sess, rgb, box) {
    var blob = cropBox(rgb, box);
    var tensor = new ort.Tensor('float32', blob, [1, 3, 80, 80]);
    return sess.run({ input: tensor }).then(function (r) {
      var logits = r['output'].data;
      var max = Math.max(logits[0], logits[1], logits[2]);
      var e0 = Math.exp(logits[0] - max), e1 = Math.exp(logits[1] - max), e2 = Math.exp(logits[2] - max);
      var sum = e0 + e1 + e2;
      return e1 / sum;
    });
  }

  return { pReal: pReal };
})();
