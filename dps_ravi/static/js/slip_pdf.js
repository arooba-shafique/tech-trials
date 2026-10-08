(function () {
    'use strict';

    function libsReady() {
        return typeof window.html2canvas === 'function' &&
            !!window.jspdf &&
            typeof window.jspdf.jsPDF === 'function';
    }

    function safeName(value) {
        var name = String(value || '')
            .replace(/[\\/:*?"<>|]+/g, '')
            .replace(/\s+/g, ' ')
            .trim();
        return name || 'Salary Slip';
    }

    function delay(ms) {
        return new Promise(function (resolve) { setTimeout(resolve, ms); });
    }

    function waitForDocument(doc, timeout) {
        var start = Date.now();
        var limit = timeout || 8000;
        return new Promise(function (resolve, reject) {
            (function poll() {
                if (doc.readyState === 'complete' && doc.querySelector('.slip')) { resolve(); return; }
                if (Date.now() - start > limit) { reject(new Error('Timed out loading salary slip.')); return; }
                setTimeout(poll, 100);
            })();
        });
    }

    function waitForFonts(doc) {
        if (doc.fonts && doc.fonts.ready) {
            return Promise.race([doc.fonts.ready.catch(function () {}), delay(3000)]);
        }
        return delay(300);
    }

    function savePdf(pdf, canvas, filename) {
        var margin = 8;
        var pw = pdf.internal.pageSize.getWidth();
        var ph = pdf.internal.pageSize.getHeight();
        var imgW = pw - margin * 2;
        var usableH = ph - margin * 2;
        var totalH = canvas.height * imgW / canvas.width;

        if (totalH <= usableH) {
            pdf.addImage(canvas.toDataURL('image/jpeg', 0.92), 'JPEG', margin, margin, imgW, totalH);
            pdf.save(filename);
            return;
        }

        var pxPerMm = canvas.width / imgW;
        var slicePx = Math.floor(usableH * pxPerMm);
        var y = 0;
        var first = true;
        while (y < canvas.height) {
            var h = Math.min(slicePx, canvas.height - y);
            var slice = document.createElement('canvas');
            slice.width = canvas.width;
            slice.height = h;
            slice.getContext('2d').drawImage(canvas, 0, y, canvas.width, h, 0, 0, canvas.width, h);
            if (!first) { pdf.addPage(); }
            pdf.addImage(slice.toDataURL('image/jpeg', 0.92), 'JPEG', margin, margin, imgW, h / pxPerMm);
            y += h;
            first = false;
        }
        pdf.save(filename);
    }

    function renderToCanvas(html) {
        var parsed = new DOMParser().parseFromString(html, 'text/html');
        var slip = parsed.querySelector('.slip');
        if (!slip) {
            return Promise.reject(new Error('Salary slip content not found in response.'));
        }

        var filename = safeName(
            slip.getAttribute('data-pdf-filename') ||
            (parsed.title || '').replace(/^Salary Slip\s*[-\u2013]\s*/i, '')
        ) + '.pdf';

        var frame = document.createElement('iframe');
        frame.setAttribute('aria-hidden', 'true');
        frame.style.cssText = 'position:fixed;left:0;bottom:0;width:900px;height:1200px;' +
            'border:0;opacity:0;pointer-events:none;z-index:-1;';
        document.body.appendChild(frame);

        function cleanup() {
            if (frame.parentNode) { frame.parentNode.removeChild(frame); }
        }

        var doc = frame.contentDocument;
        doc.open();
        doc.write(html);
        doc.close();

        return waitForDocument(doc)
            .then(function () { return waitForFonts(doc); })
            .then(function () {
                Array.prototype.slice.call(doc.querySelectorAll('.no-print')).forEach(function (node) {
                    if (node.parentNode) { node.parentNode.removeChild(node); }
                });
                return window.html2canvas(doc.querySelector('.slip'), {
                    backgroundColor: '#ffffff',
                    scale: 2,
                    useCORS: true,
                    logging: false,
                    windowWidth: 900
                });
            })
            .then(function (canvas) {
                var pdf = new window.jspdf.jsPDF({
                    orientation: 'portrait',
                    unit: 'mm',
                    format: 'a4'
                });
                savePdf(pdf, canvas, filename);
                return filename;
            })
            .then(function (result) { cleanup(); return result; },
                  function (err) { cleanup(); throw err; });
    }

    window.slipPDF = function (btn, url) {
        url = url || (btn && btn.getAttribute('data-slip-url')) || '';
        if (!url) { return false; }
        if (!libsReady()) { return true; }
        if (btn && btn.getAttribute('data-slip-busy') === '1') { return false; }

        var label = btn ? btn.innerHTML : null;
        if (btn) {
            btn.setAttribute('data-slip-busy', '1');
            btn.innerHTML = 'Saving&hellip;';
            btn.style.pointerEvents = 'none';
        }

        function restore() {
            if (btn) {
                btn.removeAttribute('data-slip-busy');
                btn.style.pointerEvents = '';
                if (label !== null) { btn.innerHTML = label; }
            }
        }

        fetch(url, { credentials: 'same-origin' })
            .then(function (res) {
                if (!res.ok) { throw new Error('Server returned ' + res.status + '.'); }
                return res.text();
            })
            .then(renderToCanvas)
            .then(function () { restore(); },
                  function (err) {
                      restore();
                      alert('Could not create PDF: ' + (err && err.message ? err.message : err));
                  });

        return false;
    };
})();
