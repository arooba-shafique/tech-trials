/* =====================================================
   DPS Ravi Campus — Admin Dashboard Scripts
   ===================================================== */

// ════════════════════════════════════════════
// DATE DISPLAY
// ════════════════════════════════════════════
(function () {
    var d = new Date();
    var days   = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
    var months = ['January','February','March','April','May','June',
                  'July','August','September','October','November','December'];
    var el = document.getElementById('topDate');
    if (el) el.textContent = days[d.getDay()] + ', ' + d.getDate() + ' ' + months[d.getMonth()] + ' ' + d.getFullYear();
})();

// ════════════════════════════════════════════
// NAVIGATION
// ════════════════════════════════════════════
var titles = {
    credentials: 'Credentials Generator',
    dashboard:   'Dashboard',
    students:    'Students',
    staff:       'Staff',
    parents:     'Parents',
    classes:     'Classes',
    subjects:    'Subjects',
    assignments: 'Staff Assignments',
    timetable:   'Timetable',
    exams:       'Exams',
    results:     'Grades & Results',
    'salary-config':    'Salary Configuration',
    'salary-sheet':     'Salary Sheet',
    'salary-slips':     'Salary Slips',
    'hr-attendance':    'Monthly Attendance',
    'left-employees':   'Left Employees'
};

function showSection(name, el) {
    document.querySelectorAll('.section').forEach(function (s) { s.classList.remove('active'); });
    document.querySelectorAll('.nav-item').forEach(function (n) { n.classList.remove('active'); });
    document.getElementById('section-' + name).classList.add('active');
    if (el) el.classList.add('active');
    document.getElementById('pageTitle').textContent = titles[name] || name;
    if (name === 'dashboard') {
        history.pushState(null, '', '/admin-console/');
    } else {
        history.pushState(null, '', '/admin-console/?section=' + name);
    }
    if (window.innerWidth <= 768) {
        document.querySelector('.sidebar').classList.remove('show');
        var ov = document.getElementById('sidebarOverlay');
        if (ov) ov.classList.remove('show');
    }
}

function toggleSidebar() {
    document.querySelector('.sidebar').classList.toggle('show');
    var ov = document.getElementById('sidebarOverlay');
    if (ov) ov.classList.toggle('show');
}

// ════════════════════════════════════════════
// TOAST
// ════════════════════════════════════════════
window.addEventListener('load', function () {
    var toast = document.getElementById('toast-msg');

    // Priority: URL param > toast data-section
    var section = '';
    var urlParams = new URLSearchParams(window.location.search);
    var urlSection = urlParams.get('section');
    var valid   = ['students','staff','parents','classes','subjects','assignments','timetable','exams','results','dashboard','salary-config','salary-sheet','salary-slips','hr-attendance','credentials','left-employees'];

    if (urlSection && valid.indexOf(urlSection) !== -1) {
        section = urlSection;
    } else if (toast) {
        var rawTags = (toast.dataset.section || '').trim();
        var parts   = rawTags.split(/\s+/);
        section = parts[parts.length - 1];
        if (valid.indexOf(section) === -1) section = 'dashboard';
    }

    if (section) {
        var navEl = document.querySelector('.nav-item[onclick*="\'' + section + '\'"]');
        if (navEl) showSection(section, navEl);
    }

    if (toast) {
        toast.style.display = 'flex';
        setTimeout(function () {
            toast.style.transition = 'opacity 0.35s ease';
            toast.style.opacity = '0';
            setTimeout(function () { toast.style.display = 'none'; }, 350);
        }, 2000);
    }
});

function showToast(msg) {
    var t = document.getElementById('toast-msg');
    if (!t) {
        t = document.createElement('div');
        t.id = 'toast-msg';
        t.style.cssText = [
            'position:fixed;bottom:28px;right:28px;z-index:9999;',
            'background:#1a1d23;color:#fff;padding:13px 20px;',
            'border-radius:12px;box-shadow:0 6px 28px rgba(0,0,0,0.25);',
            'font-size:13.5px;font-weight:600;',
            'display:flex;align-items:center;gap:10px;',
            'min-width:260px;max-width:380px;',
            'border-left:4px solid #0d9488;'
        ].join('');
        document.body.appendChild(t);
    }
    t.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0d9488" stroke-width="2.5">'
                + '<polyline points="20 6 9 17 4 12"/></svg> ' + msg;
    t.style.display  = 'flex';
    t.style.opacity  = '1';
    t.style.transition = '';
    clearTimeout(t._timer);
    t._timer = setTimeout(function () {
        t.style.transition = 'opacity 0.35s ease';
        t.style.opacity    = '0';
        setTimeout(function () { t.style.display = 'none'; }, 350);
    }, 2500);
}

// ════════════════════════════════════════════
// COLLAPSIBLE ROWS
// ════════════════════════════════════════════
function toggleStudents(id) {
    var el = document.getElementById(id);
    var ch = document.getElementById('chevron-' + id);
    var open = el.style.display === 'none';
    el.style.display   = open ? 'block' : 'none';
    ch.style.transform = open ? 'rotate(180deg)' : 'rotate(0deg)';
}

function toggleClassResults(id) {
    var el = document.getElementById(id);
    var ch = document.getElementById('chevron-' + id);
    var open = el.style.display === 'none';
    el.style.display   = open ? 'block' : 'none';
    ch.style.transform = open ? 'rotate(180deg)' : 'rotate(0deg)';
}

function toggleAttendance(id) {
    var el = document.getElementById(id);
    var ch = document.getElementById('chevron-' + id);
    var open = el.style.display === 'none';
    el.style.display   = open ? 'block' : 'none';
    ch.style.transform = open ? 'rotate(180deg)' : 'rotate(0deg)';
}

// ════════════════════════════════════════════
// EXAMS FILTER
// ════════════════════════════════════════════
var activeExamType = 'all';

function filterExams(btn) {
    if (btn && btn.dataset && btn.dataset.type) {
        activeExamType = btn.dataset.type;
        document.querySelectorAll('.exam-type-btn').forEach(function (b) {
            b.style.background = '#fff';
            b.style.color      = 'var(--text-secondary)';
        });
        btn.style.background = '#1a1d23';
        btn.style.color      = '#fff';
    }
    var teacherId = document.getElementById('exam-teacher-filter').value;
    var cards     = document.querySelectorAll('.exam-card');
    var visible   = 0;
    cards.forEach(function (card) {
        var ok = (activeExamType === 'all' || card.dataset.type === activeExamType)
              && (teacherId === 'all' || card.dataset.teacher === teacherId);
        card.style.display = ok ? '' : 'none';
        if (ok) visible++;
    });
    document.getElementById('no-exams-msg').style.display = visible === 0 ? 'block' : 'none';
}

// ════════════════════════════════════════════
// ATTENDANCE FILTER
// ════════════════════════════════════════════
function filterAttendance(clsId, status, btn) {
    var container = document.getElementById('att-' + clsId);
    container.querySelectorAll('.att-filter-btn').forEach(function (b) {
        b.style.background = '#fff';
        b.style.color      = 'var(--text-secondary)';
    });
    btn.style.background = '#1a1d23';
    btn.style.color      = '#fff';

    var rows    = document.querySelectorAll('.att-row-' + clsId);
    var visible = 0;
    rows.forEach(function (row) {
        var show = status === 'all' || row.dataset.status === status;
        row.style.display = show ? '' : 'none';
        if (show) visible++;
    });
    document.getElementById('att-empty-' + clsId).style.display = visible === 0 ? 'block' : 'none';
}

// ════════════════════════════════════════════
// STAFF DESIGNATION FILTER + SEARCH
// ════════════════════════════════════════════
var activeStaffDesignation = 'all';
var activeStaffSearch = '';

function filterStaff(designation, btn) {
    if (designation !== undefined) activeStaffDesignation = designation;
    document.querySelectorAll('.staff-filter-btn').forEach(function (b) {
        b.style.background = '#fff';
        b.style.color      = 'var(--text-secondary)';
    });
    if (btn) {
        btn.style.background = '#1a1d23';
        btn.style.color      = '#fff';
    }
    var q = activeStaffSearch.toLowerCase();
    var cards   = document.querySelectorAll('.staff-card');
    var visible = 0;
    cards.forEach(function (card) {
        var desig = card.dataset.designation || 'teacher';
        var text  = (card.dataset.search || card.textContent || '').toLowerCase();
        var showDesig = activeStaffDesignation === 'all' || desig === activeStaffDesignation;
        var showSearch = !q || text.indexOf(q) !== -1;
        var show = showDesig && showSearch;
        card.style.display = show ? '' : 'none';
        if (show) visible++;
    });
    var noResults = document.getElementById('staff-no-results');
    if (noResults) noResults.style.display = visible === 0 ? 'block' : 'none';
}

function searchStaff(query) {
    activeStaffSearch = query;
    filterStaff();
}

// ════════════════════════════════════════════
// AVATAR DROPDOWN
// ════════════════════════════════════════════
function closeAllDropdowns() {
    document.querySelectorAll('.avatar-dropdown').forEach(function (d) {
        d.classList.remove('show');
    });
}

