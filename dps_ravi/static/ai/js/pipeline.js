window.AIPipeline = (function () {
  'use strict';

  var sessions = { yunet: null, arcface: null, spoof: null };
  var tracker = null;
  var gallery = [];        // [{id, name, vec: Float32Array}]
  var results = {};        // studentId -> {tracks, bestCos}
  var registry = {};       // trackId -> {counted:false|studentId, votes:{}, spoofBad, spoofCounted, lastEmbed, lastSpoof}
  var stats = { active: 0, unknownActive: 0, spoofFlags: 0, spoofNow: 0, frames: 0 };
  var ready = false;

  function l2normalize(arr) {
    var n = 0, i;
    for (i = 0; i < arr.length; i++) n += arr[i] * arr[i];
    n = Math.sqrt(n) + 1e-9;
    var out = new Float32Array(arr.length);
    for (i = 0; i < arr.length; i++) out[i] = arr[i] / n;
    return out;
  }

  function cosine(a, b) {
    var s = 0;
    for (var i = 0; i < a.length; i++) s += a[i] * b[i];
    return s;
  }

  function buildGallery(embeddingData, rosterData) {
    var names = {};
    if (rosterData && rosterData.students) {
      rosterData.students.forEach(function (s) { names[s.id] = s.name; });
    }
    var byStudent = {};
    (embeddingData.students || []).forEach(function (row) {
      if (!byStudent[row.id]) byStudent[row.id] = [];
      (row.vectors || []).forEach(function (v) { byStudent[row.id].push(v); });
    });
    gallery = Object.keys(byStudent).map(function (id) {
      var vecs = byStudent[id];
      var dim = vecs[0].length;
      var mean = new Float64Array(dim);
      vecs.forEach(function (v) { for (var i = 0; i < dim; i++) mean[i] += v[i]; });
      for (var i = 0; i < dim; i++) mean[i] /= vecs.length;
      return { id: parseInt(id, 10), name: names[id] || ('Student ' + id), vec: l2normalize(mean) };
    });
  }

  function init(opts) {
    var cfg = AIModels.CFG;
    ready = false;
    results = {};
    registry = {};
    stats = { active: 0, unknownActive: 0, spoofFlags: 0, spoofNow: 0, frames: 0 };
    tracker = new ByteTrack.BYTETracker({
      trackThresh: cfg.TRACK_THRESH,
      matchThresh: cfg.MATCH_THRESH,
      trackBuffer: cfg.TRACK_BUFFER
    });
    return Promise.all([AIModels.loadYunet(), AIModels.loadArcface(), AIModels.loadSpoof()])
      .then(function (s) {
        sessions.yunet = s[0];
        sessions.arcface = s[1];
        sessions.spoof = s[2];
        buildGallery(opts.embeddings, opts.roster);
        ready = true;
        return { gallerySize: gallery.length };
      });
  }

  function processFrame(frameCanvas, rgb, w, h) {
    if (!ready) return Promise.resolve(null);
    var cfg = AIModels.CFG;
    stats.frames++;
    return YuNet.detect(sessions.yunet, frameCanvas, w, h).then(function (faces) {
      var dets = faces.map(function (f) { return { x: f.x, y: f.y, w: f.w, h: f.h, score: f.score, det: f }; });
      var active = tracker.update(dets);
      stats.active = active.length;
      var unknownNow = 0;
      var spoofNow = 0;
      var live = [];

      var work = active.map(function (track) {
        var face = track.det;
        if (!face) return Promise.resolve();
        var reg = registry[track.track_id];
        if (!reg) {
          reg = registry[track.track_id] = {
            counted: null, votes: {}, spoofBad: 0, spoofCounted: false,
            lastEmbed: -99, lastSpoof: -99, bestCos: -1
          };
        }
        var sizeOk = Math.min(face.w, face.h) >= cfg.MIN_FACE_SIDE;
        var liveEntry = {
          trackId: track.track_id,
          box: { x: face.x, y: face.y, w: face.w, h: face.h },
          studentId: null, name: null, cos: -1, votes: 0, spoofP: null, sizeOk: sizeOk
        };

        var tasks = [];

        // anti-spoof check every 2nd frame (soft flag)
        if (sizeOk && stats.frames - reg.lastSpoof >= 2) {
          reg.lastSpoof = stats.frames;
          tasks.push(Spoof.pReal(sessions.spoof, rgb, face).then(function (p) {
            reg.spoofP = p;
            liveEntry.spoofP = p;
            if (p < cfg.SPOOF_REAL_THRESHOLD) {
              reg.spoofBad++;
              if (reg.spoofBad === 2 && !reg.spoofCounted) {
                reg.spoofCounted = true;
                stats.spoofFlags++;
              }
            }
            if (p < cfg.SPOOF_REAL_THRESHOLD) spoofNow++;
          }));
        }

        // embed + match every 3rd frame
        if (sizeOk && stats.frames - reg.lastEmbed >= 3) {
          reg.lastEmbed = stats.frames;
          var aligned = ArcFace.align(rgb, face);
          tasks.push(ArcFace.embed(sessions.arcface, aligned).then(function (emb) {
            var bestId = null, bestCos = -1;
            for (var g = 0; g < gallery.length; g++) {
              var c = cosine(emb, gallery[g].vec);
              if (c > bestCos) { bestCos = c; bestId = gallery[g].id; }
            }
            reg.bestCos = Math.max(reg.bestCos, bestCos);
            if (bestCos >= cfg.MATCH_THRESHOLD) {
              reg.votes[bestId] = (reg.votes[bestId] || 0) + 1;
              // consensus: enough votes from this track → count once
              if (!reg.counted && reg.votes[bestId] >= cfg.TRACK_MIN_VOTES) {
                reg.counted = bestId;
                if (!results[bestId]) results[bestId] = { tracks: 0, bestCos: -1 };
                results[bestId].tracks++;
                results[bestId].bestCos = Math.max(results[bestId].bestCos, bestCos);
              }
            }
          }));
        }

        return Promise.all(tasks).then(function () {
          // current live view for this track
          var bestSid = null, bestVotes = 0, bestCos = -1;
          Object.keys(reg.votes).forEach(function (sid) {
            if (reg.votes[sid] > bestVotes) { bestVotes = reg.votes[sid]; bestSid = parseInt(sid, 10); }
          });
          if (bestSid !== null) {
            liveEntry.studentId = bestSid;
            liveEntry.votes = bestVotes;
            liveEntry.cos = reg.bestCos;
            var g = gallery.find(function (x) { return x.id === bestSid; });
            liveEntry.name = g ? g.name : null;
          } else {
            unknownNow++;
          }
          live.push(liveEntry);
        });
      });

      return Promise.all(work).then(function () {
        stats.unknownActive = unknownNow;
        stats.spoofNow = spoofNow;
        return {
          faces: faces,
          live: live,
          stats: {
            active: stats.active,
            recognized: live.filter(function (l) { return l.studentId !== null; }).length,
            unknown: unknownNow,
            spoofNow: spoofNow,
            spoofFlags: stats.spoofFlags
          }
        };
      });
    });
  }

  function getResults() {
    var recognizedTracks = 0, spoofedTracks = 0;
    Object.keys(registry).forEach(function (k) {
      if (registry[k].counted) recognizedTracks++;
      if (registry[k].spoofCounted) spoofedTracks++;
    });
    var students = gallery.map(function (g) {
      var r = results[g.id];
      return {
        id: g.id,
        name: g.name,
        tracks: r ? r.tracks : 0,
        bestCos: r ? r.bestCos : -1,
        suggested: r && r.tracks > 0
      };
    });
    return {
      students: students,
      totalTracks: Object.keys(registry).length,
      recognizedTracks: recognizedTracks,
      spoofedTracks: spoofedTracks,
      spoofFlags: stats.spoofFlags,
      frames: stats.frames
    };
  }

  function isReady() { return ready; }
  function gallerySize() { return gallery.length; }

  return { init: init, processFrame: processFrame, getResults: getResults, isReady: isReady, gallerySize: gallerySize };
})();
