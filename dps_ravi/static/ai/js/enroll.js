window.EnrollUI = (function () {
  'use strict';

  var state = {
    classId: null,
    roster: [],
    busy: false,
    stream: null,
    capStudent: null,
    capShots: [],
    capLoop: null,
    capLastDetect: 0,
    modelsLoading: false
  };

  var $ = function (id) { return document.getElementById(id); };

  // ---------- roster ----------
  function loadRoster(classId) {
    var body = $('en-roster-body');
    body.innerHTML = '<tr class="empty-row"><td colspan="5">Loading roster…</td></tr>';
    $('en-stats').style.display = 'none';
    $('en-auto-all-btn').disabled = true;
    return aiGet('/api/ai/class/' + classId + '/').then(function (data) {
      state.roster = data.students;
      renderRoster();
      renderStats();
      $('en-auto-all-btn').disabled = false;
      $('en-roster-hint').textContent = data.students.length + ' students · ' +
        data.students.filter(function (s) { return s.enrolled > 0; }).length + ' enrolled';
    }).catch(function (e) {
      body.innerHTML = '<tr class="empty-row"><td colspan="5">' + esc(e.message) + '</td></tr>';
      aiToast(e.message, true);
    });
  }

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function renderRoster() {
    var body = $('en-roster-body');
    if (!state.roster.length) {
      body.innerHTML = '<tr class="empty-row"><td colspan="5">No students in this class.</td></tr>';
      return;
    }
    body.innerHTML = state.roster.map(function (s) {
      var badge = s.enrolled > 0
        ? '<span class="badge badge-green" id="en-badge-' + s.id + '">' + s.enrolled + ' vectors</span>'
        : '<span class="badge badge-amber" id="en-badge-' + s.id + '">not enrolled</span>';
      var photo = s.photo
        ? '<img src="' + esc(s.photo) + '" style="width:38px;height:38px;border-radius:50%;object-fit:cover;border:2px solid var(--rim)">'
        : '<div style="width:38px;height:38px;border-radius:50%;background:var(--panel2);border:2px dashed var(--rim2);display:flex;align-items:center;justify-content:center;font-size:15px;color:var(--t3)">?</div>';
      return '<tr>' +
        '<td>' + photo + '</td>' +
        '<td><div style="font-weight:600">' + esc(s.name) + '</div><div class="hint" id="en-status-' + s.id + '"></div></td>' +
        '<td class="mono" style="color:var(--t2);font-size:12px">' + esc(s.roll || '—') + '</td>' +
        '<td style="text-align:center">' + badge + '</td>' +
        '<td style="text-align:right;white-space:nowrap">' +
          '<button class="btn btn-gold btn-xs" ' + (s.photo ? '' : 'disabled') + ' onclick="EnrollUI.autoOne(' + s.id + ')">⚡ From photo</button> ' +
          '<button class="btn btn-blue btn-xs" onclick="EnrollUI.openCapture(' + s.id + ')">📷 Capture</button> ' +
          '<button class="btn btn-rose btn-xs" ' + (s.enrolled > 0 ? '' : 'disabled') + ' onclick="EnrollUI.clearOne(' + s.id + ')">Clear</button>' +
        '</td></tr>';
    }).join('');
  }

  function renderStats() {
    var total = state.roster.length;
    var done = state.roster.filter(function (s) { return s.enrolled > 0; }).length;
    var vectors = state.roster.reduce(function (a, s) { return a + s.enrolled; }, 0);
    $('en-stats').style.display = 'flex';
    $('en-stat-total').textContent = total;
    $('en-stat-done').textContent = done;
    $('en-stat-missing').textContent = total - done;
    $('en-stat-vectors').textContent = vectors;
  }

  function setStatus(id, msg, cls) {
    var el = $('en-status-' + id);
    if (!el) return;
    el.textContent = msg || '';
    el.style.color = cls === 'err' ? '#e11d48' : (cls === 'ok' ? '#16a34a' : '');
  }

  function updateBadge(id, count) {
    var s = state.roster.find(function (x) { return x.id === id; });
    if (s) s.enrolled = count;
    var el = $('en-badge-' + id);
    if (el) {
      if (count > 0) { el.className = 'badge badge-green'; el.textContent = count + ' vectors'; }
      else { el.className = 'badge badge-amber'; el.textContent = 'not enrolled'; }
    }
    renderStats();
  }

  // ---------- model-backed embedding ----------
  function ensureModels() {
    if (!state.modelsLoading) {
      state.modelsLoading = Promise.all([AIModels.loadYunet(), AIModels.loadArcface()])
        .then(function (s) {
          AIModels._yunet = s[0];
          AIModels._arcface = s[1];
          return true;
        })
        .catch(function (e) { state.modelsLoading = null; throw e; });
    }
    return state.modelsLoading;
  }

  function embedFromBitmap(bmp) {
    var cv = document.createElement('canvas');
    cv.width = bmp.width; cv.height = bmp.height;
    var ctx = cv.getContext('2d');
    ctx.drawImage(bmp, 0, 0);
    var rgb = ctx.getImageData(0, 0, cv.width, cv.height);
    var rgbStruct = { data: rgb.data, w: cv.width, h: cv.height };
    return YuNet.detect(AIModels._yunet, cv, cv.width, cv.height).then(function (faces) {
      if (!faces.length) throw new Error('No face found in photo');
      faces.sort(function (a, b) { return (b.w * b.h) - (a.w * a.h); });
      var f = faces[0];
      if (Math.min(f.w, f.h) < AIModels.CFG.MIN_FACE_SIDE) throw new Error('Face too small in photo — use a closer photo');
      var aligned = ArcFace.align(rgbStruct, f);
      return ArcFace.embed(AIModels._arcface, aligned);
    });
  }

  function saveEmbeddings(studentId, vectors, source) {
    return aiPost('/api/ai/enroll/', {
      student_id: studentId,
      embeddings: vectors,
      source: source,
      model_version: 'arcface-mbf-v1',
      quality: 1
    }).then(function (r) {
      updateBadge(studentId, r.total);
      return r;
    });
  }

  function fetchPhotoBitmap(url) {
    return fetch(url).then(function (r) {
      if (!r.ok) throw new Error('Could not load profile photo');
      return r.blob();
    }).then(function (b) { return createImageBitmap(b); });
  }

  function autoOne(studentId) {
    if (state.busy) return;
    var s = state.roster.find(function (x) { return x.id === studentId; });
    if (!s || !s.photo) return;
    state.busy = true;
    setStatus(studentId, 'Loading models…');
    ensureModels().then(function () {
      setStatus(studentId, 'Analyzing photo…');
      return fetchPhotoBitmap(s.photo);
    }).then(function (bmp) {
      return embedFromBitmap(bmp);
    }).then(function (vec) {
      setStatus(studentId, 'Saving…');
      return saveEmbeddings(studentId, [vec], 'photo');
    }).then(function () {
      setStatus(studentId, 'Enrolled ✓', 'ok');
      aiToast('Enrolled ' + s.name + ' from profile photo');
    }).catch(function (e) {
      setStatus(studentId, e.message, 'err');
    }).finally(function () { state.busy = false; });
  }

  function autoAll() {
    if (state.busy) return;
    var pending = state.roster.filter(function (s) { return s.photo && s.enrolled === 0; });
    if (!pending.length) { aiToast('No pending students with profile photos'); return; }
    state.busy = true;
    $('en-auto-all-btn').disabled = true;
    var i = 0, ok = 0, fail = 0;
    var statusEl = $('en-bulk-status');
    function step() {
      if (i >= pending.length) {
        state.busy = false;
        $('en-auto-all-btn').disabled = false;
        statusEl.textContent = 'Done: ' + ok + ' enrolled, ' + fail + ' failed';
        aiToast('Auto-enroll finished: ' + ok + ' ok, ' + fail + ' failed');
        return;
      }
      var s = pending[i++];
      statusEl.textContent = 'Processing ' + i + '/' + pending.length + ' — ' + s.name;
      setStatus(s.id, 'Analyzing…');
      ensureModels()
        .then(function () { return fetchPhotoBitmap(s.photo); })
        .then(function (bmp) { return embedFromBitmap(bmp); })
        .then(function (vec) { return saveEmbeddings(s.id, [vec], 'photo'); })
        .then(function () { ok++; setStatus(s.id, 'Enrolled ✓', 'ok'); })
        .catch(function (e) { fail++; setStatus(s.id, e.message, 'err'); })
        .finally(function () { setTimeout(step, 60); });
    }
    ensureModels().then(step).catch(function (e) {
      aiToast(e.message, true); state.busy = false; $('en-auto-all-btn').disabled = false;
    });
  }

  function clearOne(studentId) {
    if (state.busy) return;
    var s = state.roster.find(function (x) { return x.id === studentId; });
    if (!s || s.enrolled === 0) return;
    if (!confirm('Remove all stored face vectors for ' + s.name + '?')) return;
    state.busy = true;
    aiPost('/api/ai/enroll/' + studentId + '/delete/', {}).then(function () {
      updateBadge(studentId, 0);
      setStatus(studentId, 'Cleared');
      aiToast('Cleared face data for ' + s.name);
    }).catch(function (e) { aiToast(e.message, true); })
      .finally(function () { state.busy = false; });
  }

  // ---------- capture wizard ----------
  function openCapture(studentId) {
    var s = state.roster.find(function (x) { return x.id === studentId; });
    if (!s) return;
    state.capStudent = s;
    state.capShots = [];
    $('en-cap-name').textContent = s.name;
    $('en-cap-shots').innerHTML = '';
    $('en-cap-count').textContent = '0 / 5 captured';
    $('en-cap-btn').disabled = true;
    $('en-cap-save').disabled = true;
    $('en-cap-msg').textContent = 'Starting camera…';
    $('en-capture-modal').classList.add('open');

    ensureModels().then(function () { return true; }).catch(function (e) {
      $('en-cap-msg').textContent = e.message;
      aiToast(e.message, true);
    });

    navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 960 } }, audio: false })
      .then(function (stream) {
        state.stream = stream;
        var v = $('en-cap-video');
        v.srcObject = stream;
        return v.play();
      })
      .then(function () { startCapLoop(); })
      .catch(function (e) {
        $('en-cap-msg').textContent = 'Camera unavailable: ' + e.message;
        aiToast('Camera error: ' + e.message, true);
      });
  }

  function capFrame() {
    var v = $('en-cap-video');
    if (!v.videoWidth) return null;
    var cv = document.createElement('canvas');
    cv.width = v.videoWidth; cv.height = v.videoHeight;
    var ctx = cv.getContext('2d');
    ctx.drawImage(v, 0, 0);
    var img = ctx.getImageData(0, 0, cv.width, cv.height);
    return { canvas: cv, rgb: { data: img.data, w: cv.width, h: cv.height } };
  }

  function startCapLoop() {
    var video = $('en-cap-video');
    var overlay = $('en-cap-canvas');
    function tick() {
      if (!state.stream) return;
      var now = performance.now();
      if (now - state.capLastDetect >= 450 && video.videoWidth) {
        state.capLastDetect = now;
        var frame = capFrame();
        if (frame && AIModels._yunet) {
          YuNet.detect(AIModels._yunet, frame.canvas, frame.canvas.width, frame.canvas.height).then(function (faces) {
            drawCapOverlay(overlay, frame.canvas.width, frame.canvas.height, faces);
            updateCapState(faces);
          }).catch(function () {});
        }
      }
      state.capLoop = requestAnimationFrame(tick);
    }
    tick();
  }

  function drawCapOverlay(overlay, fw, fh, faces) {
    var video = $('en-cap-video');
    var dispW = video.clientWidth, dispH = video.clientHeight;
    overlay.width = dispW; overlay.height = dispH;
    var ctx = overlay.getContext('2d');
    ctx.clearRect(0, 0, dispW, dispH);
    var sx = dispW / fw, sy = dispH / fh;
    ctx.lineWidth = 3;
    faces.forEach(function (f) {
      // video is CSS-mirrored; mirror x for overlay
      var mx = fw - (f.x + f.w);
      ctx.strokeStyle = Math.min(f.w, f.h) * Math.min(sx, sy) >= AIModels.CFG.MIN_FACE_SIDE ? '#14b8a6' : '#d97706';
      ctx.strokeRect(mx * sx, f.y * sy, f.w * sx, f.h * sy);
    });
  }

  function updateCapState(faces) {
    var msg = $('en-cap-msg');
    if (!faces.length) { msg.textContent = 'No face detected — face the camera'; $('en-cap-btn').disabled = true; return; }
    if (faces.length > 1) { msg.textContent = 'Multiple faces — only the student should be in frame'; $('en-cap-btn').disabled = true; return; }
    var f = faces[0];
    var minSide = Math.min(f.w, f.h);
    if (minSide < AIModels.CFG.MIN_FACE_SIDE) {
      msg.textContent = 'Move closer — face is too small (' + Math.round(minSide) + 'px, need ' + AIModels.CFG.MIN_FACE_SIDE + ')';
      $('en-cap-btn').disabled = true;
      return;
    }
    msg.textContent = 'Looks good — face detected (' + Math.round(minSide) + 'px)';
    $('en-cap-btn').disabled = state.capShots.length >= 5;
    state._lastFaces = faces;
  }

  function captureShot() {
    var faces = state._lastFaces;
    if (!faces || faces.length !== 1 || state.capShots.length >= 5) return;
    var frame = capFrame();
    if (!frame) return;
    var f = faces[0];
    // store aligned112 thumbnail + full embedding later (embed now while we have rgb)
    var aligned = ArcFace.align(frame.rgb, f);
    ArcFace.embed(AIModels._arcface, aligned).then(function (vec) {
      state.capShots.push(vec);
      addShotThumb(aligned, state.capShots.length);
      $('en-cap-count').textContent = state.capShots.length + ' / 5 captured';
      $('en-cap-btn').disabled = state.capShots.length >= 5;
      $('en-cap-save').disabled = state.capShots.length < 3;
      $('en-cap-msg').textContent = state.capShots.length < 3
        ? 'Captured ' + state.capShots.length + ' — need at least 3'
        : 'Captured ' + state.capShots.length + ' — ready to save';
    }).catch(function (e) { aiToast(e.message, true); });
  }

  function addShotThumb(alignedCanvas, n) {
    var wrap = $('en-cap-shots');
    var c = document.createElement('canvas');
    c.width = 44; c.height = 44;
    var ctx = c.getContext('2d');
    ctx.drawImage(alignedCanvas, 0, 0, 44, 44);
    c.style.cssText = 'width:44px;height:44px;border-radius:8px;border:2px solid #14b8a6;object-fit:cover';
    c.title = 'Shot ' + n;
    wrap.appendChild(c);
  }

  function saveCapture() {
    if (state.capShots.length < 3 || !state.capStudent) return;
    var sid = state.capStudent.id;
    $('en-cap-save').disabled = true;
    $('en-cap-save').textContent = 'Saving…';
    saveEmbeddings(sid, state.capShots, 'capture').then(function () {
      setStatus(sid, 'Enrolled (' + state.capShots.length + ' shots) ✓', 'ok');
      aiToast('Enrolled ' + state.capStudent.name + ' with ' + state.capShots.length + ' captures');
      closeCapture();
    }).catch(function (e) {
      aiToast(e.message, true);
      $('en-cap-save').disabled = false;
    }).finally(function () { $('en-cap-save').textContent = 'Save enrollment'; });
  }

  function closeCapture() {
    if (state.capLoop) cancelAnimationFrame(state.capLoop);
    state.capLoop = null;
    if (state.stream) {
      state.stream.getTracks().forEach(function (t) { t.stop(); });
      state.stream = null;
    }
    $('en-cap-modal').classList.remove('open');
    state.capStudent = null;
    state.capShots = [];
    state._lastFaces = null;
  }

  function init() {
    $('en-class-sel').addEventListener('change', function () {
      state.classId = this.value ? parseInt(this.value, 10) : null;
      if (state.classId) loadRoster(state.classId);
      else {
        $('en-roster-body').innerHTML = '<tr class="empty-row"><td colspan="5">Select a class above to load its roster.</td></tr>';
        $('en-stats').style.display = 'none';
        $('en-auto-all-btn').disabled = true;
      }
    });
    $('en-auto-all-btn').addEventListener('click', autoAll);
    $('en-cap-btn').addEventListener('click', captureShot);
    $('en-cap-save').addEventListener('click', saveCapture);
    $('en-capture-modal').addEventListener('click', function (e) {
      if (e.target === this) closeCapture();
    });
  }

  return {
    init: init, autoOne: autoOne, clearOne: clearOne,
    openCapture: openCapture, closeCapture: closeCapture
  };
})();

document.addEventListener('DOMContentLoaded', EnrollUI.init);