document.addEventListener('DOMContentLoaded', function () {
    var topAvatarBtn      = document.getElementById('topAvatarBtn');
    var topAvatarDropdown = document.getElementById('topAvatarDropdown');

    if (topAvatarBtn && topAvatarDropdown) {
        topAvatarBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            topAvatarDropdown.classList.toggle('show');
        });
    }

    window.addEventListener('click', function (e) {
        if (topAvatarDropdown && !topAvatarDropdown.contains(e.target) && !topAvatarBtn.contains(e.target)) {
            topAvatarDropdown.classList.remove('show');
        }
    });
});

// ════════════════════════════════════════════
// TIMETABLE (tt2)
// ════════════════════════════════════════════
(function () {
    'use strict';

    /* ── state ── */
    var store      = {};
    var activeId   = '';
    var activeLabel= '';
    var activeDay  = 'Monday';
    var activeDays = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];

    /* ── helpers ── */
    function gv(id) { var e = document.getElementById(id); return e ? e.value : ''; }
    function gi(id) { return parseInt(gv(id)) || 0; }

    function minsToAmPm(m) {
        var h = Math.floor(m / 60), mn = m % 60;
        var ap = h >= 12 ? 'PM' : 'AM', h12 = h % 12 || 12;
        return h12 + ':' + (mn < 10 ? '0' : '') + mn + ' ' + ap;
    }

    function timeToMins(t) {
        if (!t) return 0;
        var p = t.split(':'); return parseInt(p[0]) * 60 + parseInt(p[1]);
    }

    /* ── FIX #2: proper AM/PM → 24-hour converter for Django TimeField ── */
    function ampmTo24(t) {
        var m = t.match(/(\d+):(\d+)\s*(AM|PM)/i);
        if (!m) return t;
        var h = parseInt(m[1]), mn = m[2], ap = m[3].toUpperCase();
        if (ap === 'PM' && h !== 12) h += 12;
        if (ap === 'AM' && h === 12) h = 0;
        return (h < 10 ? '0' : '') + h + ':' + mn;
    }

    /* ── build slot list ── */
    function buildSlots(customDurations) {
        var startM   = timeToMins(gv('tt2-start'));
        var nPeriods = gi('tt2-periods') || 8;
        var defSlot  = gi('tt2-slot') || 45;
        var brkAfter = gi('tt2-break-after');
        var brkDur   = gi('tt2-break-dur') || 0;

        var slots = [], cur = startM;

        for (var i = 0; i < nPeriods; i++) {
            var dur = (customDurations && customDurations[i]) ? customDurations[i] : defSlot;
            slots.push({
                isBreak: false, index: i,
                label: 'Period ' + (i + 1),
                start: cur, end: cur + dur, dur: dur,
                startStr: minsToAmPm(cur), endStr: minsToAmPm(cur + dur)
            });
            cur += dur;

            if (brkAfter > 0 && brkDur > 0 && (i + 1) === brkAfter) {
                slots.push({
                    isBreak: true, label: 'Break',
                    start: cur, end: cur + brkDur,
                    startStr: minsToAmPm(cur), endStr: minsToAmPm(cur + brkDur)
                });
                cur += brkDur;
            }
        }
        return slots;
    }

    /* ── subject colour ── */
    var cMap = {}, cIdx = 0;
    var COLS = ['tt2-c0','tt2-c1','tt2-c2','tt2-c3','tt2-c4','tt2-c5','tt2-c6','tt2-c7'];
    function colour(s) { if (!cMap[s]) cMap[s] = COLS[cIdx++ % COLS.length]; return cMap[s]; }

    /* ── subjects / teachers from DOM ── */
    function subjects() {
        if (window.SUBJECTS_DATA && window.SUBJECTS_DATA.length)
            return window.SUBJECTS_DATA.map(function (s) { return { name: s.name || s }; });
        var list = [];
        document.querySelectorAll('#section-subjects tbody tr td:first-child').forEach(function (td) {
            var v = td.textContent.trim(); if (v) list.push({ name: v });
        });
        return list;
    }

    function teachers() {
        var list = [];
        document.querySelectorAll('#tt2-vt-teacher option').forEach(function (o) {
            if (o.value) list.push({ name: o.value });
        });
        return list;
    }

    /* ── config rebuild ── */
    window.tt2Rebuild = function () { renderPeriods(); };
    window.tt2RebuildDays = function () {
        var v = gv('tt2-days');
        activeDays = v === 'mon-fri'
            ? ['Monday','Tuesday','Wednesday','Thursday','Friday']
            : ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
        populateDayDrops();
        buildDayBar();
        renderPeriods();
    };

    function populateDayDrops() {
        ['tt2-vc-day','tt2-vt-day'].forEach(function (id) {
            var el = document.getElementById(id); if (!el) return;
            var prev = el.value;
            el.innerHTML = '<option value="all">All Days</option>';
            activeDays.forEach(function (d) { el.innerHTML += '<option value="' + d + '">' + d + '</option>'; });
            if (prev) el.value = prev;
        });
    }

    /* ── tab switching ── */
    window.tt2Tab = function (tab, btn) {
        ['gen','class','teacher'].forEach(function (t) {
            var p = document.getElementById('tt2-panel-' + t);
            if (p) p.style.display = t === tab ? '' : 'none';
        });
        document.querySelectorAll('.tt2-tab').forEach(function (b) { b.classList.remove('active'); });
        if (btn) btn.classList.add('active');
        if (tab === 'class')   tt2RenderClass();
        if (tab === 'teacher') tt2RenderTeacher();
    };

    /* ── day bar ── */
    function buildDayBar() {
        var bar = document.getElementById('tt2-day-bar'); if (!bar) return;
        var html = '';
        activeDays.forEach(function (day) {
            var hasData = activeId && store[activeId] && dayHasData(activeId, day);
            var cls = 'tt2-day-btn' + (day === activeDay ? ' active' : '') + (hasData ? ' has-data' : '');
            html += '<button class="' + cls + '" onclick="tt2Day(\'' + day + '\',this)">' + day.substring(0, 3) + '</button>';
        });
        bar.innerHTML = html;
    }

    function dayHasData(cid, day) {
        if (!store[cid] || !store[cid][day]) return false;
        return Object.keys(store[cid][day]).some(function (k) {
            var e = store[cid][day][k]; return e && (e.s || e.t);
        });
    }

    window.tt2Day = function (day, btn) {
        activeDay = day;
        document.querySelectorAll('.tt2-day-btn').forEach(function (b) {
            b.classList.remove('active');
            var d = b.textContent.trim();
            var full = activeDays.find(function (x) { return x.substring(0, 3) === d; });
            if (full && activeId && dayHasData(activeId, full)) b.classList.add('has-data');
            else b.classList.remove('has-data');
        });
        if (btn) btn.classList.add('active');
        renderPeriods();
    };

    /* ── load class — FIX #1: properly closed, fetches from DB ── */
    window.tt2LoadClass = function () {
        var sel = document.getElementById('tt2-class-sel');
        activeId    = sel.value;
        activeLabel = sel.value
            ? (sel.options[sel.selectedIndex].dataset.label || sel.options[sel.selectedIndex].text)
            : '';

        if (!activeId) {
            document.getElementById('tt2-title').textContent    = 'Select a class to begin';
            document.getElementById('tt2-subtitle').textContent = 'Choose a class, then pick a day and assign subjects & teachers';
            renderPeriods();
            return;
        }

        if (!store[activeId]) store[activeId] = { __label: activeLabel, __slots: {} };
        else store[activeId].__label = activeLabel;

        document.getElementById('tt2-title').textContent    = activeLabel + ' — Generate Timetable';
        document.getElementById('tt2-subtitle').textContent = 'Loading saved timetable…';
        buildDayBar();

        /* fetch saved slots from DB */
        fetch('/timetable/load/?class_id=' + activeId, { credentials: 'same-origin' })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.status === 'ok' && data.slots.length) {
                    data.slots.forEach(function (s) {
                        if (!store[activeId][s.day]) store[activeId][s.day] = {};
                        store[activeId][s.day][s.period_number - 1] = {
                            s: s.subject_name,
                            t: s.teacher_name
                        };
                        /* restore custom durations */
                        if (!store[activeId].__slots[s.day]) store[activeId].__slots[s.day] = {};
                        store[activeId].__slots[s.day][s.period_number - 1] = s.duration;
                    });
                }
                document.getElementById('tt2-subtitle').textContent =
                    'Day: ' + activeDay + ' · Edit duration per period, then assign subject & teacher';
                buildDayBar();
                renderPeriods();
            })
            .catch(function () {
                document.getElementById('tt2-subtitle').textContent =
                    'Day: ' + activeDay + ' · (could not load saved data)';
                renderPeriods();
            });
    }; /* ← FIX #1: closing }; for tt2LoadClass */

    /* ── render period rows ── */
    function getCustomDurations() {
        if (!activeId || !store[activeId] || !store[activeId].__slots) return {};
        return store[activeId].__slots[activeDay] || {};
    }

    function renderPeriods() {
        var tbody = document.getElementById('tt2-tbody'); if (!tbody) return;
        if (!activeId) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:40px;color:var(--text-muted);font-size:13px;">Select a class above to begin.</td></tr>';
            return;
        }
        var custDur = getCustomDurations();
        var slots   = buildSlots(custDur);
        var dayData = (store[activeId] && store[activeId][activeDay]) || {};
        var subjs   = subjects();
        var tchrs   = teachers();

        var html = '';
        slots.forEach(function (slot) {
            if (slot.isBreak) {
                html += '<tr class="tt2-period-row tt2-break-row">'
                     + '<td colspan="4"><span class="tt2-break-badge">☕ Break &nbsp;' + slot.startStr + ' – ' + slot.endStr + '</span></td>'
                     + '<td colspan="3"></td></tr>';
                return;
            }
            var i = slot.index;
            var entry = dayData[i] || {};
            var sOpts = '<option value="">-- Subject --</option>';
            subjs.forEach(function (s) { sOpts += '<option value="' + s.name + '"' + (s.name === entry.s ? ' selected' : '') + '>' + s.name + '</option>'; });
            var tOpts = '<option value="">-- Teacher --</option>';
            tchrs.forEach(function (t) { tOpts += '<option value="' + t.name + '"' + (t.name === entry.t ? ' selected' : '') + '>' + t.name + '</option>'; });

            html += '<tr class="tt2-period-row">'
                 + '<td><div class="tt2-period-label">' + slot.label + '</div></td>'
                 + '<td><div class="tt2-period-time">' + slot.startStr + '</div></td>'
                 + '<td><input class="tt2-dur-input" type="number" value="' + slot.dur + '" min="10" max="120" step="5"'
                 + ' data-period="' + i + '" onchange="tt2SetDur(this)" title="Duration in minutes"></td>'
                 + '<td><div class="tt2-period-time">' + slot.endStr + '</div></td>'
                 + '<td><select class="tt2-sel' + (entry.s ? ' filled' : '') + '" data-period="' + i + '" data-field="s" onchange="tt2Entry(this)">' + sOpts + '</select></td>'
                 + '<td><select class="tt2-sel' + (entry.t ? ' filled' : '') + '" data-period="' + i + '" data-field="t" onchange="tt2Entry(this)">' + tOpts + '</select></td>'
                 + '<td><button onclick="tt2ClearPeriod(' + i + ')" title="Clear row" style="background:none;border:none;cursor:pointer;color:var(--text-muted);padding:4px;" onmouseover="this.style.color=\'#dc2626\'" onmouseout="this.style.color=\'var(--text-muted)\'"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button></td>'
                 + '</tr>';
        });
        tbody.innerHTML = html;
    }

    window.tt2SetDur = function (el) {
        var i = parseInt(el.dataset.period), val = parseInt(el.value) || 45;
        if (!store[activeId].__slots) store[activeId].__slots = {};
        if (!store[activeId].__slots[activeDay]) store[activeId].__slots[activeDay] = {};
        store[activeId].__slots[activeDay][i] = val;
        renderPeriods();
    };

    window.tt2Entry = function (el) {
        var i = parseInt(el.dataset.period), field = el.dataset.field, val = el.value;
        if (!store[activeId][activeDay]) store[activeId][activeDay] = {};
        if (!store[activeId][activeDay][i]) store[activeId][activeDay][i] = {};
        store[activeId][activeDay][i][field] = val;
        el.classList.toggle('filled', !!val);
        buildDayBar();
    };

    window.tt2ClearPeriod = function (i) {
        if (!activeId || !store[activeId] || !store[activeId][activeDay]) return;
        delete store[activeId][activeDay][i];
        renderPeriods();
    };

    /* ── save — FIX #2: ampmTo24, FIX #3: removed localStorage ── */
    window.tt2Save = function () {
        if (!activeId) { showToast('Please select a class first.'); return; }

        var classData = store[activeId];
        if (!classData) { showToast('No timetable data found.'); return; }

        /* check there's at least one filled period */
        var hasData = false;
        for (var day in classData) {
            if (day === '__label' || day === '__slots') continue;
            var periods = classData[day];
            if (typeof periods !== 'object') continue;
            for (var p in periods) {
                var period = periods[p];
                if (period && ((period.s && period.s.trim()) || (period.t && period.t.trim()))) {
                    hasData = true; break;
                }
            }
            if (hasData) break;
        }
        if (!hasData) { showToast('Please fill at least one period first.'); return; }

        /* build slots array for ALL days */
        var slots = [];
        activeDays.forEach(function (day) {
            var custDur  = (store[activeId].__slots && store[activeId].__slots[day]) || {};
            var daySlots = buildSlots(custDur);
            var dayData  = store[activeId][day] || {};
            daySlots.forEach(function (slot) {
                if (slot.isBreak) return;
                var e = dayData[slot.index] || {};
                if (!e.s) return; /* skip empty rows */
                slots.push({
                    day:           day,
                    period_number: slot.index + 1,
                    start_time:    ampmTo24(slot.startStr),   /* FIX #2 */
                    end_time:      ampmTo24(slot.endStr),     /* FIX #2 */
                    duration:      slot.dur,
                    subject_name:  e.s,
                    teacher_name:  e.t || ''
                });
            });
        });

        if (!slots.length) { showToast('Please fill at least one period.'); return; }

        var csrf = document.querySelector('[name=csrfmiddlewaretoken]');
        fetch('/timetable/save/', {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken':  csrf ? csrf.value : ''
            },
            body: JSON.stringify({ class_id: parseInt(activeId), slots: slots })
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.status === 'ok') {
                showToast('Timetable saved — ' + data.created + ' period(s) stored!');
                buildDayBar();
            } else {
                showToast('Save failed: ' + (data.message || 'Unknown error'));
            }
        })
        .catch(function () { showToast('Network error — timetable not saved.'); });
    };

    /* ── clear all — FIX #4: hits DB endpoint ── */
    window.tt2ClearAll = function () {
        if (!activeId || !confirm('Clear the entire timetable for ' + activeLabel + '?')) return;

        var csrf = document.querySelector('[name=csrfmiddlewaretoken]');
        fetch('/timetable/clear/', {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken':  csrf ? csrf.value : ''
            },
            body: JSON.stringify({ class_id: parseInt(activeId) })
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.status === 'ok') {
                store[activeId] = { __label: activeLabel, __slots: {} };
                renderPeriods();
                buildDayBar();
                showToast('Cleared ' + data.deleted + ' slot(s) from database.');
            } else {
                showToast('Clear failed: ' + (data.message || 'error'));
            }
        })
        .catch(function () { showToast('Network error — could not clear.'); });
    };

    /* ── class view ── */
    /* ── class view ── */
    window.tt2RenderClass = function () {
        var cid  = gv('tt2-vc-class'), dayF = gv('tt2-vc-day') || 'all';
        var out  = document.getElementById('tt2-cv-out');
        if (!cid) {
            out.innerHTML = '<div style="text-align:center;color:var(--text-muted);font-size:13px;padding:40px;">Select a class to view its timetable.</div>';
            return;
        }
        if (!store[cid]) {
            out.innerHTML = '<div style="text-align:center;color:var(--text-muted);font-size:13px;padding:40px;">⏳ Loading…</div>';
            var sel = document.getElementById('tt2-vc-class');
            var lbl = sel ? (sel.options[sel.selectedIndex].dataset.label || sel.options[sel.selectedIndex].text) : cid;
            store[cid] = { __label: lbl, __slots: {} };
            fetch('/timetable/load/?class_id=' + cid, { credentials: 'same-origin' })
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    if (data.status === 'ok') {
                        data.slots.forEach(function(s) {
                            if (!store[cid][s.day]) store[cid][s.day] = {};
                            store[cid][s.day][s.period_number - 1] = { s: s.subject_name, t: s.teacher_name };
                            if (!store[cid].__slots[s.day]) store[cid].__slots[s.day] = {};
                            store[cid].__slots[s.day][s.period_number - 1] = s.duration;
                        });
                    }
                    tt2RenderClass();
                })
                .catch(function() { out.innerHTML = '<div style="text-align:center;color:#dc2626;font-size:13px;padding:40px;">Could not load timetable.</div>'; });
            return;
        }
        var clabel = store[cid].__label || cid;
        var days   = dayF === 'all' ? activeDays : [dayF];

        var allSlots = [];
        days.forEach(function (day) {
            var cDur = store[cid].__slots && store[cid].__slots[day] ? store[cid].__slots[day] : {};
            buildSlots(cDur).forEach(function (s) {
                if (!s.isBreak && !allSlots.find(function (x) { return x.label === s.label; })) allSlots.push(s);
                if (s.isBreak  && !allSlots.find(function (x) { return x.isBreak; }))          allSlots.push(s);
            });
        });

        var html = '<table class="tt2-preview-table" id="tt2-cv-table"><thead><tr>'
                 + '<th style="text-align:left;min-width:120px;">Period</th>';
        days.forEach(function (d) { html += '<th>' + d.substring(0, 3) + '</th>'; });
        html += '</tr></thead><tbody>';

        allSlots.forEach(function (slot) {
            if (slot.isBreak) {
                html += '<tr class="tt2-brk"><td>☕ Break</td>';
                days.forEach(function (day) {
                    var cDur     = store[cid].__slots && store[cid].__slots[day] ? store[cid].__slots[day] : {};
                    var daySlots = buildSlots(cDur);
                    var brk      = daySlots.find(function (s) { return s.isBreak; });
                    html += '<td>' + (brk ? brk.startStr + ' – ' + brk.endStr : '—') + '</td>';
                });
                html += '</tr>'; return;
            }
            html += '<tr><td><strong>' + slot.label + '</strong><br><span style="font-size:10px;color:var(--text-muted);">' + slot.startStr + ' – ' + slot.endStr + '</span></td>';
            days.forEach(function (day) {
                var cDur  = store[cid].__slots && store[cid].__slots[day] ? store[cid].__slots[day] : {};
                var ds    = buildSlots(cDur);
                var match = ds.find(function (s) { return !s.isBreak && s.label === slot.label; });
                var i     = match ? match.index : slot.index;
                var e     = (store[cid][day] && store[cid][day][i]) || {};
                if (e.s) {
                    var cc = colour(e.s);
                    html += '<td><div class="tt2-pill ' + cc + '"><span class="ps">' + e.s + '</span><span class="pt">' + (e.t || '') + '</span></div></td>';
                } else { html += '<td style="color:var(--text-muted);">—</td>'; }
            });
            html += '</tr>';
        });
        html += '</tbody></table>';
        out.innerHTML = html;
    };

    /* ── teacher view ── */
    window.tt2RenderTeacher = function () {
        var tname = gv('tt2-vt-teacher'), dayF = gv('tt2-vt-day') || 'all';
        var out   = document.getElementById('tt2-tv-out');
        if (!tname) { out.innerHTML = '<div style="text-align:center;color:var(--text-muted);font-size:13px;padding:40px;">Select a teacher.</div>'; return; }
        var days = dayF === 'all' ? activeDays : [dayF];

        var tchrSched = {};
        Object.keys(store).forEach(function (cid) {
            var cl = store[cid].__label || cid;
            activeDays.forEach(function (day) {
                if (!store[cid][day]) return;
                Object.keys(store[cid][day]).forEach(function (k) {
                    var e = store[cid][day][k];
                    if (e && e.t === tname) {
                        if (!tchrSched[day]) tchrSched[day] = {};
                        tchrSched[day][k] = { cl: cl, s: e.s };
                    }
                });
            });
        });

var hasAny = Object.keys(tchrSched).length > 0;
        if (!hasAny) {
            // No data in store — fetch all classes from DB then retry
            var opts = document.querySelectorAll('#tt2-vc-class option[value]');
            var toLoad = [];
            opts.forEach(function(o) { if (o.value && !store[o.value]) toLoad.push(o); });
            if (toLoad.length > 0) {
                out.innerHTML = '<div style="text-align:center;color:var(--text-muted);font-size:13px;padding:40px;">⏳ Loading…</div>';
                var done = 0;
                toLoad.forEach(function(o) {
                    var cid = o.value;
                    store[cid] = { __label: o.dataset.label || o.text, __slots: {} };
                    fetch('/timetable/load/?class_id=' + cid, { credentials: 'same-origin' })
                        .then(function(r) { return r.json(); })
                        .then(function(data) {
                            if (data.status === 'ok') {
                                data.slots.forEach(function(s) {
                                    if (!store[cid][s.day]) store[cid][s.day] = {};
                                    store[cid][s.day][s.period_number - 1] = { s: s.subject_name, t: s.teacher_name };
                                    if (!store[cid].__slots[s.day]) store[cid].__slots[s.day] = {};
                                    store[cid].__slots[s.day][s.period_number - 1] = s.duration;
                                });
                            }
                        })
                        .catch(function(){})
                        .finally(function() {
                            done++;
                            if (done === toLoad.length) tt2RenderTeacher();
                        });
                });
                return;
            }
            out.innerHTML = '<div style="text-align:center;color:var(--text-muted);font-size:13px;padding:40px;">No periods assigned to this teacher yet.</div>';
            return;
        }
        var allSlots = [];
        days.forEach(function (day) {
            buildSlots({}).forEach(function (s) {
                if (!s.isBreak && !allSlots.find(function (x) { return x.label === s.label; })) allSlots.push(s);
            });
        });

        var html = '<table class="tt2-preview-table" id="tt2-tv-table"><thead><tr><th style="text-align:left;">Period</th>';
        days.forEach(function (d) { html += '<th>' + d.substring(0, 3) + '</th>'; });
        html += '</tr></thead><tbody>';

        allSlots.forEach(function (slot) {
            html += '<tr><td><strong>' + slot.label + '</strong><br><span style="font-size:10px;color:var(--text-muted);">' + slot.startStr + '</span></td>';
            days.forEach(function (day) {
                var e = tchrSched[day] && tchrSched[day][slot.index];
                if (e) {
                    var cc = colour(e.s);
                    html += '<td><div class="tt2-pill ' + cc + '"><span class="ps">' + e.s + '</span><span class="pt">' + e.cl + '</span></div></td>';
                } else { html += '<td style="color:var(--text-muted);">—</td>'; }
            });
            html += '</tr>';
        });
        html += '</tbody></table>';
        out.innerHTML = html;
    };

    /* ── PDF export ── */
    window.tt2PDF = function (tableId, title) {
        if (typeof html2canvas === 'undefined' || typeof window.jspdf === 'undefined') {
            alert('PDF libraries not loaded.');
            return;
        }
        var tbl = document.getElementById(tableId);
        if (!tbl) { alert('No timetable to export yet.'); return; }
        // Build descriptive title from current selections
var classEl   = document.getElementById('tt2-vc-class');
var teacherEl = document.getElementById('tt2-vt-teacher');
if (tableId === 'tt2-cv-table' && classEl && classEl.value) {
    title = classEl.options[classEl.selectedIndex].text + ' — Timetable';
}
if (tableId === 'tt2-tv-table' && teacherEl && teacherEl.value) {
    title = teacherEl.value + ' — Schedule';
}

        var wrap = document.createElement('div');
        wrap.style.cssText = 'position:absolute;left:-9999px;top:0;font-family:Plus Jakarta Sans,Arial,sans-serif;background:#fff;padding:32px 36px;width:1120px;';

        var hdr = document.createElement('div');
        hdr.style.cssText = 'display:flex;align-items:center;justify-content:space-between;padding-bottom:14px;margin-bottom:18px;border-bottom:3px solid #0d9488;';
       hdr.innerHTML = '<div>'
    + '<div style="font-size:22px;font-weight:800;color:#0f1623;letter-spacing:-.3px;">Institution Management</div>'
    + '<div style="font-size:12px;color:#9ca3af;margin-top:3px;font-weight:500;">School Management System</div>'
    + '</div>'
            + '<div style="text-align:right;">'
            + '<div style="font-size:15px;font-weight:700;color:#1a1d23;">' + title + '</div>'
            + '<div style="font-size:11px;color:#9ca3af;margin-top:4px;">Generated: ' + new Date().toLocaleDateString('en-PK', { day: '2-digit', month: 'long', year: 'numeric' }) + '</div>'
            + '</div>';
        wrap.appendChild(hdr);

        var t = tbl.cloneNode(true);
        t.style.cssText = 'width:100%;border-collapse:collapse;border-radius:0;';
        t.querySelectorAll('thead th').forEach(function (th, ci) {
            th.style.cssText = 'background:#0f1623;color:#fff;padding:10px 12px;font-size:10.5px;font-weight:700;'
                + 'text-transform:uppercase;letter-spacing:.5px;text-align:' + (ci === 0 ? 'left' : 'center') + ';border:1px solid #0f1623;white-space:nowrap;';
        });
        t.querySelectorAll('tbody tr').forEach(function (row, ri) {
            var isBreak = row.className.indexOf('brk') !== -1 || row.className.indexOf('break') !== -1;
            row.querySelectorAll('td').forEach(function (td, ci) {
                td.style.cssText = isBreak
                    ? 'background:#fffbeb;color:#d97706;font-weight:700;font-size:11.5px;padding:9px 12px;border:1px solid #fde68a;text-align:' + (ci === 0 ? 'left' : 'center') + ';'
                    : 'padding:9px 12px;border:1px solid #e5e7eb;vertical-align:middle;text-align:' + (ci === 0 ? 'left' : 'center') + ';background:' + (ri % 2 === 0 ? '#fff' : '#f8fafc') + ';font-size:12px;';
                var pill = td.querySelector('.tt2-pill');
                if (pill) {
                    var subj    = pill.querySelector('.ps') ? pill.querySelector('.ps').textContent : '';
                    var teacher = pill.querySelector('.pt') ? pill.querySelector('.pt').textContent : '';
                    td.innerHTML = '<div style="font-weight:700;font-size:12px;color:#111;">' + subj + '</div>'
                                 + '<div style="font-size:10px;color:#555;margin-top:2px;">' + teacher + '</div>';
                }
            });
        });
        wrap.appendChild(t);

        var foot = document.createElement('div');
        foot.style.cssText = 'margin-top:16px;padding-top:12px;border-top:1px solid #e5e7eb;display:flex;justify-content:space-between;font-size:10px;color:#9ca3af;';
foot.innerHTML = '<span>School Management System</span><span>Confidential · For Internal Use Only</span>';        wrap.appendChild(foot);

        document.body.appendChild(wrap);

        html2canvas(wrap, { scale: 2, useCORS: true, backgroundColor: '#ffffff', logging: false }).then(function (canvas) {
            document.body.removeChild(wrap);
            var jsPDF = window.jspdf.jsPDF;
            var pdf   = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a4' });
            var pw    = pdf.internal.pageSize.getWidth(), ph = pdf.internal.pageSize.getHeight();
            var r     = Math.min((pw - 10) / (canvas.width / 3.7795), (ph - 10) / (canvas.height / 3.7795));
            var fw    = (canvas.width  / 3.7795) * r, fh = (canvas.height / 3.7795) * r;
            pdf.addImage(canvas.toDataURL('image/png'), 'PNG', (pw - fw) / 2, (ph - fh) / 2, fw, fh);
var fname = (title).replace(/[^a-zA-Z0-9 _-]/g, '').replace(/\s+/g, '_') + '.pdf';            pdf.save(fname);
            showToast('PDF downloaded successfully!');
        }).catch(function (err) {
            document.body.removeChild(wrap);
            console.error(err);
            showToast('PDF export failed. Try again.');
        });
    };

    /* ── init — FIX #4: removed localStorage, DB is source of truth ── */
    function init() {
        buildDayBar();
        populateDayDrops();
    }

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
    else init();

})();


