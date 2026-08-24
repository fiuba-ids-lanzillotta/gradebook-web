document.addEventListener('DOMContentLoaded', function () {
    // --- Modal de edición de item ---
    const editModal = document.getElementById('edit-item-modal');
    if (editModal) {
        const nombre = document.getElementById('edit-nombre');
        const descripcion = document.getElementById('edit-descripcion');
        const activo = document.getElementById('edit-activo');
        const form = document.getElementById('edit-item-form');

        const openEdit = (btn) => {
            nombre.value = btn.dataset.nombre || '';
            descripcion.value = btn.dataset.descripcion || '';
            activo.checked = btn.dataset.activo === '1';
            if (form) form.action = btn.dataset.editUrl || '#';
            editModal.classList.add('is-open');
            editModal.setAttribute('aria-hidden', 'false');
        };
        const closeEdit = () => {
            editModal.classList.remove('is-open');
            editModal.setAttribute('aria-hidden', 'true');
        };

        document.querySelectorAll('.js-edit-item').forEach((btn) => {
            btn.addEventListener('click', () => openEdit(btn));
        });
        editModal.querySelectorAll('[data-close]').forEach((el) => {
            el.addEventListener('click', closeEdit);
        });
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') closeEdit();
        });
    }

    // --- Modal de confirmación de borrado ---
    const deleteModal = document.getElementById('delete-item-modal');
    if (deleteModal) {
        const deleteName = document.getElementById('delete-item-nombre');
        const deleteForm = document.getElementById('delete-item-form');

        const openDelete = (btn) => {
            if (deleteName) deleteName.textContent = btn.dataset.nombre || 'este item';
            if (deleteForm) deleteForm.action = btn.dataset.deleteUrl || '#';
            deleteModal.classList.add('is-open');
            deleteModal.setAttribute('aria-hidden', 'false');
        };
        const closeDelete = () => {
            deleteModal.classList.remove('is-open');
            deleteModal.setAttribute('aria-hidden', 'true');
        };

        document.querySelectorAll('.js-delete-item').forEach((btn) => {
            btn.addEventListener('click', () => openDelete(btn));
        });
        deleteModal.querySelectorAll('[data-close]').forEach((el) => {
            el.addEventListener('click', closeDelete);
        });
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') closeDelete();
        });
    }

    // --- Mostrar / ocultar contraseña en el login ---
    const csvInput = document.getElementById('csv-input');
    const csvNombre = document.getElementById('csv-nombre');
    if (csvInput && csvNombre) {
        csvInput.addEventListener('change', () => {
            csvNombre.textContent = csvInput.files.length ? csvInput.files[0].name : 'Subir archivo csv';
        });
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

    const modalEditar = document.getElementById('modal-editar');
    if (modalEditar) {
        const titulo = document.getElementById('editar-titulo');
        const form = document.getElementById('form-editar');
        cablearCierre(modalEditar);
        document.querySelectorAll('.js-editar').forEach((btn) => {
            btn.addEventListener('click', () => {
                document.getElementById('editar-nombre').value = btn.dataset.nombre || '';
                document.getElementById('editar-apellido').value = btn.dataset.apellido || '';
                document.getElementById('editar-email').value = btn.dataset.email || '';
                document.getElementById('editar-padron').value = btn.dataset.padron || '';
                titulo.textContent = `${btn.dataset.nombre || ''} ${btn.dataset.apellido || ''} ${btn.dataset.padron || ''}`;
                form.action = btn.dataset.url || '#';
                abrirModal(modalEditar);
            });
        });
    }

    const modalAbandonar = document.getElementById('modal-abandonar');
    if (modalAbandonar) {
        const texto = document.getElementById('abandonar-texto');
        const form = document.getElementById('form-abandonar');
        cablearCierre(modalAbandonar);
        document.querySelectorAll('.js-abandonar').forEach((btn) => {
            btn.addEventListener('click', () => {
                texto.innerHTML = `¿Desea <strong>marcar que abandonó</strong> ${btn.dataset.nombre} ${btn.dataset.apellido}, ${btn.dataset.padron} la materia?`;
                form.action = btn.dataset.url || '#';
                abrirModal(modalAbandonar);
            });
        });
    }

    const modalBaja = document.getElementById('modal-baja');
    if (modalBaja) {
        const texto = document.getElementById('baja-texto');
        const form = document.getElementById('form-baja');
        cablearCierre(modalBaja);
        document.querySelectorAll('.js-baja').forEach((btn) => {
            btn.addEventListener('click', () => {
                texto.innerHTML = `¿Desea <strong>dar de baja</strong> a ${btn.dataset.nombre} ${btn.dataset.apellido}, ${btn.dataset.padron} de la materia?`;
                form.action = btn.dataset.url || '#';
                form.reset();
                abrirModal(modalBaja);
            });
        });
    }

    const modalMotivos = document.getElementById('modal-motivos');
    if (modalMotivos) {
        const lista = document.getElementById('motivos-lista');
        cablearCierre(modalMotivos);
        document.querySelectorAll('.js-motivos').forEach((btn) => {
            btn.addEventListener('click', () => {
                let motivos = [];
                try { motivos = JSON.parse(btn.dataset.motivos || '[]'); } catch (error) { motivos = []; }
                lista.innerHTML = '';
                motivos.forEach((item) => {
                    const li = document.createElement('li');
                    li.innerHTML = `<strong>${item.cuatrimestre}C ${item.anio}</strong>${item.motivo || 'Sin motivo cargado'}`;
                    lista.appendChild(li);
                });
                if (btn.dataset.estado === 'abandono') {
                    const li = document.createElement('li');
                    li.innerHTML = '<strong>Cuatrimestre actual</strong>Abandonó la materia.';
                    lista.appendChild(li);
                }
                if (!lista.children.length) {
                    const li = document.createElement('li');
                    li.textContent = 'No hay razones registradas.';
                    lista.appendChild(li);
                }
                abrirModal(modalMotivos);
            });
        });
    }

    document.addEventListener('keydown', (e) => {
        if (e.key !== 'Escape') return;
        document.querySelectorAll('.modal.is-open').forEach((modal) => cerrarModal(modal));
    });

    document.querySelectorAll('.login__toggle-pass').forEach((togglePass) => {
        const field = togglePass.closest('.login__field');
        const input = field ? field.querySelector('input') : null;
        if (!input) return;

        togglePass.addEventListener('click', () => {
            const visible = input.type === 'text';
            input.type = visible ? 'password' : 'text';
            togglePass.setAttribute('aria-label', visible ? 'Mostrar contraseña' : 'Ocultar contraseña');

            const eyeOpen = togglePass.querySelector('.login__eye--open');
            const eyeShut = togglePass.querySelector('.login__eye--shut');
            if (eyeOpen) eyeOpen.hidden = !visible;
            if (eyeShut) eyeShut.hidden = visible;
        });
    });
});