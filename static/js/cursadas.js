document.addEventListener('DOMContentLoaded', function () {
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

    const modalCrear = document.getElementById('modal-crear-cursada');
    if (modalCrear) {
        const form = document.getElementById('form-crear-cursada');
        const inputCodigo = document.getElementById('crear-codigo');
        const inputNombre = document.getElementById('crear-nombre');
        const hint = document.getElementById('crear-hint');
        cablearCierre(modalCrear);

        document.querySelectorAll('.js-crear-cursada').forEach((btn) => {
            btn.addEventListener('click', () => {
                form.reset();
                inputNombre.readOnly = true;
                if (hint) hint.hidden = true;
                abrirModal(modalCrear);
            });
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
        cablearCierre(modalEditar);

        document.querySelectorAll('.js-editar-cursada').forEach((btn) => {
            btn.addEventListener('click', () => {
                document.getElementById('editar-cursada-codigo').value = btn.dataset.codigo || '';
                document.getElementById('editar-cursada-nombre').value = btn.dataset.nombre || '';
                document.getElementById('editar-cursada-anio').value = btn.dataset.anio || '';
                document.getElementById('editar-cursada-cuatrimestre').value = btn.dataset.cuatrimestre || '1';
                document.getElementById('editar-cursada-inicio').value = btn.dataset.inicio || '';
                document.getElementById('editar-cursada-fin').value = btn.dataset.fin || '';
                titulo.textContent = `Editar cursada · ${btn.dataset.codigo || ''} ${btn.dataset.cuatrimestre || ''}C ${btn.dataset.anio || ''}`;
                form.action = btn.dataset.url || '#';
                abrirModal(modalEditar);
            });
        });
    }
});
