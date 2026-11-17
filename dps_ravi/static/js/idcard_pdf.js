/* =====================================================
   Student ID Cards → PDF  (html2canvas + jsPDF)
   Used by the Admin Manager dashboard "ID Cards" section.
   ===================================================== */
(function () {
    'use strict';

    function libsReady() {
        return typeof window.html2canvas === 'function' &&
            !!window.jspdf && typeof window.jspdf.jsPDF === 'function';
    }

    function safeName(value) {
        return String(value || '')
            .replace(/[\\/:*?"<>|]+/g, '')
            .replace(/\s+/g, ' ')
            .trim() || 'Student';
    }

    /* Render a single .idc element (front + back) onto a canvas. */
    function capture(el) {
        return window.html2canvas(el, {
            backgroundColor: '#ffffff',
            scale: 2,
            useCORS: true,
            logging: false,
            onclone: function (doc) {
                Array.prototype.slice.call(doc.querySelectorAll('.idc-actions')).forEach(function (n) {
                    if (n.parentNode) { n.parentNode.removeChild(n); }
                });
                Array.prototype.slice.call(doc.querySelectorAll('.idc')).forEach(function (n) {
                    n.style.display = 'flex';
                    n.style.width = '500px';
                    n.style.maxWidth = 'none';
                    n.style.margin = '0';
                    n.style.breakInside = 'auto';
                });
                var area = doc.getElementById('idcPrintArea');
                if (area) { area.style.display = 'none'; }
            }
        });
    }

    /* One landscape A4 page per student (front + back together). */
    function compose(cards, filename, onProgress) {
        var jsPDF = window.jspdf.jsPDF;
        var pdf = null;
        var i = 0;

        function next() {
            if (i >= cards.length) {
                if (pdf) { pdf.save(filename); }
                return Promise.resolve(cards.length);
            }
            var el = cards[i++];
            if (onProgress) { onProgress(i, cards.length); }
            return capture(el).then(function (canvas) {
                if (!pdf) {
                    pdf = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a4' });
                } else {
                    pdf.addPage('a4', 'landscape');
                }
                var pw = pdf.internal.pageSize.getWidth();
                var ph = pdf.internal.pageSize.getHeight();
                var margin = 8;
                var maxW = pw - margin * 2;
                var maxH = ph - margin * 2;
                var w = maxW;
                var h = canvas.height * w / canvas.width;
                if (h > maxH) { h = maxH; w = canvas.width * h / canvas.height; }
                pdf.addImage(canvas.toDataURL('image/jpeg', 0.92), 'JPEG', (pw - w) / 2, (ph - h) / 2, w, h);
            }).then(next);
        }

        return next();
    }

    function run(btn, cards, filename) {
        if (!cards.length) {
            alert('No student cards selected.');
            return Promise.resolve(0);
        }
        if (!libsReady()) {
            alert('The PDF library is still loading — please try again, or use the Print button instead.');
            return Promise.resolve(0);
        }
        if (cards.length > 60 &&
            !window.confirm('This will generate ' + cards.length + ' ID cards into one PDF.\nIt may take a minute — continue?')) {
            return;
        }

        var label = btn ? btn.innerHTML : '';
        function progress(done, total) {
            if (btn) { btn.innerHTML = 'Saving ' + done + '/' + total + '…'; }
        }
        if (btn) { btn.disabled = true; btn.innerHTML = 'Preparing…'; }

        return compose(cards, filename, progress).then(function () {
            if (btn) { btn.disabled = false; btn.innerHTML = label; }
            return cards.length;
        }, function (err) {
            if (btn) { btn.disabled = false; btn.innerHTML = label; }
            alert('Could not create PDF: ' + (err && err.message ? err.message : err) +
                  '\nYou can still use the Print button and choose "Save as PDF".');
            throw err;
        });
    }

    function cardOf(btn) {
        return btn && btn.closest ? btn.closest('.idc') : null;
    }

    /* Download a single student's card. */
    window.idcPdfOne = function (btn) {
        var card = cardOf(btn);
        if (!card) { return Promise.resolve(0); }
        var name = safeName(card.getAttribute('data-name'));
        return run(btn, [card], 'ID-Card-' + name + '.pdf');
    };

    /* Download every currently visible (filtered) card. */
    window.idcPdfAll = function (btn) {
        var cards = (typeof window.idcVisible === 'function')
            ? window.idcVisible()
            : Array.prototype.slice.call(document.querySelectorAll('#idcGrid .idc'));
        var suffix = '';
        var sel = document.getElementById('idcClassFilter');
        if (sel && sel.value) { suffix = '-' + safeName(sel.options[sel.selectedIndex].text); }
        return run(btn, cards, 'Student-ID-Cards' + suffix + '.pdf');
    };
})();
