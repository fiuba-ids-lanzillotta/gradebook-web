document.addEventListener('DOMContentLoaded', function () {
    const app = document.getElementById('asistencia-app');
    const form = document.getElementById('form-marcar');
    if (!app || !form) return;

    const els = {
        app,
        form,
        qrReader: document.getElementById('qr-reader'),
        placeholder: document.getElementById('scanner-placeholder'),
        btnCamara: document.getElementById('btn-activar-camara'),
        btnDetener: document.getElementById('btn-detener-camara'),
        inputCodigo: document.getElementById('codigo-manual'),
        inputPadron: document.getElementById('padron-manual'),
        btnConfirmar: document.getElementById('btn-confirmar'),
        resultado: document.getElementById('resultado-asistencia'),
        progreso: document.getElementById('progreso-envio'),
        progresoBar: document.getElementById('progreso-envio-bar'),
        progresoTexto: document.getElementById('progreso-envio-texto'),
        btnTomar: document.querySelector('.js-tomar'),
        btnConfirmarTomar: document.getElementById('btn-confirmar-tomar'),
        modalTomar: document.getElementById('modal-tomar'),
    };

    let claseId = (app.dataset.claseId || '').trim();
    const puedeGestionar = app.dataset.puedeGestionar === '1';
    let html5QrCode = null;
    let camaraActiva = false;
    let enviando = false;
    let tomando = false;
    let ultimoCodigo = '';
    let ultimoAt = 0;

    function urlConClase(tpl, id) {
        return tpl.replace('/0/', '/' + id + '/');
    }

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

    function pintarProgreso(enviados, total, conError) {
        if (!els.progreso) return;
        els.progreso.hidden = false;
        const tope = total || 0;
        const pct = tope ? Math.min(100, Math.round((enviados / tope) * 100)) : 0;
        if (els.progresoBar) els.progresoBar.style.width = pct + '%';
        let texto = tope ? ('Enviando mails: ' + enviados + ' / ' + tope) : 'Enviando mails…';
        if (conError) texto += ' · ' + conError + ' con error';
        if (els.progresoTexto) els.progresoTexto.textContent = texto;
    }

    function ocultarProgreso() {
        if (!els.progreso) return;
        els.progreso.hidden = true;
        if (els.progresoBar) els.progresoBar.style.width = '0';
    }

    function setTomando(activo) {
        tomando = activo;
        if (!els.btnTomar) return;
        els.btnTomar.disabled = activo || !puedeGestionar;
        els.btnTomar.setAttribute('aria-busy', activo ? 'true' : 'false');
        if (puedeGestionar) {
            els.btnTomar.textContent = activo ? 'Enviando…' : 'Tomar asistencia';
        }
    }

    async function postJson(url, cuerpo) {
        const respuesta = await fetch(url, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                Accept: 'application/json',
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(cuerpo || {}),
        });
        if (respuesta.status === 401) {
            window.location.href = '/admin/login';
            throw new Error('sesion');
        }
        const datos = await respuesta.json().catch(() => ({}));
        return { http: respuesta.status, datos };
    }

    async function tomarAsistencia() {
        if (tomando) return;
        setTomando(true);
        ocultarProgreso();

        try {
            const creado = await postJson(app.dataset.urlClases, {});
            if (!creado.datos.ok) {
                ocultarProgreso();
                mostrarResultado('error', creado.datos.error || 'No se pudo crear la toma de hoy.');
                return;
            }
            claseId = String(creado.datos.clase_id || (creado.datos.clase && creado.datos.clase.id) || '');
            app.dataset.claseId = claseId;
            if (!claseId) {
                ocultarProgreso();
                mostrarResultado('error', 'La API no devolvió el id de la clase.');
                return;
            }

            pintarProgreso(0, creado.datos.total_estudiantes || 0, 0);
            let estado;
            do {
                const lote = await postJson(urlConClase(app.dataset.urlEnviarTpl, claseId), {});
                if (!lote.datos.ok) {
                    ocultarProgreso();
                    mostrarResultado('error', lote.datos.error || 'Falló el envío de un lote.');
                    return;
                }
                estado = lote.datos;
                pintarProgreso(estado.enviados || 0, estado.total || 0, estado.con_error || 0);
            } while (!estado.completo);

            const extra = estado.con_error
                ? ' · ' + estado.con_error + ' no se pudieron enviar (reintentá Tomar asistencia).'
                : '';
            mostrarResultado('ok', 'Listo: ' + (estado.enviados || 0) + '/' + (estado.total || 0) + ' mails.' + extra);
            if (els.progresoTexto) {
                els.progresoTexto.textContent = 'Envío completo: ' + (estado.enviados || 0) + '/' + (estado.total || 0);
            }
        } catch (error) {
            if (error && error.message === 'sesion') return;
            ocultarProgreso();
            mostrarResultado('error', 'No se pudo tomar asistencia. Revisá la conexión.');
        } finally {
            setTomando(false);
        }
    }

    async function marcarAsistencia({ codigo, padron, origen }) {
        if (!claseId) {
            mostrarResultado('error', 'Primero tomá asistencia de hoy (botón de arriba).');
            return;
        }
        const ahora = Date.now();
        const codigoNorm = extraerCodigo(codigo);
        if (origen === 'scan' && codigoNorm && codigoNorm === ultimoCodigo && ahora - ultimoAt < 2500) {
            return;
        }
        if (enviando) return;
        if (codigoNorm && padron) {
            mostrarResultado('error', 'Ingresá el código del QR o el padrón, no los dos.');
            return;
        }
        if (!codigoNorm && !padron) {
            mostrarResultado('error', 'Ingresá el código del QR o el padrón.');
            return;
        }

        enviando = true;
        ultimoCodigo = codigoNorm;
        ultimoAt = ahora;
        if (els.btnConfirmar) els.btnConfirmar.disabled = true;

        const cuerpo = {};
        if (padron) {
            cuerpo.padron = padron;
        } else {
            cuerpo.codigo = codigoNorm;
            if (origen === 'form') cuerpo.manual = true;
        }

        try {
            const { datos } = await postJson(urlConClase(app.dataset.urlMarcarTpl, claseId), cuerpo);
            if (datos.ok) {
                mostrarResultado('ok', datos.mensaje || 'Presente.');
                els.inputCodigo.value = '';
                els.inputPadron.value = '';
            } else {
                mostrarResultado('error', datos.error || 'Código o padrón inválido para la clase de hoy.');
            }
        } catch (error) {
            if (error && error.message === 'sesion') return;
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
        if (!puedeGestionar || camaraActiva) return;
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
            mostrarResultado('info', 'Cámara activa. Apuntá al QR; sigue prendida entre alumnos. Detener cámara la apaga.');
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
        if (!puedeGestionar) return;
        marcarAsistencia({
            codigo: els.inputCodigo.value,
            padron: els.inputPadron.value,
            origen: 'form',
        });
    });

    if (els.modalTomar && els.btnTomar) {
        els.btnTomar.addEventListener('click', () => {
            if (!puedeGestionar || tomando || els.btnTomar.disabled) return;
            els.modalTomar.classList.add('is-open');
            els.modalTomar.setAttribute('aria-hidden', 'false');
        });
        els.modalTomar.querySelectorAll('[data-close]').forEach((el) => {
            el.addEventListener('click', () => {
                els.modalTomar.classList.remove('is-open');
                els.modalTomar.setAttribute('aria-hidden', 'true');
            });
        });
    }
    if (els.btnConfirmarTomar) {
        els.btnConfirmarTomar.addEventListener('click', () => {
            if (!puedeGestionar) return;
            if (els.modalTomar) {
                els.modalTomar.classList.remove('is-open');
                els.modalTomar.setAttribute('aria-hidden', 'true');
            }
            tomarAsistencia();
        });
    }
});