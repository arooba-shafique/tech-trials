window.ByteTrack = (function () {
  'use strict';

  // ---------- small dense matrix helpers (row-major arrays of arrays) ----------
  function zeros(n, m) {
    var a = new Array(n);
    for (var i = 0; i < n; i++) { a[i] = new Float64Array(m); }
    return a;
  }
  function eye(n) { var a = zeros(n, n); for (var i = 0; i < n; i++) a[i][i] = 1; return a; }
  function matMul(A, B) {
    var n = A.length, k = B.length, m = B[0].length;
    var C = zeros(n, m);
    for (var i = 0; i < n; i++) for (var p = 0; p < k; p++) {
      var a = A[i][p]; if (a === 0) continue;
      for (var j = 0; j < m; j++) C[i][j] += a * B[p][j];
    }
    return C;
  }
  function matT(A) {
    var n = A.length, m = A[0].length, C = zeros(m, n);
    for (var i = 0; i < n; i++) for (var j = 0; j < m; j++) C[j][i] = A[i][j];
    return C;
  }
  function addMat(A, B) {
    var C = zeros(A.length, A[0].length);
    for (var i = 0; i < A.length; i++) for (var j = 0; j < A[0].length; j++) C[i][j] = A[i][j] + B[i][j];
    return C;
  }
  function subMat(A, B) {
    var C = zeros(A.length, A[0].length);
    for (var i = 0; i < A.length; i++) for (var j = 0; j < A[0].length; j++) C[i][j] = A[i][j] - B[i][j];
    return C;
  }
  function diagMat(vec) {
    var n = vec.length, C = zeros(n, n);
    for (var i = 0; i < n; i++) C[i][i] = vec[i] * vec[i];
    return C;
  }
  function invMat(M) { // Gauss-Jordan, square
    var n = M.length, i, j, k;
    var A = zeros(n, 2 * n);
    for (i = 0; i < n; i++) {
      for (j = 0; j < n; j++) A[i][j] = M[i][j];
      A[i][n + i] = 1;
    }
    for (i = 0; i < n; i++) {
      var piv = i;
      for (k = i; k < n; k++) if (Math.abs(A[k][i]) > Math.abs(A[piv][i])) piv = k;
      if (Math.abs(A[piv][i]) < 1e-12) continue;
      if (piv !== i) { var tmp = A[i]; A[i] = A[piv]; A[piv] = tmp; }
      var d = A[i][i];
      for (j = 0; j < 2 * n; j++) A[i][j] /= d;
      for (k = 0; k < n; k++) {
        if (k === i) continue;
        var f = A[k][i];
        if (f === 0) continue;
        for (j = 0; j < 2 * n; j++) A[k][j] -= f * A[i][j];
      }
    }
    var R = zeros(n, n);
    for (i = 0; i < n; i++) for (j = 0; j < n; j++) R[i][j] = A[i][n + j];
    return R;
  }
  function vecMat(v, M) { // 1xN * NxM
    var m = M[0].length, C = new Float64Array(m);
    for (var j = 0; j < m; j++) { var s = 0; for (var i = 0; i < v.length; i++) s += v[i] * M[i][j]; C[j] = s; }
    return C;
  }

  // ---------- Kalman filter (8-dim x,y,a,h + velocities) ----------
  function KalmanFilter() {
    this.ndim = 4; this.dt = 1;
    this.motionMat = eye(8);
    for (var i = 0; i < 4; i++) this.motionMat[i][4 + i] = this.dt;
    this.updateMat = zeros(4, 8);
    for (var j = 0; j < 4; j++) this.updateMat[j][j] = 1;
    this.stdWeightPosition = 1 / 20;
    this.stdWeightVelocity = 1 / 160;
  }
  KalmanFilter.prototype.initiate = function (meas) {
    var meanPos = meas.slice(), meanVel = [0, 0, 0, 0];
    var mean = meanPos.concat(meanVel);
    var h = meas[3];
    var std = [
      2 * this.stdWeightPosition * h, 2 * this.stdWeightPosition * h, 1e-2, 2 * this.stdWeightPosition * h,
      10 * this.stdWeightVelocity * h, 10 * this.stdWeightVelocity * h, 1e-5, 10 * this.stdWeightVelocity * h
    ];
    var cov = zeros(8, 8);
    for (var i = 0; i < 8; i++) cov[i][i] = std[i] * std[i];
    return { mean: mean, cov: cov };
  };
  KalmanFilter.prototype.predict = function (mean, cov) {
    var h = mean[3];
    var stdPos = [this.stdWeightPosition * h, this.stdWeightPosition * h, 1e-2, this.stdWeightPosition * h];
    var stdVel = [this.stdWeightVelocity * h, this.stdWeightVelocity * h, 1e-5, this.stdWeightVelocity * h];
    var motionCov = diagMat(stdPos.concat(stdVel));
    var m = mean.slice();
    for (var i = 0; i < 4; i++) m[i] = mean[i] + mean[4 + i];
    var M = this.motionMat;
    var Mc = zeros(8, 8);
    for (var a = 0; a < 8; a++) for (var b = 0; b < 8; b++) {
      var s = 0; for (var k = 0; k < 8; k++) s += M[a][k] * cov[k][b];
      Mc[a][b] = s;
    }
    var Mf = matT(M);
    var cov2 = zeros(8, 8);
    for (var a2 = 0; a2 < 8; a2++) for (var b2 = 0; b2 < 8; b2++) {
      var s2 = 0; for (var k2 = 0; k2 < 8; k2++) s2 += Mc[a2][k2] * Mf[k2][b2];
      cov2[a2][b2] = s2 + motionCov[a2][b2];
    }
    return { mean: m, cov: cov2 };
  };
  KalmanFilter.prototype.project = function (mean, cov) {
    var h = mean[3];
    var std = [this.stdWeightPosition * h, this.stdWeightPosition * h, 1e-1, this.stdWeightPosition * h];
    var innovationCov = diagMat(std);
    var pm = mean.slice(0, 4);
    var pc = zeros(4, 4);
    for (var i = 0; i < 4; i++) for (var j = 0; j < 4; j++) pc[i][j] = cov[i][j];
    return { mean: pm, cov: addMat(pc, innovationCov) };
  };
  KalmanFilter.prototype.update = function (mean, cov, meas) {
    var proj = this.project(mean, cov);
    var S = proj.cov;
    var Sinv = invMat(S);
    // K = P[:, :4] * Sinv   (P * H^T, H = [I4 0])
    var K = zeros(8, 4);
    for (var i = 0; i < 8; i++) for (var j = 0; j < 4; j++) {
      var s = 0; for (var k = 0; k < 4; k++) s += cov[i][k] * Sinv[k][j];
      K[i][j] = s;
    }
    var innov = [0, 0, 0, 0];
    for (var d = 0; d < 4; d++) innov[d] = meas[d] - proj.mean[d];
    var newMean = mean.slice();
    for (var d2 = 0; d2 < 8; d2++) newMean[d2] = mean[d2] + (K[d2][0] * innov[0] + K[d2][1] * innov[1] + K[d2][2] * innov[2] + K[d2][3] * innov[3]);
    // newCov = P - K * S * K^T
    var KS = zeros(8, 4);
    for (var a = 0; a < 8; a++) for (var b = 0; b < 4; b++) {
      var s3 = 0; for (var k3 = 0; k3 < 4; k3++) s3 += K[a][k3] * S[k3][b];
      KS[a][b] = s3;
    }
    var newCov = zeros(8, 8);
    for (var a2 = 0; a2 < 8; a2++) for (var b2 = 0; b2 < 8; b2++) {
      var s4 = 0; for (var k4 = 0; k4 < 4; k4++) s4 += KS[a2][k4] * K[b2][k4];
      newCov[a2][b2] = cov[a2][b2] - s4;
    }
    return { mean: newMean, cov: newCov };
  };

  // ---------- Hungarian assignment with cost limit ----------
  function hungarian(cost) {
    var n = cost.length;
    if (n === 0) return [];
    var m = cost[0].length;
    if (m === 0) return [];
    var transposed = false, a = cost;
    if (n > m) {
      transposed = true;
      a = zeros(m, n);
      for (var i = 0; i < n; i++) for (var j = 0; j < m; j++) a[j][i] = cost[i][j];
      n = a.length; m = a[0].length;
    }
    var u = new Float64Array(n + 1), v = new Float64Array(m + 1);
    var p = new Int32Array(m + 1), way = new Int32Array(m + 1);
    for (var i2 = 1; i2 <= n; i2++) {
      p[0] = i2;
      var j0 = 0;
      var minv = new Float64Array(m + 1);
      for (var z = 0; z <= m; z++) minv[z] = Infinity;
      var used = new Uint8Array(m + 1);
      do {
        used[j0] = 1;
        var i0 = p[j0], delta = Infinity, j1 = -1;
        for (var j = 1; j <= m; j++) {
          if (used[j]) continue;
          var cur = a[i0 - 1][j - 1] - u[i0] - v[j];
          if (cur < minv[j]) { minv[j] = cur; way[j] = j0; }
          if (minv[j] < delta) { delta = minv[j]; j1 = j; }
        }
        for (var j2 = 0; j2 <= m; j2++) {
          if (used[j2]) { u[p[j2]] += delta; v[j2] -= delta; }
          else minv[j2] -= delta;
        }
        j0 = j1;
      } while (p[j0] !== 0);
      do {
        var jW = way[j0];
        p[j0] = p[jW];
        j0 = jW;
      } while (j0);
    }
    var res = [];
    for (var jj = 1; jj <= m; jj++) {
      if (p[jj] > 0) {
        var ri = p[jj] - 1, ci = jj - 1;
        if (transposed) { var t = ri; ri = ci; ci = t; }
        res.push({ i: ri, j: ci, cost: cost[ri][ci] });
      }
    }
    return res;
  }

  function linearAssignment(cost, thresh) {
    var pairs = hungarian(cost);
    var matches = [], usedA = {}, usedB = {};
    for (var k = 0; k < pairs.length; k++) {
      if (pairs[k].cost <= thresh) {
        matches.push([pairs[k].i, pairs[k].j]);
        usedA[pairs[k].i] = 1; usedB[pairs[k].j] = 1;
      }
    }
    var ua = [], ub = [];
    var n = cost.length, m = cost[0] ? cost[0].length : 0;
    for (var i = 0; i < n; i++) if (!usedA[i]) ua.push(i);
    for (var j = 0; j < m; j++) if (!usedB[j]) ub.push(j);
    return { matches: matches, unmatchedA: ua, unmatchedB: ub };
  }

  function iou(a, b) {
    var ix = Math.max(0, Math.min(a[2], b[2]) - Math.max(a[0], b[0]));
    var iy = Math.max(0, Math.min(a[3], b[3]) - Math.max(a[1], b[1]));
    var inter = ix * iy;
    var areaA = (a[2] - a[0]) * (a[3] - a[1]);
    var areaB = (b[2] - b[0]) * (b[3] - b[1]);
    return inter / (areaA + areaB - inter + 1e-9);
  }

  // ---------- STrack ----------
  var TRACK_STATE = { NEW: 0, TRACKED: 1, LOST: 2, REMOVED: 3 };
  var idCounter = 0;

  function STrack(tlwh, score, det) {
    this._tlwh = tlwh.slice();
    this.mean = null; this.cov = null;
    this.is_activated = false;
    this.state = TRACK_STATE.NEW;
    this.score = score;
    this.track_id = 0;
    this.frame_id = 0;
    this.start_frame = 0;
    this.tracklet_len = 0;
    this.det = det || null;
  }
  STrack.tlwhToXyah = function (tlwh) {
    return [tlwh[0] + tlwh[2] / 2, tlwh[1] + tlwh[3] / 2, tlwh[2] / tlwh[3], tlwh[3]];
  };
  STrack.prototype.tlwh = function () {
    if (!this.mean) return this._tlwh.slice();
    var w = this.mean[2] * this.mean[3];
    return [this.mean[0] - w / 2, this.mean[1] - this.mean[3] / 2, w, this.mean[3]];
  };
  STrack.prototype.tlbr = function () {
    var t = this.tlwh();
    return [t[0], t[1], t[0] + t[2], t[1] + t[3]];
  };
  STrack.prototype.activate = function (kf, frameId, det) {
    this.track_id = ++idCounter;
    var st = kf.initiate(STrack.tlwhToXyah(this._tlwh));
    this.mean = st.mean; this.cov = st.cov;
    this.tracklet_len = 0;
    this.state = TRACK_STATE.TRACKED;
    if (frameId === 1) this.is_activated = true;
    this.frame_id = frameId;
    this.start_frame = frameId;
    this.det = det || this.det;
  };
  STrack.prototype.update = function (newTrack, frameId, det) {
    this.frame_id = frameId;
    this.tracklet_len += 1;
    var st = this.kf.update(this.mean, this.cov, STrack.tlwhToXyah(newTrack._tlwh));
    this.mean = st.mean; this.cov = st.cov;
    this.state = TRACK_STATE.TRACKED;
    this.is_activated = true;
    this.score = newTrack.score;
    this.det = det || newTrack.det;
  };
  STrack.prototype.reActivate = function (newTrack, frameId, det) {
    var st = this.kf.update(this.mean, this.cov, STrack.tlwhToXyah(newTrack._tlwh));
    this.mean = st.mean; this.cov = st.cov;
    this.tracklet_len = 0;
    this.state = TRACK_STATE.TRACKED;
    this.is_activated = true;
    this.frame_id = frameId;
    this.score = newTrack.score;
    this.det = det || newTrack.det;
  };
  STrack.prototype.predict = function () {
    if (!this.mean) return;
    var meanState = this.mean.slice();
    if (this.state !== TRACK_STATE.TRACKED) meanState[7] = 0;
    var st = this.kf.predict(meanState, this.cov);
    this.mean = st.mean; this.cov = st.cov;
  };
  STrack.prototype.markLost = function () { this.state = TRACK_STATE.LOST; };
  STrack.prototype.markRemoved = function () { this.state = TRACK_STATE.REMOVED; };

  // ---------- list helpers ----------
  function joint(a, b) {
    var seen = {}, out = [], i;
    for (i = 0; i < a.length; i++) { seen[a[i].track_id] = 1; out.push(a[i]); }
    for (i = 0; i < b.length; i++) if (!seen[b[i].track_id]) { seen[b[i].track_id] = 1; out.push(b[i]); }
    return out;
  }
  function sub(a, b) {
    var map = {}, i;
    for (i = 0; i < a.length; i++) map[a[i].track_id] = a[i];
    for (i = 0; i < b.length; i++) delete map[b[i].track_id];
    return Object.keys(map).map(function (k) { return map[k]; });
  }
  function removeDup(a, b) {
    var pa = a.map(function (t) { return t.tlbr(); });
    var pb = b.map(function (t) { return t.tlbr(); });
    var dupa = {}, dupb = {}, i, j;
    for (i = 0; i < a.length; i++) for (j = 0; j < b.length; j++) {
      if (iou(pa[i], pb[j]) < 0.15) {
        var timep = a[i].frame_id - a[i].start_frame;
        var timeq = b[j].frame_id - b[j].start_frame;
        if (timep > timeq) dupb[j] = 1; else dupa[i] = 1;
      }
    }
    return [
      a.filter(function (_, idx) { return !dupa[idx]; }),
      b.filter(function (_, idx) { return !dupb[idx]; })
    ];
  }

  // ---------- BYTETracker ----------
  function BYTETracker(opts) {
    opts = opts || {};
    this.trackThresh = opts.trackThresh != null ? opts.trackThresh : 0.5;
    this.matchThresh = opts.matchThresh != null ? opts.matchThresh : 0.8;
    this.bufferSize = opts.trackBuffer != null ? opts.trackBuffer : 30;
    this.maxTimeLost = this.bufferSize;
    this.detThresh = this.trackThresh + 0.1;
    this.tracked = [];
    this.lost = [];
    this.removed = [];
    this.frameId = 0;
    this.kf = new KalmanFilter();
  }

  // dets: [{x,y,w,h,score}] in original image coords
  BYTETracker.prototype.update = function (dets) {
    this.frameId++;
    var fid = this.frameId;
    var activated = [], refind = [], lostNew = [], removedNew = [];
    var i, j;

    var high = [], second = [];
    for (i = 0; i < dets.length; i++) {
      var d = dets[i];
      var det = new STrack([d.x, d.y, d.w, d.h], d.score, d.det || d);
      det.kf = this.kf;
      if (d.score > this.trackThresh) high.push(det);
      else if (d.score > 0.1 && d.score <= this.trackThresh) second.push(det);
    }

    var unconfirmed = [], trackedConfirmed = [];
    for (i = 0; i < this.tracked.length; i++) {
      if (!this.tracked[i].is_activated) unconfirmed.push(this.tracked[i]);
      else trackedConfirmed.push(this.tracked[i]);
    }

    var pool = joint(trackedConfirmed, this.lost);
    for (i = 0; i < pool.length; i++) { pool[i].kf = this.kf; pool[i].predict(); }

    // step 2: first association (high-score dets)
    var res1 = { matches: [], unmatchedA: range(pool.length), unmatchedB: range(high.length) };
    if (pool.length && high.length) {
      var cost1 = iouCost(pool, high);
      fuseScore(cost1, high);
      res1 = linearAssignment(cost1, this.matchThresh);
    }
    for (i = 0; i < res1.matches.length; i++) {
      var mi = res1.matches[i][0], mj = res1.matches[i][1];
      var tr = pool[mi], dt = high[mj];
      if (tr.state === TRACK_STATE.TRACKED) { tr.update(dt, fid, dt.det); activated.push(tr); }
      else { tr.reActivate(dt, fid, dt.det); refind.push(tr); }
    }

    // step 3: second association (low-score dets) with remaining tracked
    var remainTracked = [];
    for (i = 0; i < res1.unmatchedA.length; i++) {
      var t2 = pool[res1.unmatchedA[i]];
      if (t2.state === TRACK_STATE.TRACKED) remainTracked.push(t2);
    }
    if (remainTracked.length && second.length) {
      var cost2 = iouCost(remainTracked, second);
      var res2 = linearAssignment(cost2, 0.5);
      for (i = 0; i < res2.matches.length; i++) {
        var tr2 = remainTracked[res2.matches[i][0]], dt2 = second[res2.matches[i][1]];
        if (tr2.state === TRACK_STATE.TRACKED) { tr2.update(dt2, fid, dt2.det); activated.push(tr2); }
        else { tr2.reActivate(dt2, fid, dt2.det); refind.push(tr2); }
      }
      for (i = 0; i < res2.unmatchedA.length; i++) {
        var t3 = remainTracked[res2.unmatchedA[i]];
        if (t3.state !== TRACK_STATE.LOST) { t3.markLost(); lostNew.push(t3); }
      }
    } else {
      for (i = 0; i < remainTracked.length; i++) {
        var t4 = remainTracked[i];
        if (t4.state !== TRACK_STATE.LOST) { t4.markLost(); lostNew.push(t4); }
      }
    }

    // step 4: unconfirmed tracks vs unmatched high-score dets
    var detsLeft = res1.unmatchedB.map(function (idx) { return high[idx]; });
    if (unconfirmed.length && detsLeft.length) {
      var cost3 = iouCost(unconfirmed, detsLeft);
      fuseScore(cost3, detsLeft);
      var res3 = linearAssignment(cost3, 0.7);
      for (i = 0; i < res3.matches.length; i++) {
        var uc = unconfirmed[res3.matches[i][0]], d3 = detsLeft[res3.matches[i][1]];
        uc.update(d3, fid, d3.det); activated.push(uc);
      }
      for (i = 0; i < res3.unmatchedA.length; i++) {
        unconfirmed[res3.unmatchedA[i]].markRemoved(); removedNew.push(unconfirmed[res3.unmatchedA[i]]);
      }
      detsLeft = res3.unmatchedB.map(function (idx) { return detsLeft[idx]; });
    } else {
      for (i = 0; i < unconfirmed.length; i++) { unconfirmed[i].markRemoved(); removedNew.push(unconfirmed[i]); }
    }

    // step 5: init new stracks
    for (i = 0; i < detsLeft.length; i++) {
      var nd = detsLeft[i];
      if (nd.score < this.detThresh) continue;
      nd.kf = this.kf;
      nd.activate(this.kf, fid, nd.det);
      activated.push(nd);
    }

    // step 6: expire old lost
    for (i = 0; i < this.lost.length; i++) {
      if (fid - this.lost[i].frame_id > this.maxTimeLost) {
        this.lost[i].markRemoved(); removedNew.push(this.lost[i]);
      }
    }

    this.tracked = this.tracked.filter(function (t) { return t.state === TRACK_STATE.TRACKED; });
    this.tracked = joint(this.tracked, activated);
    this.tracked = joint(this.tracked, refind);
    this.lost = sub(this.lost, this.tracked);
    this.lost = this.lost.concat(lostNew);
    this.lost = sub(this.lost, this.removed);
    this.removed = this.removed.concat(removedNew);
    var dup = removeDup(this.tracked, this.lost);
    this.tracked = dup[0]; this.lost = dup[1];

    var out = [];
    for (i = 0; i < this.tracked.length; i++) {
      if (this.tracked[i].is_activated && this.tracked[i].frame_id === fid) out.push(this.tracked[i]);
    }
    return out;
  };

  function range(n) { var a = []; for (var i = 0; i < n; i++) a.push(i); return a; }
  function iouCost(tracks, dets) {
    var cost = zeros(tracks.length, dets.length);
    for (var i = 0; i < tracks.length; i++) {
      var ta = tracks[i].tlbr();
      for (var j = 0; j < dets.length; j++) {
        var da = dets[j].tlbr();
        cost[i][j] = 1 - iou(ta, da);
      }
    }
    return cost;
  }
  function fuseScore(cost, dets) {
    for (var i = 0; i < cost.length; i++) for (var j = 0; j < cost[0].length; j++) {
      cost[i][j] = 1 - (1 - cost[i][j]) * dets[j].score;
    }
  }

  return { BYTETracker: BYTETracker, TRACK_STATE: TRACK_STATE };
})();
