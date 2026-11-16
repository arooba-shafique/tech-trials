window.AIModels = (function () {
  'use strict';
  var BASE = '/static/ai/models/';
  var CFG = {
    MATCH_THRESHOLD: 0.50,
    SPOOF_REAL_THRESHOLD: 0.5,
    MIN_FACE_SIDE: 90,
    TRACK_MIN_VOTES: 2,
    YUNET_SCORE: 0.5,
    YUNET_NMS: 0.3,
    YUNET_SIZE: 640,
    TRACK_THRESH: 0.5,
    MATCH_THRESH: 0.8,
    TRACK_BUFFER: 30
  };

  if (typeof ort !== 'undefined') {
    ort.env.wasm.wasmPaths = '/static/ai/js/';
    ort.env.wasm.numThreads = 1;
    // Inference in a worker: avoids a main-thread wasm futex spin (renderer
    // freeze after heavy mixed session use) and keeps the UI thread free.
    ort.env.wasm.proxy = true;
  }

  var cache = {};

  function load(file) {
    if (cache[file]) return cache[file];
    cache[file] = fetch(BASE + file)
      .then(function (r) {
        if (!r.ok) throw new Error('Failed to fetch ' + file + ' (HTTP ' + r.status + ')');
        return r.arrayBuffer();
      })
      .then(function (buf) {
        return ort.InferenceSession.create(buf, {
          executionProviders: ['wasm'],
          graphOptimizationLevel: 'all'
        });
      })
      .catch(function (e) { delete cache[file]; throw e; });
    return cache[file];
  }

  return {
    CFG: CFG,
    loadYunet: function () { return load('yunet_2023mar.onnx'); },
    loadArcface: function () { return load('arcface_mbf.onnx'); },
    loadSpoof: function () { return load('minifasnet_v2.onnx'); }
  };
})();
