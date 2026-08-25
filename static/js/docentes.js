document.addEventListener('DOMContentLoaded', function () {
    const defaultsEl = document.getElementById('permisos-por-cargo');
    let porCargo = {};
    if (defaultsEl) {
        try { porCargo = JSON.parse(defaultsEl.textContent || '{}'); } catch (error) { porCargo = {}; }
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

    const checks = () => Array.from(document.querySelectorAll('#editar-docente-permisos input[type="checkbox"]'));

    function pintarChecks(codigos, bloquear) {
        const set = new Set(codigos || []);
        checks().forEach((input) => {
            input.checked = set.has(input.value);
            input.disabled = !!bloquear;
        });
        const nota = document.getElementById('editar-docente-permisos-nota');
        if (nota) nota.hidden = !bloquear;
    }

    const modalEditar = document.getElementById('modal-editar-docente');
    if (modalEditar) {
        const titulo = document.getElementById('editar-docente-titulo');
        const form = document.getElementById('form-editar-docente');
        const inputNombre = document.getElementById('editar-docente-nombre');
        const inputApellido = document.getElementById('editar-docente-apellido');
        const inputEmail = document.getElementById('editar-docente-email');
        const inputRol = document.getElementById('editar-docente-rol');
        cablearCierre(modalEditar);

        document.querySelectorAll('.js-editar-docente').forEach((btn) => {
            btn.addEventListener('click', () => {
                inputNombre.value = btn.dataset.nombre || '';
                inputApellido.value = btn.dataset.apellido || '';
                inputEmail.value = btn.dataset.email || '';
                inputRol.value = btn.dataset.rol || 'Ayudante';
                titulo.textContent = `${btn.dataset.nombre || ''} ${btn.dataset.apellido || ''}`.trim();
                form.action = btn.dataset.url || '#';
                let permisos = [];
                try { permisos = JSON.parse(btn.dataset.permisos || '[]'); } catch (error) { permisos = []; }
                pintarChecks(permisos, btn.dataset.rol === 'Profesor');
                abrirModal(modalEditar);
            });
        });

        if (inputRol) {
            inputRol.addEventListener('change', () => {
                const rol = inputRol.value;
                pintarChecks(porCargo[rol] || [], rol === 'Profesor');
            });
        }
    }

    const modalDesactivar = document.getElementById('modal-desactivar-docente');
    if (modalDesactivar) {
        const texto = document.getElementById('desactivar-docente-texto');
        const form = document.getElementById('form-desactivar-docente');
        cablearCierre(modalDesactivar);
        document.querySelectorAll('.js-desactivar-docente').forEach((btn) => {
            btn.addEventListener('click', () => {
                texto.innerHTML = `¿Desactivar a <strong>${btn.dataset.apellido}, ${btn.dataset.nombre}</strong>? Va a quedar inactivo y un profesor puede reactivarlo.`;
                form.action = btn.dataset.url || '#';
                abrirModal(modalDesactivar);
            });
        });
    }
});