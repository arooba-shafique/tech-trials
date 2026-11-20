/* =====================================================
   Student ID Cards -> PDF  (html2canvas + jsPDF)
   Every PDF page is exactly 86mm x 54mm (true card size):
   page 1 = front, page 2 = back, then the next student.
   Used by the Admin Manager dashboard "ID Cards" section.
   ===================================================== */
(function () {
    'use strict';

    var CARD_W = 86;   // mm
    var CARD_H = 54;   // mm

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

    /* Render one card face (.idc-front / .idc-back) onto a canvas. */
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
                Array.prototype.slice.call(doc.querySelectorAll('.idc-card')).forEach(function (n) {
                    n.style.width = '500px';
                    n.style.height = 'auto';
                    n.style.aspectRatio = '86 / 54';
                    n.style.borderRadius = '0';
                    n.style.boxShadow = 'none';
                    n.style.margin = '0';
                });
            }
        });
    }

    function addFace(pdf, canvas) {
        if (!pdf) {
            pdf = new window.jspdf.jsPDF({ unit: 'mm', format: [CARD_W, CARD_H], orientation: 'landscape' });
        } else {
            pdf.addPage([CARD_W, CARD_H], 'landscape');
        }
        // JPEG at 0.95 keeps the colours identical while keeping file size sane
        pdf.addImage(canvas.toDataURL('image/jpeg', 0.95), 'JPEG', 0, 0, CARD_W, CARD_H);
        return pdf;
    }

    /* One 86x54mm page per card face. */
    function compose(wraps, filename, onProgress) {
        var pdf = null;
        var i = 0;

        function next() {
            if (i >= wraps.length) {
                if (pdf) { pdf.save(filename); }
                return Promise.resolve(wraps.length);
            }
            var wrap = wraps[i++];
            if (onProgress) { onProgress(i, wraps.length); }
            var front = wrap.querySelector('.idc-front');
            var back = wrap.querySelector('.idc-back');
            if (!front || !back) { return next(); }
            return capture(front)
                .then(function (canvas) { pdf = addFace(pdf, canvas); })
                .then(function () { return capture(back); })
                .then(function (canvas) { pdf = addFace(pdf, canvas); })
                .then(next);
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
            return Promise.resolve(0);
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
