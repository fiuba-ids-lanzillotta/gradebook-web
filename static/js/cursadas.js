document.addEventListener('DOMContentLoaded', function () {
    const filtroCodigo = document.getElementById('filtro-codigo');
    const filtroCuatrimestre = document.getElementById('filtro-cuatrimestre');
    const filtroAnio = document.getElementById('filtro-anio');
    const avisoSinResultado = document.getElementById('cursadas-sin-resultado');

    if (filtroCodigo && filtroCuatrimestre && filtroAnio) {
        const aplicarFiltro = () => {
            const codigo = filtroCodigo.value.trim().toLowerCase();
            const cuatrimestre = filtroCuatrimestre.value;
            const anio = filtroAnio.value.trim();
            const filas = document.querySelectorAll('.cursadas__tabla tbody tr');
            let visibles = 0;

            filas.forEach((fila) => {
                const coincideCodigo = !codigo || String(fila.dataset.codigo || '').toLowerCase().includes(codigo);
                const coincideCuatrimestre = !cuatrimestre || String(fila.dataset.cuatrimestre || '') === cuatrimestre;
                const coincideAnio = !anio || String(fila.dataset.anio || '') === anio;
                const visible = coincideCodigo && coincideCuatrimestre && coincideAnio;
                fila.hidden = !visible;
                if (visible) visibles += 1;
            });

            if (avisoSinResultado) avisoSinResultado.hidden = visibles !== 0;
        };

        filtroCodigo.addEventListener('input', aplicarFiltro);
        filtroCuatrimestre.addEventListener('change', aplicarFiltro);
        filtroAnio.addEventListener('input', aplicarFiltro);
    }

    const materiasEl = document.getElementById('materias-cursadas');
    let materias = {};
    if (materiasEl) {
        try { materias = JSON.parse(materiasEl.textContent || '{}'); } catch (error) { materias = {}; }
    }

    const abrirModal = (modal) => {
        if (!modal) return;
        modal.classList.add('is-open');
        modal.setAttribute('aria-hidden', 'false');
    };
    const cerrarModal = (modal) => {
        if (!modal) return;
        modal.classList.remove('is-open');
        modal.setAttribute('aria-hidden', 'true');
    };
    const cablearCierre = (modal) => {
        if (!modal) return;
        modal.querySelectorAll('[data-close]').forEach((el) => {
            el.addEventListener('click', () => cerrarModal(modal));
        });
    };

    const mostrarErrores = (lista, errores) => {
        if (!lista) return;
        lista.replaceChildren();
        errores.forEach((texto) => {
            const item = document.createElement('li');
            item.textContent = texto;
            lista.appendChild(item);
        });
        lista.hidden = errores.length === 0;
    };

    const anioDe = (fecha) => Number(String(fecha || '').slice(0, 4));
    const mesDe = (fecha) => Number(String(fecha || '').slice(5, 7));

    const validarAlta = (form, anioOriginal) => {
        const errores = [];
        const codigo = form.codigo.value.trim();
        const nombre = form.nombre.value.trim();
        const cuatrimestre = form.cuatrimestre.value;
        const inicio = form.fecha_inicio.value;
        const fin = form.fecha_fin.value;
        const anioActual = new Date().getFullYear();
        const anioGuardado = Number(anioOriginal) || 0;

        if (!codigo) errores.push('Ingresá el código de la materia.');
        if (!nombre) errores.push('Ingresá el nombre de la materia.');
        if (!cuatrimestre) errores.push('Elegí el cuatrimestre.');
        if (!inicio || !fin) {
            errores.push('Ingresá la fecha de inicio y la de fin.');
            return errores;
        }

        const anioInicio = anioDe(inicio);
        const anioFin = anioDe(fin);

        const anioAnteriorAlActual = (anio) => anio < anioActual && anio !== anioGuardado;

        if (anioAnteriorAlActual(anioInicio) || anioAnteriorAlActual(anioFin)) {
            const texto = anioGuardado && anioGuardado < anioActual
                ? `Las fechas tienen que ser de ${anioGuardado}, o del año actual en adelante.`
                : 'Las fechas tienen que ser del año actual en adelante.';
            errores.push(texto);
        }
        if (anioInicio !== anioFin) {
            errores.push('La fecha de inicio y la de fin tienen que ser del mismo año.');
        }
        if (inicio >= fin) {
            errores.push('La fecha de inicio tiene que ser anterior a la fecha de fin.');
        }

        const cuatri = Number(cuatrimestre);
        const fuera = (mes) => (cuatri === 1 ? mes < 1 || mes > 6 : mes < 7 || mes > 12);

        if (cuatrimestre && (fuera(mesDe(inicio)) || fuera(mesDe(fin)))) {
            const texto = cuatri === 1
                ? 'El 1.er cuatrimestre admite fechas entre el 1 de enero y el 30 de junio.'
                : 'El 2.º cuatrimestre admite fechas entre el 1 de julio y el 31 de diciembre.';
            errores.push(texto);
        }

        return errores;
    };

    const enviarFormulario = (form, listaErrores, anio) => {
        const datos = new FormData(form);
        datos.set('anio', String(anio));
        const confirmar = form.querySelector('[type="submit"]');
        if (confirmar) confirmar.disabled = true;

        fetch(form.action, {
            method: 'POST',
            body: datos,
            headers: { 'X-Requested-With': 'fetch' },
        })
            .then((respuesta) => respuesta.json().then((cuerpo) => ({ estado: respuesta.status, cuerpo })))
            .then(({ estado, cuerpo }) => {
                if (estado === 401) {
                    window.location.assign('/admin/login');
                    return;
                }
                if (cuerpo && cuerpo.ok) {
                    window.location.assign(window.location.pathname);
                    return;
                }
                mostrarErrores(listaErrores, [(cuerpo && cuerpo.error) || 'No se pudo guardar la cursada.']);
                if (confirmar) confirmar.disabled = false;
            })
            .catch(() => {
                mostrarErrores(listaErrores, ['No se pudo conectar con el servidor.']);
                if (confirmar) confirmar.disabled = false;
            });
    };

    const modalCrear = document.getElementById('modal-crear-cursada');
    if (modalCrear) {
        const form = document.getElementById('form-crear-cursada');
        const inputCodigo = document.getElementById('crear-codigo');
        const inputNombre = document.getElementById('crear-nombre');
        const hint = document.getElementById('crear-hint');
        const listaErrores = document.getElementById('crear-cursada-errores');
        const anioActual = new Date().getFullYear();
        const minimo = `${anioActual}-01-01`;
        form.querySelectorAll('input[type="date"]').forEach((input) => {
            input.min = minimo;
        });
        cablearCierre(modalCrear);

        document.querySelectorAll('.js-crear-cursada').forEach((btn) => {
            btn.addEventListener('click', () => {
                form.reset();
                inputNombre.readOnly = true;
                if (hint) hint.hidden = true;
                mostrarErrores(listaErrores, []);
                if (inputCodigo) inputCodigo.dispatchEvent(new Event('input'));
                abrirModal(modalCrear);
            });
        });

        form.addEventListener('submit', (evento) => {
            evento.preventDefault();
            const errores = validarAlta(form);
            mostrarErrores(listaErrores, errores);

            if (errores.length) return;

            enviarFormulario(form, listaErrores, anioDe(form.fecha_inicio.value));
        });

        if (inputCodigo && inputNombre) {
            const sincronizarNombre = () => {
                const nombre = materias[inputCodigo.value.trim().toUpperCase()];

                if (nombre) {
                    inputNombre.value = nombre;
                    inputNombre.readOnly = true;
                    if (hint) hint.hidden = true;
                } else {
                    inputNombre.value = '';
                    inputNombre.readOnly = false;
                    if (hint) hint.hidden = inputCodigo.value.trim() === '';
                }
            };

            inputCodigo.addEventListener('input', sincronizarNombre);
            inputCodigo.addEventListener('change', sincronizarNombre);
        }
    }

    const modalEditar = document.getElementById('modal-editar-cursada');
    if (modalEditar) {
        const titulo = document.getElementById('editar-cursada-titulo');
        const form = document.getElementById('form-editar-cursada');
        const listaErrores = document.getElementById('editar-cursada-errores');
        const anioActual = new Date().getFullYear();
        cablearCierre(modalEditar);

        document.querySelectorAll('.js-editar-cursada').forEach((btn) => {
            btn.addEventListener('click', () => {
                const anioGuardado = Number(btn.dataset.anio) || anioActual;
                const piso = Math.min(anioActual, anioGuardado);
                document.getElementById('editar-cursada-codigo').value = btn.dataset.codigo || '';
                document.getElementById('editar-cursada-nombre').value = btn.dataset.nombre || '';
                document.getElementById('editar-cursada-cuatrimestre').value = btn.dataset.cuatrimestre || '1';
                document.getElementById('editar-cursada-inicio').value = btn.dataset.inicio || '';
                document.getElementById('editar-cursada-fin').value = btn.dataset.fin || '';
                form.querySelectorAll('input[type="date"]').forEach((input) => {
                    input.min = `${piso}-01-01`;
                });
                form.dataset.anioOriginal = String(anioGuardado);
                titulo.textContent = `Editar cursada · ${btn.dataset.codigo || ''} ${btn.dataset.cuatrimestre || ''}C ${btn.dataset.anio || ''}`;
                form.action = btn.dataset.url || '#';
                mostrarErrores(listaErrores, []);
                abrirModal(modalEditar);
            });
        });

        form.addEventListener('submit', (evento) => {
            evento.preventDefault();
            const errores = validarAlta(form, form.dataset.anioOriginal);
            mostrarErrores(listaErrores, errores);

            if (errores.length) return;

            enviarFormulario(form, listaErrores, anioDe(form.fecha_inicio.value));
        });
    }
});
