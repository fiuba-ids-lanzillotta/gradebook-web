document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('form-marcar');
    if (!form) return;

    const els = {
        form,
        qrReader: document.getElementById('qr-reader'),
        placeholder: document.getElementById('scanner-placeholder'),
        btnCamara: document.getElementById('btn-activar-camara'),
        btnDetener: document.getElementById('btn-detener-camara'),
        inputCodigo: document.getElementById('codigo-manual'),
        inputPadron: document.getElementById('padron-manual'),
        btnConfirmar: document.getElementById('btn-confirmar'),
        resultado: document.getElementById('resultado-asistencia'),
        marcarUrl: form.dataset.marcarUrl,
    };

    let html5QrCode = null;
    let camaraActiva = false;
    let enviando = false;
    let ultimoCodigo = '';
    let ultimoAt = 0;

    function mostrarResultado(tipo, texto) {
        if (!els.resultado) return;
        els.resultado.className = 'asistencia__resultado is-visible is-' + tipo;
        els.resultado.textContent = texto;
    }

    function extraerCodigo(valor) {
        const trimmed = (valor || '').trim();
        const desdeUrl = trimmed.match(/\/asistencia\/([A-Za-z0-9_-]+)/);
        if (desdeUrl) return desdeUrl[1];
        return trimmed;
    }

    async function marcarAsistencia({ codigo, padron, origen }) {
        const ahora = Date.now();
        const codigoNorm = extraerCodigo(codigo);
        if (origen === 'scan' && codigoNorm && codigoNorm === ultimoCodigo && ahora - ultimoAt < 2500) {
            return;
        }
        if (enviando) return;
        if (!codigoNorm && !padron) {
            mostrarResultado('error', 'Ingresá el código del QR o el padrón.');
            return;
        }

        enviando = true;
        ultimoCodigo = codigoNorm;
        ultimoAt = ahora;
        if (els.btnConfirmar) els.btnConfirmar.disabled = true;

        try {
            const cuerpo = new URLSearchParams();
            if (codigoNorm) cuerpo.set('codigo', codigoNorm);
            if (padron) cuerpo.set('padron', padron);

            const respuesta = await fetch(els.marcarUrl, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    Accept: 'application/json',
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: cuerpo.toString(),
            });

            if (respuesta.status === 401) {
                window.location.href = '/admin/login';
                return;
            }

            const datos = await respuesta.json().catch(() => ({}));

            if (datos.ok) {
                mostrarResultado('info', datos.mensaje || 'Leído. Todavía no se guarda en la base.');
                els.inputCodigo.value = '';
                els.inputPadron.value = '';
            } else {
                mostrarResultado('error', datos.error || 'No se pudo leer el código o el padrón.');
            }
        } catch (error) {
            mostrarResultado('error', 'No se pudo confirmar. Revisá la conexión.');
        } finally {
            enviando = false;
            if (els.btnConfirmar) els.btnConfirmar.disabled = false;
        }
    }

    async function resetVista() {
        if (html5QrCode && camaraActiva) {
            try { await html5QrCode.stop(); } catch (e) { /* ya detenida */ }
        }
        if (html5QrCode) {
            try { await html5QrCode.clear(); } catch (e) { /* sin instancia */ }
        }
        camaraActiva = false;
        if (els.qrReader) els.qrReader.classList.remove('is-active');
        if (els.placeholder) els.placeholder.classList.remove('is-hidden');
        if (els.btnCamara) {
            els.btnCamara.disabled = false;
            els.btnCamara.textContent = 'Activar cámara del dispositivo';
        }
        if (els.btnDetener) els.btnDetener.classList.remove('is-visible');
    }

    const CONFIG = { fps: 10, qrbox: { width: 220, height: 220 } };
    const PREFERENCIAS = [{ facingMode: 'environment' }, { facingMode: 'user' }];

    async function iniciarConPreferencias() {
        const onDecode = (texto) => marcarAsistencia({ codigo: texto, origen: 'scan' });
        const onError = () => {};
        let ultimoError = null;

        for (const config of PREFERENCIAS) {
            try {
                await html5QrCode.start(config, CONFIG, onDecode, onError);
                return;
            } catch (err) {
                ultimoError = err;
            }
        }

        const devices = await Html5Qrcode.getCameras();
        if (devices && devices.length) {
            const trasera = devices.find((d) => /back|rear|environment|trasera/i.test(d.label));
            await html5QrCode.start(trasera ? trasera.id : devices[0].id, CONFIG, onDecode, onError);
            return;
        }
        throw ultimoError || new Error('NO_CAMERA');
    }

    function mensajeErrorCamara(err) {
        if (!window.isSecureContext) {
            return 'La cámara pide HTTPS o localhost. En el celu usá el dominio https, o cargá el código / padrón a mano.';
        }
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            return 'Este navegador no deja usar la cámara. Probá Chrome o Safari.';
        }
        if (err && err.message === 'NO_CAMERA') {
            return 'No hay cámara. Si estás en una VM, usá el código o el padrón.';
        }
        if (err && (err.name === 'NotAllowedError' || /permission/i.test(String(err && err.message)))) {
            return 'Permiso de cámara denegado. Tocá el candado → Cámara → Permitir y recargá.';
        }
        if (err && (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError')) {
            return 'No se detectó cámara. Usá el código o el padrón.';
        }
        if (err && err.name === 'NotReadableError') {
            return 'La cámara la está usando otra app. Cerrala e intentá de nuevo.';
        }
        return 'No se pudo activar la cámara. Usá el código o el padrón.';
    }

    async function iniciarCamara() {
        if (camaraActiva) return;
        if (typeof Html5Qrcode === 'undefined') {
            mostrarResultado('error', 'No se pudo cargar el lector QR. Revisá la conexión.');
            return;
        }

        html5QrCode = new Html5Qrcode('qr-reader');
        els.placeholder.classList.add('is-hidden');
        els.qrReader.classList.add('is-active');
        els.btnCamara.disabled = true;
        els.btnCamara.textContent = 'Escaneando…';
        els.btnDetener.classList.add('is-visible');

        try {
            await iniciarConPreferencias();
            camaraActiva = true;
            mostrarResultado('info', 'Apuntá al código. Al leerlo se completa el campo (todavía no se guarda).');
        } catch (err) {
            await resetVista();
            mostrarResultado('error', mensajeErrorCamara(err));
        }
    }

    els.btnCamara.addEventListener('click', iniciarCamara);
    els.btnDetener.addEventListener('click', () => {
        resetVista();
    });

    if (els.inputPadron) {
        els.inputPadron.addEventListener('input', () => {
            els.inputPadron.value = els.inputPadron.value.replace(/\D/g, '');
        });
    }

    form.addEventListener('submit', (evento) => {
        evento.preventDefault();
        marcarAsistencia({
            codigo: els.inputCodigo.value,
            padron: els.inputPadron.value,
            origen: 'form',
        });
    });

    const modalTomar = document.getElementById('modal-tomar');
    const abrirTomar = document.querySelector('.js-tomar');
    if (modalTomar && abrirTomar) {
        abrirTomar.addEventListener('click', () => {
            modalTomar.classList.add('is-open');
            modalTomar.setAttribute('aria-hidden', 'false');
        });
        modalTomar.querySelectorAll('[data-close]').forEach((el) => {
            el.addEventListener('click', () => {
                modalTomar.classList.remove('is-open');
                modalTomar.setAttribute('aria-hidden', 'true');
            });
        });
    }
});