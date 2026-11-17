window.SessionUI = (function () {
  'use strict';

  var state = {
    classId: null,
    roster: null,
    subjects: [],
    stream: null,
    loopTimer: null,
    running: false,
    facing: 'user',
    _flipping: false,
    lastProcess: 0,
    processed: 0,
    fpsWindowStart: 0,
    fpsCount: 0,
    reviewData: null
  };

  var $ = function (id) { return document.getElementById(id); };

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  // ---------- setup ----------
  function onClassChange(classId) {
    state.classId = classId;
    var subj = $('ai-subj-sel');
    var start = $('ai-start-btn');
    var hint = $('ai-setup-hint');
    subj.innerHTML = '<option value="">— Select class first —</option>';
    subj.disabled = true;
    start.disabled = true;
    $('ai-review-card').style.display = 'none';
    $('ai-live-grid').style.display = 'none';
    if (!classId) { hint.textContent = 'Choose a class to begin.'; return; }
    hint.textContent = 'Loading class…';
    aiGet('/api/ai/class/' + classId + '/').then(function (data) {
      state.roster = data;
      state.subjects = data.subjects || [];
      if (!state.subjects.length) {
        hint.textContent = 'No subjects assigned to this class — assign a subject first.';
        return;
      }
      subj.innerHTML = '<option value="">— Select subject —</option>' +
        state.subjects.map(function (s) {
          return '<option value="' + s.id + '">' + esc(s.name) + '</option>';
        }).join('');
      subj.disabled = false;
      var enrolled = data.students.filter(function (s) { return s.enrolled > 0; }).length;
      var total = data.students.length;
      if (enrolled === 0) {
        hint.innerHTML = '<span style="color:#e11d48;font-weight:600">No faces enrolled for this class yet.</span> Go to Face Enrollment first.';
        start.disabled = true;
      } else {
        hint.textContent = enrolled + ' of ' + total + ' students have enrolled faces. Choose subject & date, then start.';
        start.disabled = false;
      }
    }).catch(function (e) { hint.textContent = e.message; aiToast(e.message, true); });
  }

  // ---------- camera + pipeline ----------
  function start() {
    if (state.running) return;
    var classId = state.classId;
    var subjectId = parseInt($('ai-subj-sel').value, 10);
    var date = $('ai-date').value;
    if (!classId || !subjectId || !date) { aiToast('Choose class, subject and date first', true); return; }

    var startBtn = $('ai-start-btn');
    startBtn.disabled = true;
    startBtn.textContent = '⏳ Loading models…';
    $('ai-setup-hint').textContent = 'Requesting camera and loading AI models…';

    var streamP = navigator.mediaDevices.getUserMedia({
      video: { facingMode: state.facing, width: { ideal: 1280 }, height: { ideal: 960 } }, audio: false
    });
    var dataP = Promise.all([
      aiGet('/api/ai/class/' + classId + '/'),
      aiGet('/api/ai/embeddings/' + classId + '/')
    ]);

    Promise.all([streamP, dataP]).then(function (res) {
      state.stream = res[0];
      var roster = res[1][0], embeddings = res[1][1];
      state.roster = roster;
      var video = $('ai-video');
      video.srcObject = state.stream;
      return video.play().then(function () {
        detectCams();
        startBtn.textContent = '⏳ Initializing AI…';
        return AIPipeline.init({ embeddings: embeddings, roster: roster });
      }).then(function (info) {
        if (!info.gallerySize) throw new Error('No enrolled face vectors found for this class');
        state.running = true;
        state.processed = 0;
        state.fpsWindowStart = performance.now();
        state.fpsCount = 0;
        $('ai-live-grid').style.display = 'grid';
        $('ai-review-card').style.display = 'none';
        $('ai-setup-hint').textContent = 'Session running — students appear in the list as they are recognized.';
        startBtn.style.display = 'none';
        $('ai-stop-btn').style.display = '';
        setStage('Camera on — looking for faces…');
        scheduleNext(0);
      });
    }).catch(function (e) {
      aiToast(e.message, true);
      $('ai-setup-hint').textContent = 'Could not start: ' + e.message;
      startBtn.disabled = false;
      startBtn.textContent = '▶ Start session';
      $('ai-flip-btn').style.display = 'none';
      stopStream();
    });
  }

  function stopStream() {
    if (state.stream) {
      state.stream.getTracks().forEach(function (t) { t.stop(); });
      state.stream = null;
    }
  }

  // Show the flip button only when the device actually has 2+ cameras
  // (phones); single-camera laptops never see it.
  function detectCams() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) return;
    navigator.mediaDevices.enumerateDevices().then(function (devices) {
      var n = devices.filter(function (d) { return d.kind === 'videoinput'; }).length;
      $('ai-flip-btn').style.display = n > 1 ? '' : 'none';
    }).catch(function () {});
  }

  function applyFacing() {
    // Front camera previews mirrored (selfie convention); back camera natural.
    $('ai-video').style.transform = state.facing === 'user' ? 'scaleX(-1)' : 'none';
  }

  function requestCamera(facing, exact, withSize) {
    var v = {};
    v.facingMode = exact ? { exact: facing } : facing;
    if (withSize !== false) {
      v.width = { ideal: 1280 };
      v.height = { ideal: 960 };
    }
    return navigator.mediaDevices.getUserMedia({ video: v, audio: false });
  }

  function adoptStream(s, facing) {
    state.stream = s;
    state.facing = facing;
    applyFacing();
    var video = $('ai-video');
    video.srcObject = s;
    video.play().catch(function () {});
  }

  function isGoodSwitch(s, wantFacing, oldSettings) {
    var t = s.getVideoTracks()[0];
    var st = (t && t.getSettings) ? (t.getSettings() || {}) : {};
    // Same physical camera means the switch did not actually happen.
    if (oldSettings && oldSettings.deviceId && st.deviceId &&
        st.deviceId === oldSettings.deviceId) {
      return false;
    }
    if (st.facingMode && st.facingMode !== wantFacing) return false;
    return true;
  }

  function flipCamera() {
    if (!state.running || state._flipping) return;
    state._flipping = true;
    var btn = $('ai-flip-btn');
    btn.disabled = true;
    var prev = state.facing;
    var next = prev === 'user' ? 'environment' : 'user';
    var oldSettings = {};
    if (state.stream) {
      var ot = state.stream.getVideoTracks()[0];
      if (ot && ot.getSettings) oldSettings = ot.getSettings() || {};
    }
    setStage('Switching camera…');
    // Stop the current camera first: many Android devices only feed one
    // camera stream at a time, so a parallel request gets rejected.
    stopStream();

    requestCamera(next, true)
      .catch(function () { return requestCamera(next, true, false); })
      .catch(function () { return requestCamera(next, false); })
      .then(function (s) {
        if (!isGoodSwitch(s, next, oldSettings)) {
          s.getTracks().forEach(function (t) { t.stop(); });
          throw new Error('requested camera not provided');
        }
        adoptStream(s, next);
        state._flipping = false;
        btn.disabled = false;
        setStage(next === 'environment' ? 'Back camera on' : 'Front camera on');
      })
      .catch(function (err) {
        console.error('camera flip failed:', err);
        // Restore the previous camera so the session keeps running.
        return requestCamera(prev, false).then(function (s) {
          adoptStream(s, prev);
          state._flipping = false;
          btn.disabled = false;
          setStage(prev === 'environment' ? 'Back camera on' : 'Front camera on');
          aiToast(next === 'environment'
            ? 'Back camera not available on this device'
            : 'Front camera not available on this device', true);
        }, function (err2) {
          console.error('camera restore failed:', err2);
          state._flipping = false;
          btn.disabled = false;
          setStage('Camera lost — press Stop');
          aiToast('Camera error — press Stop, then start again', true);
        });
      });
  }

  function setStage(msg) { $('ai-stage-msg').textContent = msg; }

  function scheduleNext(delay) {
    if (!state.running) return;
    state.loopTimer = setTimeout(processOnce, delay);
  }

  function processOnce() {
    if (!state.running) return;
    var video = $('ai-video');
    if (!video.videoWidth) { scheduleNext(200); return; }
    var w = video.videoWidth, h = video.videoHeight;
    var frame = document.createElement('canvas');
    frame.width = w; frame.height = h;
    var ctx = frame.getContext('2d');
    ctx.drawImage(video, 0, 0);
    var img = ctx.getImageData(0, 0, w, h);
    var rgb = { data: img.data, w: w, h: h };

    AIPipeline.processFrame(frame, rgb, w, h).then(function (result) {
      if (!state.running) return;
      state.processed++;
      state.fpsCount++;
      var now = performance.now();
      if (now - state.fpsWindowStart >= 1000) {
        $('ai-fps').textContent = (state.fpsCount * 1000 / (now - state.fpsWindowStart)).toFixed(1) + ' fps';
        state.fpsWindowStart = now;
        state.fpsCount = 0;
      }
      if (result) {
        drawOverlay(result.faces, w, h);
        renderLive(result);
        if (result.stats.active === 0) setStage('No faces — frame the class in view');
        else if (result.stats.spoofNow > 0) setStage('⚠ Possible spoof (photo/screen) detected — verify');
        else setStage(result.stats.recognized + ' recognized · ' + result.stats.unknown + ' unknown');
      }
      scheduleNext(120);
    }).catch(function (e) {
      console.error(e);
      scheduleNext(400);
    });
  }

  function drawOverlay(faces, fw, fh) {
    var video = $('ai-video');
    var canvas = $('ai-overlay');
    var dispW = video.clientWidth, dispH = video.clientHeight;
    if (!dispW || !dispH) return;
    canvas.width = dispW; canvas.height = dispH;
    var ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, dispW, dispH);
    var sx = dispW / fw, sy = dispH / fh;
    ctx.lineWidth = 2.5;
    ctx.font = '600 12px "DM Sans", sans-serif';
    faces.forEach(function (f) {
      var mx = state.facing === 'user' ? fw - (f.x + f.w) : f.x; // front camera preview is mirrored
      var x = mx * sx, y = f.y * sy, bw = f.w * sx, bh = f.h * sy;
      ctx.strokeStyle = '#14b8a6';
      ctx.strokeRect(x, y, bw, bh);
    });
    // draw labels from live results (matched by nearest box)
    var live = state._lastLive || [];
    live.forEach(function (l) {
      if (l.studentId === null || !l.box) return;
      var mx = state.facing === 'user' ? fw - (l.box.x + l.box.w) : l.box.x;
      var x = mx * sx, y = l.box.y * sy;
      var label = (l.name || 'Student') + (l.cos > 0 ? ' · ' + l.cos.toFixed(2) : '');
      var tw = ctx.measureText(label).width + 12;
      var lx = Math.max(2, Math.min(x, dispW - tw - 2));
      var ly = Math.max(16, y - 6);
      ctx.fillStyle = 'rgba(13,148,136,0.92)';
      roundRect(ctx, lx, ly - 16, tw, 18, 5);
      ctx.fill();
      ctx.fillStyle = '#fff';
      ctx.fillText(label, lx + 6, ly - 3);
    });
  }

  function roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  function renderLive(result) {
    state._lastLive = result.live;
    var s = result.stats;
    $('ai-n-recognized').textContent = s.recognized;
    $('ai-n-unknown').textContent = s.unknown;
    $('ai-n-spoof').textContent = s.spoofFlags;
    $('ai-n-tracks').textContent = s.active;

    var body = $('ai-live-body');
    var rows = result.live.filter(function (l) { return l.studentId !== null; })
      .sort(function (a, b) { return b.cos - a.cos; });
    if (!rows.length) {
      body.innerHTML = '<tr class="empty-row"><td colspan="4">' +
        (s.active > 0 ? 'Faces seen but not yet matched to enrolled students.' : 'Recognized students appear here in real time.') +
        '</td></tr>';
      $('ai-live-hint').textContent = s.active + ' face(s) in view';
      return;
    }
    var byStudent = {};
    rows.forEach(function (l) {
      if (!byStudent[l.studentId]) byStudent[l.studentId] = { name: l.name, cos: -1, votes: 0 };
      byStudent[l.studentId].cos = Math.max(byStudent[l.studentId].cos, l.cos);
      byStudent[l.studentId].votes = Math.max(byStudent[l.studentId].votes, l.votes);
    });
    body.innerHTML = Object.keys(byStudent).map(function (sid) {
      var r = byStudent[sid];
      var conf = r.cos >= 0.65 ? 'badge-green' : (r.cos >= AIModels.CFG.MATCH_THRESHOLD ? 'badge-gold' : 'badge-amber');
      return '<tr>' +
        '<td style="font-weight:600">' + esc(r.name || ('#' + sid)) + '</td>' +
        '<td class="hint">—</td>' +
        '<td style="text-align:center"><span class="badge ' + conf + '">' + r.cos.toFixed(3) + '</span></td>' +
        '<td style="text-align:center" class="mono">' + r.votes + '</td>' +
        '</tr>';
    }).join('');
    $('ai-live-hint').textContent = rows.length + ' matched student(s)';
  }

  // ---------- stop → review ----------
  function stop() {
    if (!state.running) return;
    state.running = false;
    if (state.loopTimer) clearTimeout(state.loopTimer);
    stopStream();
    $('ai-flip-btn').style.display = 'none';
    $('ai-cam-dot').style.background = '#94a3b8';
    setStage('Stopped');
    buildReview();
  }

  function buildReview() {
    var res = AIPipeline.getResults();
    state.reviewData = res;
    var rosterStudents = (state.roster && state.roster.students) || [];
    var byId = {};
    res.students.forEach(function (s) { byId[s.id] = s; });

    var tbody = $('ai-review-body');
    tbody.innerHTML = rosterStudents.map(function (st, idx) {
      var ai = byId[st.id];
      var suggested = ai && ai.suggested;
      var suggestion = suggested
        ? '<span class="badge badge-green">PRESENT</span> <span class="hint mono">' + ai.bestCos.toFixed(3) + ' · ' + ai.tracks + ' track(s)</span>'
        : '<span class="badge badge-gray">ABSENT</span>';
      var sel = suggested ? 'p' : 'a';
      return '<tr>' +
        '<td class="hint">' + (idx + 1) + '</td>' +
        '<td style="font-weight:600">' + esc(st.name) + '</td>' +
        '<td class="mono" style="color:var(--t2);font-size:12px">' + esc(st.roll || '—') + '</td>' +
        '<td style="text-align:center">' + suggestion + '</td>' +
        '<td><div class="att-btn-group">' +
          '<button type="button" class="att-btn p ' + (sel === 'p' ? 'sel' : '') + '" data-sid="' + st.id + '" data-v="present" onclick="SessionUI.pick(this)">Present</button>' +
          '<button type="button" class="att-btn a ' + (sel === 'a' ? 'sel' : '') + '" data-sid="' + st.id + '" data-v="absent" onclick="SessionUI.pick(this)">Absent</button>' +
          '<button type="button" class="att-btn l ' + (sel === 'l' ? 'sel' : '') + '" data-sid="' + st.id + '" data-v="leave" onclick="SessionUI.pick(this)">Leave</button>' +
        '</div></td>' +
        '</tr>';
    }).join('');

    var presentCount = rosterStudents.filter(function (st) { var a = byId[st.id]; return a && a.suggested; }).length;
    $('ai-save-summary').innerHTML =
      'AI suggests <b>' + presentCount + ' present</b> · ' + (rosterStudents.length - presentCount) + ' absent' +
      ' — ' + res.recognizedTracks + '/' + res.totalTracks + ' face tracks matched' +
      (res.spoofFlags > 0 ? ' · <b style="color:#e11d48">' + res.spoofFlags + ' spoof flag(s)</b>' : '') +
      ' · adjust anything, then save.';

    $('ai-review-card').style.display = '';
    $('ai-save-btn').disabled = false;
    $('ai-save-btn').textContent = '💾 Save attendance';
    $('ai-review-card').scrollIntoView({ behavior: 'smooth', block: 'start' });
    aiToast('Review the suggested list — nothing is saved until you confirm');
  }

  function pick(btn) {
    var sid = btn.getAttribute('data-sid');
    var group = btn.parentElement;
    group.querySelectorAll('.att-btn').forEach(function (b) { b.classList.remove('sel'); });
    btn.classList.add('sel');
  }

  function markAll(value) {
    document.querySelectorAll('#ai-review-body .att-btn-group').forEach(function (g) {
      g.querySelectorAll('.att-btn').forEach(function (b) {
        b.classList.toggle('sel', b.getAttribute('data-v') === value);
      });
    });
  }

  function save() {
    var classId = state.classId;
    var subjectId = parseInt($('ai-subj-sel').value, 10);
    var date = $('ai-date').value;
    var statuses = {};
    document.querySelectorAll('#ai-review-body .att-btn.sel').forEach(function (b) {
      statuses[b.getAttribute('data-sid')] = b.getAttribute('data-v');
    });
    if (!Object.keys(statuses).length) { aiToast('Nothing to save', true); return; }
    var btn = $('ai-save-btn');
    btn.disabled = true;
    btn.textContent = '⏳ Saving…';
    var res = state.reviewData || { recognizedTracks: 0, totalTracks: 0, spoofFlags: 0 };
    var presentSug = Object.keys(statuses).filter(function (k) { return statuses[k] === 'present'; }).length;
    aiPost('/api/ai/attendance/save/', {
      class_id: classId,
      subject_id: subjectId,
      date: date,
      statuses: statuses,
      meta: {
        recognized: presentSug,
        unrecognized: Math.max(0, res.totalTracks - res.recognizedTracks),
        spoof_blocked: res.spoofFlags
      }
    }).then(function (r) {
      btn.textContent = '✓ Saved ' + r.saved + ' records';
      aiToast('Attendance saved (' + r.saved + ' students, source = AI)');
    }).catch(function (e) {
      aiToast(e.message, true);
      btn.disabled = false;
      btn.textContent = '💾 Save attendance';
    });
  }

  function init() {
    $('ai-class-sel').addEventListener('change', function () {
      onClassChange(this.value ? parseInt(this.value, 10) : null);
    });
    $('ai-start-btn').addEventListener('click', start);
    $('ai-stop-btn').addEventListener('click', stop);
    $('ai-flip-btn').addEventListener('click', flipCamera);
    $('ai-save-btn').addEventListener('click', save);
    $('ai-all-present').addEventListener('click', function () { markAll('present'); });
    $('ai-all-absent').addEventListener('click', function () { markAll('absent'); });
    $('ai-stop-btn').style.display = 'none';
    window.addEventListener('beforeunload', function () { stopStream(); });
  }

  return { init: init, pick: pick };
})();

document.addEventListener('DOMContentLoaded', SessionUI.init);