// ════════════════════════════════════════════
// DRAWER SYSTEM
// ════════════════════════════════════════════
(function () {
    'use strict';

    var TITLE_MAP = [
        { key: '/add/student',     label: 'Add Student'     },
        { key: '/edit/student',    label: 'Edit Student'    },
        { key: '/add/teacher',     label: 'Add Staff'        },
        { key: '/edit/teacher',    label: 'Edit Staff'       },
        { key: '/add/parent',      label: 'Add Parent'      },
        { key: '/edit/parent',     label: 'Edit Parent'     },
        { key: '/add/class',       label: 'Add Class'       },
        { key: '/edit/class',      label: 'Edit Class'      },
        { key: '/add/subject',     label: 'Add Subject'     },
        { key: '/edit/subject',    label: 'Edit Subject'    },
        { key: '/add/assignment',  label: 'Assign Teacher'  },
        { key: '/edit/assignment', label: 'Edit Assignment' },
        { key: '/separation',      label: 'Mark as Left'    },
        { key: '/clearance',       label: 'Clearance'       },
        { key: '/edit/separation', label: 'Edit Separation' },
        { key: 'add_student',      label: 'Add Student'     },
        { key: 'edit_student',     label: 'Edit Student'    },
        { key: 'add_teacher',      label: 'Add Staff'        },
        { key: 'edit_teacher',     label: 'Edit Staff'       },
        { key: 'add_parent',       label: 'Add Parent'      },
        { key: 'edit_parent',      label: 'Edit Parent'     },
        { key: 'add_class',        label: 'Add Class'       },
        { key: 'edit_class',       label: 'Edit Class'      },
        { key: 'add_subject',      label: 'Add Subject'     },
        { key: 'edit_subject',     label: 'Edit Subject'    },
        { key: 'add_assignment',   label: 'Assign Teacher'  },
        { key: 'edit_assignment',  label: 'Edit Assignment' },
        { key: 'separation',       label: 'Mark as Left'    },
        { key: 'clearance',        label: 'Clearance'       },
    ];

    var OPEN_IN_DRAWER = [
        '/add/student', '/edit/student',
        '/add/teacher', '/edit/teacher',
        '/add/parent',  '/edit/parent',
        '/add/class',   '/edit/class',
        '/add/subject', '/edit/subject',
        '/add/assignment', '/edit/assignment', '/separation', '/clearance', '/edit/separation',
        'add_student',  'edit_student',
        'add_teacher',  'edit_teacher',
        'add_parent',   'edit_parent',
        'add_class',    'edit_class',
        'add_subject',  'edit_subject',
        'add_assignment', 'edit_assignment', 'separation', 'clearance', 'edit/separation',
    ];

    function getTitle(url) {
        for (var i = 0; i < TITLE_MAP.length; i++) {
            if (url.indexOf(TITLE_MAP[i].key) !== -1) return TITLE_MAP[i].label;
        }
        return 'Form';
    }

    function isDrawerUrl(url) {
        if (!url || url === '#' || url.indexOf('javascript') === 0) return false;
        for (var i = 0; i < OPEN_IN_DRAWER.length; i++) {
            if (url.indexOf(OPEN_IN_DRAWER[i]) !== -1) return true;
        }
        return false;
    }

    function attachMaritalStatusToggle(root) {
        var statusField = root.querySelector('[name="marital_status"]');
        var husbandInfo = root.querySelector('#husband-info');
        var kidsSection = root.querySelector('#kids-section');
        if (!statusField) return;
        function toggleFields() {
            var v = statusField.value;
            if (husbandInfo) husbandInfo.style.display = v === 'married' ? '' : 'none';
            if (kidsSection) kidsSection.style.display = v !== 'single' ? '' : 'none';
        }
        toggleFields();
        statusField.addEventListener('change', toggleFields);
    }

    function attachKidsHandler(root) {
        var kidsList = root.querySelector('#kids-list');
        var kidsJson = root.querySelector('#kids_json');
        var addKidBtn = root.querySelector('#add-kid-btn');
        if (!kidsList || !kidsJson) return;
        var kids = [];
        try { kids = JSON.parse(kidsJson.value || '[]'); } catch(e) { kids = []; }

        function renderKids() {
            kidsList.innerHTML = '';
            kids.forEach(function(kid, i) {
                var row = document.createElement('div');
                row.style.cssText = 'display:flex;gap:10px;align-items:flex-end;margin-bottom:10px;flex-wrap:wrap;';
                row.innerHTML =
                    '<div class="form-group" style="flex:1;min-width:150px;margin-bottom:0;"><label>Child Name</label><input type="text" data-kid="'+i+'" data-field="name" value="'+(kid.name||'')+'" style="width:100%;padding:8px 10px;border:1.5px solid #e5e7eb;border-radius:8px;font-size:13px;box-sizing:border-box;"></div>' +
                    '<div class="form-group" style="flex:0 0 140px;min-width:0;margin-bottom:0;"><label>Date of Birth</label><input type="date" data-kid="'+i+'" data-field="dob" value="'+(kid.dob||'')+'" style="width:100%;padding:8px 10px;border:1.5px solid #e5e7eb;border-radius:8px;font-size:13px;box-sizing:border-box;"></div>' +
                    '<div class="form-group" style="flex:0 0 100px;min-width:0;margin-bottom:0;"><label>Gender</label><select data-kid="'+i+'" data-field="gender" style="width:100%;padding:8px 10px;border:1.5px solid #e5e7eb;border-radius:8px;font-size:13px;box-sizing:border-box;"><option value="M"'+(kid.gender==='M'?' selected':'')+'>Boy</option><option value="F"'+(kid.gender==='F'?' selected':'')+'>Girl</option></select></div>' +
                    '<div class="form-group" style="flex:0 0 110px;min-width:0;margin-bottom:0;"><label>Relationship</label><select data-kid="'+i+'" data-field="relationship" style="width:100%;padding:8px 10px;border:1.5px solid #e5e7eb;border-radius:8px;font-size:13px;box-sizing:border-box;"><option value="son"'+(kid.relationship==='son'?' selected':'')+'>Son</option><option value="daughter"'+(kid.relationship==='daughter'?' selected':'')+'>Daughter</option></select></div>' +
                    '<div class="form-group" style="flex:0 0 130px;min-width:0;margin-bottom:0;"><label>B-Form/CRC No.</label><input type="text" data-kid="'+i+'" data-field="bform" value="'+(kid.bform||'')+'" style="width:100%;padding:8px 10px;border:1.5px solid #e5e7eb;border-radius:8px;font-size:13px;box-sizing:border-box;"></div>' +
                    '<div class="form-group" style="flex:0 0 140px;min-width:0;margin-bottom:0;"><label>School/College</label><input type="text" data-kid="'+i+'" data-field="school" value="'+(kid.school||'')+'" style="width:100%;padding:8px 10px;border:1.5px solid #e5e7eb;border-radius:8px;font-size:13px;box-sizing:border-box;"></div>' +
                    '<div class="form-group" style="flex:0 0 110px;min-width:0;margin-bottom:0;"><label>Class/Grade</label><input type="text" data-kid="'+i+'" data-field="class_grade" value="'+(kid.class_grade||'')+'" style="width:100%;padding:8px 10px;border:1.5px solid #e5e7eb;border-radius:8px;font-size:13px;box-sizing:border-box;"></div>' +
                    '<button type="button" class="remove-kid" data-idx="'+i+'" style="padding:8px 12px;background:#fef2f2;color:#dc2626;border:1px solid #fecaca;border-radius:8px;cursor:pointer;font-size:13px;flex-shrink:0;">\u2715</button>';
                kidsList.appendChild(row);
            });
            kidsJson.value = JSON.stringify(kids);
        }

        kidsList.addEventListener('input', function(e) {
            var el = e.target;
            var i = parseInt(el.dataset.kid);
            var f = el.dataset.field;
            if (!isNaN(i) && f) { kids[i][f] = el.value; kidsJson.value = JSON.stringify(kids); }
        });
        kidsList.addEventListener('click', function(e) {
            var btn = e.target.closest('.remove-kid');
            if (!btn) return;
            kids.splice(parseInt(btn.dataset.idx), 1);
            renderKids();
        });
        if (addKidBtn) addKidBtn.addEventListener('click', function() {
            kids.push({name:'', dob:'', gender:'M', relationship:'son', bform:'', school:'', class_grade:''});
            renderKids();
        });
        renderKids();
    }

    function attachSidebarScrollspy(root) {
        if (!document.getElementById('drawer-mobile-css')) {
            var s = document.createElement('style');
            s.id = 'drawer-mobile-css';
            s.textContent = '@media(max-width:700px){#drawer-body .upload-form{flex-direction:column !important;}#drawer-body .upload-form .form-group{max-width:100% !important;flex:1 1 100% !important;}#drawer-body .form-row{grid-template-columns:1fr !important;}#drawer-body .doc-row{flex-direction:column !important;align-items:stretch !important;}#drawer-body .doc-row .form-group{min-width:0;flex:1 1 100% !important;}#drawer-body .doc-item{flex-direction:column;align-items:flex-start;gap:10px;}#drawer-body .doc-actions{width:100%;}#drawer-body .doc-actions .btn{flex:1;text-align:center;}}';
            document.head.appendChild(s);
        }

        var sidebar = root.querySelector('.form-sidebar');
        var main = root.querySelector('.form-main') || root;
        if (!sidebar) return;

        if (!document.getElementById('staff-form-sidebar-css')) {
            var style = document.createElement('style');
            style.id = 'staff-form-sidebar-css';
            style.textContent = '' +
                '#drawer > div:first-child{position:relative;z-index:20;}' +
                '#drawer-body .form-sidebar{width:180px;background:#0f2744;padding:16px 0;flex-shrink:0;position:absolute;left:0;top:60px;bottom:0;z-index:10;border-radius:0 0 0 16px;}' +
                '#drawer-body .form-sidebar a{display:flex;align-items:center;padding:10px 20px;font-size:13px;font-weight:600;color:rgba(255,255,255,0.5);text-decoration:none;transition:all .15s;border-left:3px solid transparent;}' +
                '#drawer-body .form-sidebar a:hover{color:rgba(255,255,255,0.85);background:rgba(255,255,255,0.06);}' +
                '#drawer-body .form-sidebar a.active{color:#fff;background:rgba(20,184,166,0.15);border-left-color:#14b8a6;}' +
                '#drawer-body .form-main{margin-left:180px;padding:0;min-width:0;overflow-y:auto;max-height:70vh;}' +
                '#drawer-body .form-section{scroll-margin-top:10px;padding:20px 24px;}' +
                '#drawer-body .form-section+.form-section{border-top:1px solid #f3f4f6;}' +
                '#drawer-body .form-footer{padding:14px 24px;border-top:1px solid #f3f4f6;display:flex;gap:10px;justify-content:flex-end;}' +
                '#drawer-body .btn-save{padding:10px 28px;background:#0d9488;color:#fff;border:none;border-radius:8px;cursor:pointer;font-weight:600;font-size:13px;font-family:inherit;}' +
                '#drawer-body .btn-save:hover{background:#0f766e;}' +
                '#drawer-body .btn-cancel{padding:10px 20px;background:#fff;color:#6b7280;border:1.5px solid #e5e7eb;border-radius:8px;cursor:pointer;font-weight:600;font-size:13px;font-family:inherit;}' +
                '#drawer-body .btn-cancel:hover{background:#f9fafb;color:#374151;}' +
                '#drawer-body .husband-section .section-title{color:#9333ea;border-bottom-color:#faf5ff;}' +
                '#drawer-body .kids-section .section-title{color:#9333ea;border-bottom-color:#faf5ff;}' +
                '#drawer-body .section-title{font-size:13px;font-weight:700;color:#0d9488;text-transform:uppercase;letter-spacing:.5px;margin:0 0 14px;padding-bottom:6px;border-bottom:2px solid #f0fdfa;}' +
                '@media(max-width:700px){#drawer-body .form-sidebar{width:100%;border-right:none;border-bottom:1px solid rgba(255,255,255,0.1);display:flex;overflow-x:auto;padding:0;position:static;border-radius:0;}.form-sidebar a{border-left:none;border-bottom:3px solid transparent;white-space:nowrap;padding:12px 16px;}.form-sidebar a.active{border-bottom-color:#14b8a6;border-left-color:transparent;}#drawer-body .form-main{margin-left:0;}}';
            document.head.appendChild(style);
        }
        var links = sidebar.querySelectorAll('a[data-section]');
        if (!links.length) return;

        links.forEach(function(link) {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                var id = this.getAttribute('data-section');
                var sec = root.querySelector('#' + id);
                if (sec) sec.scrollIntoView({behavior:'smooth', block:'start'});
            });
        });

        var sections = [];
        links.forEach(function(link) {
            var id = link.getAttribute('data-section');
            var sec = root.querySelector('#' + id);
            if (sec) sections.push({el:sec, link:link});
        });

        function onScroll() {
            var scrollTop = main.scrollTop;
            var active = sections[0];
            for (var i = 0; i < sections.length; i++) {
                if (sections[i].el.offsetTop - main.offsetTop <= scrollTop + 60) {
                    active = sections[i];
                }
            }
            links.forEach(function(l) { l.classList.remove('active'); });
            if (active) active.link.classList.add('active');
        }

        main.addEventListener('scroll', onScroll);
        onScroll();
    }

    window.openDrawer = function (url, title) {
        var overlay = document.getElementById('drawer-overlay');
        var drawer  = document.getElementById('drawer');
        var body    = document.getElementById('drawer-body');
        var titleEl = document.getElementById('drawer-title');

        if (!overlay || !drawer || !body) {
            window.location.href = url;
            return;
        }

        titleEl.textContent = title || getTitle(url);
        body.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:200px;flex-direction:column;gap:12px;">'
            + '<div style="width:36px;height:36px;border:3px solid #e5e7eb;border-top-color:#0d9488;border-radius:50%;animation:spin 0.7s linear infinite;"></div>'
            + '<span style="font-size:13px;color:#9ca3af;">Loading…</span></div>';

        overlay.style.display    = 'block';
        drawer.style.visibility  = 'visible';
        drawer.style.opacity     = '1';
        drawer.style.transform   = 'translate(-50%, -50%) scale(1)';
        document.body.style.overflow = 'hidden';

        fetch(url, { credentials: 'same-origin' })
            .then(function (res) { return res.text(); })
            .then(function (html) {
                var parser = new DOMParser();
                var doc    = parser.parseFromString(html, 'text/html');

                var container = doc.querySelector('.container') || doc.querySelector('.form-container') || doc.querySelector('.hr-main') || doc.querySelector('.content') || doc.querySelector('main');
                if (container) {
                    var backLinks = container.querySelectorAll('a[href*="admin_console"], a[href*="left-employees"]');
                    backLinks.forEach(function(l) {
                        if (l.textContent && l.textContent.indexOf('Back to') !== -1) {
                            if (l.parentElement && l.parentElement.children.length === 1) {
                                l.parentElement.remove();
                            } else {
                                l.remove();
                            }
                        }
                    });
                    body.innerHTML = container.innerHTML;
                } else {
                    var form = doc.querySelector('form');
                    if (form) {
                        body.innerHTML = form.outerHTML;
                    } else {
                        body.innerHTML = '<p style="color:#dc2626;padding:20px;">Could not load content.</p>';
                    }
                }
                attachFormHandler(body, url);
                attachDeleteHandlers(body, url);
                attachAddMoreHandler(body);
                attachMaritalStatusToggle(body);
                attachKidsHandler(body);
                attachSidebarScrollspy(body);
            })
            .catch(function () {
                body.innerHTML = '<div style="text-align:center;padding:40px;">'
                    + '<p style="color:#dc2626;font-size:13px;margin-bottom:12px;">Failed to load form.</p>'
                    + '<a href="' + url + '" class="btn btn-blue">Open Full Page Instead</a></div>';
            });
    };

    window.closeDrawer = function () {
        var drawer  = document.getElementById('drawer');
        var overlay = document.getElementById('drawer-overlay');
        if (drawer) {
            drawer.style.opacity    = '0';
            drawer.style.visibility = 'hidden';
            drawer.style.transform  = 'translate(-50%, -45%) scale(0.95)';
        }
        if (overlay) overlay.style.display = 'none';
        document.body.style.overflow = '';
    };

    window.generateClearancePDF = function (data) {
        if (!window.jspdf) return;
        var jsPDF = window.jspdf.jsPDF;
        var doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
        var pw = doc.internal.pageSize.getWidth();
        var y = 0;

        // Header
        doc.setFillColor(13, 148, 136);
        doc.rect(0, 0, pw, 32, 'F');
        doc.setTextColor(255, 255, 255);
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(15);
        doc.text('Employee Clearance Certificate', pw / 2, 13, { align: 'center' });
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(9);
        doc.text('Generated: ' + new Date().toLocaleDateString(), pw / 2, 22, { align: 'center' });

        y = 42;

        // Employee Info
        doc.setFillColor(249, 250, 251);
        doc.rect(10, y - 5, pw - 20, 30, 'F');
        doc.setTextColor(26, 29, 35);
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(10);
        doc.text('Employee: ' + data.name, 15, y + 3);
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(9);
        doc.setTextColor(100, 100, 100);
        doc.text('ID: ' + (data.employeeId || 'N/A'), 15, y + 10);
        doc.text('Designation: ' + (data.designation || 'N/A'), 15, y + 16);
        doc.text('Last Working Date: ' + data.lastWorkingDate, 15, y + 22);
        y += 35;

        // Accumulated Deductions
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(11);
        doc.setTextColor(26, 29, 35);
        doc.text('Accumulated Deductions', 15, y);
        y += 3;

        doc.setDrawColor(13, 148, 136);
        doc.setLineWidth(0.5);
        doc.line(15, y, pw - 15, y);
        y += 7;

        doc.setFont('helvetica', 'normal');
        doc.setFontSize(9);
        var deductions = [
            ['Provident Fund', data.totalPf],
            ['Security', data.totalSecurity],
            ['Tax', data.totalTax],
            ['Van/Child Deductions', data.totalVanChild],
            ['Other Deductions', data.totalOther],
            ['Grand Total Deductions', data.totalDeductions]
        ];
        deductions.forEach(function (d) {
            doc.setTextColor(80, 80, 80);
            doc.text(d[0], 20, y);
            doc.setTextColor(26, 29, 35);
            doc.text('PKR ' + Number(d[1]).toLocaleString(), pw - 20, y, { align: 'right' });
            y += 6;
        });

        y += 5;

        // Exit Clearance
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(11);
        doc.setTextColor(26, 29, 35);
        doc.text('Exit Clearance', 15, y);
        y += 3;

        doc.setDrawColor(13, 148, 136);
        doc.setLineWidth(0.5);
        doc.line(15, y, pw - 15, y);
        y += 7;

        doc.setFont('helvetica', 'normal');
        doc.setFontSize(9);
        var exitItems = [
            ['Security Deposit Deduction', data.securityDeduction],
            ['Last Salary Withheld', data.lastSalaryWithheld],
            ['Last Salary Amount', data.lastSalaryAmount],
            ['Additional Deductions', data.additionalDeductions],
            ['Clearance Date', data.clearanceDate]
        ];
        exitItems.forEach(function (item) {
            doc.setTextColor(80, 80, 80);
            doc.text(item[0], 20, y);
            doc.setTextColor(26, 29, 35);
            var val = item[1];
            if (typeof val === 'number') val = 'PKR ' + val.toLocaleString();
            doc.text(String(val || 'N/A'), pw - 20, y, { align: 'right' });
            y += 6;
        });

        y += 5;

        // Total Exit Deductions
        doc.setFillColor(254, 226, 226);
        doc.rect(10, y - 5, pw - 20, 12, 'F');
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(10);
        doc.setTextColor(220, 38, 38);
        doc.text('Total Exit Deductions:', 20, y + 2);
        doc.text('PKR ' + Number(data.totalExitDeductions).toLocaleString(), pw - 20, y + 2, { align: 'right' });
        y += 18;

        // Status
        doc.setFillColor(240, 253, 244);
        doc.rect(10, y - 5, pw - 20, 12, 'F');
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(10);
        doc.setTextColor(22, 163, 74);
        doc.text('Clearance Status: COMPLETED', pw / 2, y + 2, { align: 'center' });

        var safeName = (data.name || 'employee').replace(/[^a-zA-Z0-9]/g, '_');
        doc.save('clearance_' + safeName + '_' + new Date().toISOString().slice(0, 10) + '.pdf');
    };

    function attachFormHandler(container, originalUrl) {
        container.querySelectorAll('form').forEach(function (f) {
            var action = f.getAttribute('action');
            if (!action || action === '') f.setAttribute('action', originalUrl);

            f.addEventListener('submit', function (e) {
                e.preventDefault();

                var btn = f.querySelector('[type=submit], button[type=submit]');
                var originalText = btn ? (btn.value || btn.textContent) : 'Save';
                if (btn) { btn.disabled = true; btn.textContent = 'Uploading…'; }

                var formData  = new FormData(f);
                var submitUrl = f.getAttribute('action') || originalUrl;

                var xhr = new XMLHttpRequest();
                xhr.open('POST', submitUrl, true);
                xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');

                xhr.onreadystatechange = function () {
                    if (xhr.readyState !== 4) return;

                    var finalUrl      = xhr.responseURL || '';
                    var submittedPath = submitUrl.replace(window.location.origin, '').split('?')[0];
                    var responsePath  = finalUrl.replace(window.location.origin, '').split('?')[0];
                    var isRedirect    = responsePath && responsePath !== submittedPath;

                    if (isRedirect) {
                        var reloadUrl = finalUrl || originalUrl;
                        fetch(reloadUrl, { credentials: 'same-origin' })
                            .then(function (r) { return r.text(); })
                            .then(function (html) {
                                var parser = new DOMParser();
                                var doc = parser.parseFromString(html, 'text/html');
                                var container = doc.querySelector('.container');
                                var drawerBody = document.getElementById('drawer-body');
                                if (container && drawerBody) {
                                    drawerBody.innerHTML = container.innerHTML;
                                    attachFormHandler(drawerBody, originalUrl);
                                    drawerBody.scrollTop = 0;
                                    showToast('Uploaded successfully!');
                                } else {
                                    var isClearanceComplete = false;
                                    var clearanceData = {};
                                    if (submitUrl.indexOf('clearance') !== -1) {
                                        var db = document.getElementById('drawer-body');
                                        if (db) {
                                            var sel = db.querySelector('[name=clearance_status]');
                                            isClearanceComplete = sel && sel.value === 'completed';
                                            var pdfForm = db.querySelector('form[data-pdf-info]');
                                            if (pdfForm) {
                                                var info = JSON.parse(pdfForm.getAttribute('data-pdf-info'));
                                                var secDed = parseFloat(db.querySelector('[name=security_deduction]').value) || 0;
                                                var lastWithheld = db.querySelector('[name=last_salary_withheld]').checked;
                                                var lastAmt = parseFloat(db.querySelector('[name=last_salary_amount]').value) || 0;
                                                var addDed = parseFloat(db.querySelector('[name=additional_deductions]').value) || 0;
                                                clearanceData = {
                                                    name: info.name,
                                                    employeeId: info.id,
                                                    designation: info.designation,
                                                    lastWorkingDate: info.lastDate,
                                                    totalPf: info.pf,
                                                    totalSecurity: info.security,
                                                    totalTax: info.tax,
                                                    totalVanChild: info.vanChild,
                                                    totalOther: info.other,
                                                    totalDeductions: info.grandTotal,
                                                    securityDeduction: secDed,
                                                    lastSalaryWithheld: lastWithheld,
                                                    lastSalaryAmount: lastAmt,
                                                    additionalDeductions: addDed,
                                                    clearanceDate: db.querySelector('[name=clearance_date]').value || '',
                                                    totalExitDeductions: secDed + addDed + (lastWithheld ? lastAmt : 0)
                                                };
                                            }
                                        }
                                    }
                                    closeDrawer();
                                    showToast('Saved successfully!');
                                    if (isClearanceComplete && window.jspdf) {
                                        window.generateClearancePDF(clearanceData);
                                    }
                                    var targetReload = (submitUrl.indexOf('clearance') !== -1 || submitUrl.indexOf('separation') !== -1 || submitUrl.indexOf('move-back') !== -1)
                                        ? (window.location.pathname + '?section=left-employees')
                                        : window.location.href;
                                    setTimeout(function () { window.location.href = targetReload; }, 800);
                                }
                            })
                            .catch(function () {
                                closeDrawer();
                                window.location.reload();
                            });
                        return;
                    }

                    var parser    = new DOMParser();
                    var doc       = parser.parseFromString(xhr.responseText, 'text/html');
                    var hasErrors = doc.querySelector('.errorlist, .alert-danger');
                    var form2     = doc.querySelector('form');

                    if (hasErrors || form2) {
                        var drawerBody = document.getElementById('drawer-body');
                        drawerBody.innerHTML = form2 ? form2.outerHTML : xhr.responseText;
                        attachFormHandler(drawerBody, originalUrl);
                        drawerBody.scrollTop = 0;
                    } else {
                        var isClearanceComplete2 = false;
                        var clearanceData2 = {};
                        if (submitUrl.indexOf('clearance') !== -1) {
                            var db2 = document.getElementById('drawer-body');
                            if (db2) {
                                var sel2 = db2.querySelector('[name=clearance_status]');
                                isClearanceComplete2 = sel2 && sel2.value === 'completed';
                                var pdfForm2 = db2.querySelector('form[data-pdf-info]');
                                if (pdfForm2) {
                                    var info2 = JSON.parse(pdfForm2.getAttribute('data-pdf-info'));
                                    var sd2 = parseFloat(db2.querySelector('[name=security_deduction]').value) || 0;
                                    var lw2 = db2.querySelector('[name=last_salary_withheld]').checked;
                                    var la2 = parseFloat(db2.querySelector('[name=last_salary_amount]').value) || 0;
                                    var ad2 = parseFloat(db2.querySelector('[name=additional_deductions]').value) || 0;
                                    clearanceData2 = {
                                        name: info2.name,
                                        employeeId: info2.id,
                                        designation: info2.designation,
                                        lastWorkingDate: info2.lastDate,
                                        totalPf: info2.pf,
                                        totalSecurity: info2.security,
                                        totalTax: info2.tax,
                                        totalVanChild: info2.vanChild,
                                        totalOther: info2.other,
                                        totalDeductions: info2.grandTotal,
                                        securityDeduction: sd2,
                                        lastSalaryWithheld: lw2,
                                        lastSalaryAmount: la2,
                                        additionalDeductions: ad2,
                                        clearanceDate: db2.querySelector('[name=clearance_date]').value || '',
                                        totalExitDeductions: sd2 + ad2 + (lw2 ? la2 : 0)
                                    };
                                }
                            }
                        }
                        closeDrawer();
                        showToast('Saved successfully!');
                        if (isClearanceComplete2 && window.jspdf) {
                            window.generateClearancePDF(clearanceData2);
                        }
                        var targetReload = (submitUrl.indexOf('clearance') !== -1 || submitUrl.indexOf('separation') !== -1 || submitUrl.indexOf('move-back') !== -1)
                            ? (window.location.pathname + '?section=left-employees')
                            : window.location.href;
                        setTimeout(function () { window.location.href = targetReload; }, 800);
                    }
                };

                xhr.onerror = function () {
                    if (btn) { btn.disabled = false; btn.textContent = originalText; }
                    showToast('Network error. Please try again.');
                };

                xhr.send(formData);
            });
        });
    }

    function attachDeleteHandlers(container, originalUrl) {
        container.querySelectorAll('a[href*="/delete/"]').forEach(function (a) {
            if (a.dataset.ajaxBound) return;
            a.dataset.ajaxBound = '1';
            a.removeAttribute('onclick');
            a.addEventListener('click', function (e) {
                e.preventDefault();
                var href = a.getAttribute('href');
                customConfirm('Delete this document?', function () {
                    fetch(href, { credentials: 'same-origin', headers: { 'X-Requested-With': 'XMLHttpRequest' } })
                        .then(function (r) { return r.json(); })
                        .then(function () {
                            var row = a.closest('.doc-item');
                            if (row) {
                                row.style.transition = 'opacity 0.2s';
                                row.style.opacity = '0';
                                setTimeout(function () {
                                    row.remove();
                                    var list = container.querySelector('.docs-list') || container.closest('.docs-list');
                                    if (list) {
                                        var remaining = list.querySelectorAll('.doc-item').length;
                                        var header = list.querySelector('.docs-header');
                                        if (header) header.textContent = 'Uploaded Documents (' + remaining + ')';
                                    }
                                }, 200);
                            }
                            showToast('Document deleted.');
                        })
                        .catch(function () {
                            window.location.href = href;
                        });
                });
            });
        });
    }

    function attachAddMoreHandler(container) {
        var addBtn = container.querySelector('#add-doc-row');
        if (!addBtn || addBtn.dataset.ajaxBound) return;
        addBtn.dataset.ajaxBound = '1';
        addBtn.addEventListener('click', function () {
            var docRows = container.querySelector('#doc-rows');
            if (!docRows) return;
            var row = docRows.querySelector('.form-row');
            if (!row) return;
            var newRow = row.cloneNode(true);
            newRow.querySelectorAll('input').forEach(function (inp) { inp.value = ''; });
            docRows.appendChild(newRow);
        });
    }

    /* ── custom confirm dialog ── */
    function customConfirm(message, onConfirm) {
        var existing = document.getElementById('custom-confirm');
        if (existing) existing.remove();

        var modal = document.createElement('div');
        modal.id = 'custom-confirm';
        modal.style.cssText = 'position:fixed;inset:0;z-index:9999;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,0.5);backdrop-filter:blur(2px);';
        modal.innerHTML =
            '<div style="background:#fff;border-radius:16px;padding:28px 28px 22px;width:360px;max-width:90vw;box-shadow:0 20px 60px rgba(0,0,0,0.25);text-align:center;">'
          + '<div style="width:48px;height:48px;background:#fef2f2;border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 16px;">'
          + '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#dc2626" stroke-width="2.5"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4h6v2"/></svg></div>'
          + '<h3 style="font-size:16px;font-weight:700;color:#1a1d23;margin-bottom:8px;">Confirm Delete</h3>'
          + '<p style="font-size:13.5px;color:#6b7280;margin-bottom:22px;">' + message + '</p>'
          + '<div style="display:flex;gap:10px;justify-content:center;">'
          + '<button id="confirm-cancel" style="flex:1;padding:10px;border-radius:9px;border:1.5px solid #e5e7eb;background:#fff;font-size:13.5px;font-weight:600;cursor:pointer;font-family:inherit;color:#374151;">Cancel</button>'
          + '<button id="confirm-ok" style="flex:1;padding:10px;border-radius:9px;border:none;background:#dc2626;color:#fff;font-size:13.5px;font-weight:700;cursor:pointer;font-family:inherit;">Delete</button>'
          + '</div></div>';

        document.body.appendChild(modal);
        document.getElementById('confirm-cancel').onclick = function () { modal.remove(); };
        document.getElementById('confirm-ok').onclick     = function () { modal.remove(); onConfirm(); };
        modal.addEventListener('click', function (e) { if (e.target === modal) modal.remove(); });
    }

    /* ── intercept all link clicks ── */
    document.addEventListener('click', function (e) {
        var el = e.target.closest('a[href]');
        if (!el) return;
        var href = el.getAttribute('href');
        if (!href || href === '#') return;

        /* delete links → custom confirm + POST (skip staff document deletes, handled by AJAX below) */
        if (href.indexOf('delete') !== -1 && !(href.indexOf('/documents/') !== -1 && href.indexOf('/delete/') !== -1)) {
            e.preventDefault();
            e.stopImmediatePropagation();
            customConfirm('Are you sure you want to delete this?', function () {
                var form = document.createElement('form');
                form.method = 'POST';
                form.action = href;
                form.style.display = 'none';
                var csrf = document.querySelector('[name=csrfmiddlewaretoken]');
                if (csrf) {
                    var csrfInput   = document.createElement('input');
                    csrfInput.type  = 'hidden';
                    csrfInput.name  = 'csrfmiddlewaretoken';
                    csrfInput.value = csrf.value;
                    form.appendChild(csrfInput);
                }
                document.body.appendChild(form);
                form.submit();
            });
            return;
        }

        /* add/edit links → open in drawer */
        if (isDrawerUrl(href)) {
            e.preventDefault();
            e.stopImmediatePropagation();
            var title = getTitle(href);
            if (title === 'Edit Staff') {
                var card = el.closest('[style*="background:#fff"]') || el.closest('.staff-card') || el.parentElement.parentElement.parentElement;
                if (card) {
                    var allBold = card.querySelectorAll('[style*="font-weight:700"]');
                    for (var i = 0; i < allBold.length; i++) {
                        var txt = allBold[i].textContent.trim();
                        if (txt.length > 2 && txt.indexOf(' ') !== -1) { title = 'Edit Staff — ' + txt; break; }
                    }
                }
            }
            openDrawer(href, title);
            return;
        }
    }, true);

    /* close on Escape */
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') closeDrawer();
    });

    /* ── AJAX delete for staff documents ── */
    document.addEventListener('click', function (e) {
        var link = e.target.closest('a[href*="/documents/"][href*="/delete/"]');
        if (!link) return;
        e.preventDefault();
        e.stopPropagation();
        var href = link.getAttribute('href');
        var row = link.closest('.doc-item');
        customConfirm('Are you sure you want to delete this?', function () {
            fetch(href, { credentials: 'same-origin', headers: { 'X-Requested-With': 'XMLHttpRequest' } })
                .then(function (r) { return r.json(); })
                .then(function () {
                    if (row) {
                        row.style.transition = 'opacity 0.2s';
                        row.style.opacity = '0';
                        setTimeout(function () {
                            row.remove();
                            var docsList = document.querySelector('#drawer-body .docs-list') || document.querySelector('.docs-list');
                            if (docsList) {
                                var remaining = docsList.querySelectorAll('.doc-item').length;
                                var header = docsList.querySelector('.docs-header');
                                if (header) header.textContent = 'Uploaded Documents (' + remaining + ')';
                            }
                        }, 200);
                    }
                    if (typeof showToast === 'function') showToast('Document deleted.');
                })
                .catch(function () {
                    if (typeof showToast === 'function') showToast('Failed to delete.', 'error');
                });
        });
    }, true);

    var nativeConfirm = window.confirm;
    window.confirm = function (msg) { return nativeConfirm(msg); };

})();


function filterAttendanceByDate(classId) {
    const date = document.getElementById('att-date-' + classId).value;
    const rows = document.querySelectorAll('.att-row-' + classId);
    let visible = 0;

    rows.forEach(row => {
        const rowDate = row.querySelector('td:nth-child(3)').textContent.trim();
        // rowDate is in YYYY-MM-DD format from Django
        const match = !date || rowDate === date;
        row.style.display = match ? '' : 'none';
        if (match) visible++;
    });

    const empty = document.getElementById('att-empty-' + classId);
    if (empty) empty.style.display = visible === 0 ? 'block' : 'none';

    // Reset status filter buttons to "All" visually
    document.querySelectorAll(`[onclick*="filterAttendance('${classId}'"]`).forEach(btn => {
        btn.style.background = '#fff';
        btn.style.color = 'var(--text-secondary)';
    });
}

function clearAttendanceDate(classId) {
    const input = document.getElementById('att-date-' + classId);
    if (input) input.value = '';
    // Show all rows
    document.querySelectorAll('.att-row-' + classId).forEach(row => {
        row.style.display = '';
    });
    const empty = document.getElementById('att-empty-' + classId);
    if (empty) empty.style.display = 'none';
}

// ════════════════════════════════════════════
// SALARY SLIPS SEARCH
// ════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', function () {
    var slipSearch = document.getElementById('slip-search');
    if (slipSearch) {
        slipSearch.addEventListener('input', function () {
            var q = this.value.toLowerCase();
            document.querySelectorAll('.slip-row').forEach(function (row) {
                var name = row.querySelector('td:nth-child(2)');
                row.style.display = (name && name.textContent.toLowerCase().indexOf(q) !== -1) ? '' : 'none';
            });
        });
    }
});
