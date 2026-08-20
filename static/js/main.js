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
    const password = document.getElementById('password');
    const togglePass = document.getElementById('toggle-password');

    if (password && togglePass) {
        togglePass.addEventListener('click', () => {
            const visible = password.type === 'text';
            password.type = visible ? 'password' : 'text';
            togglePass.setAttribute('aria-label', visible ? 'Mostrar contraseña' : 'Ocultar contraseña');

            const eyeOpen = togglePass.querySelector('.login__eye--open');
            const eyeShut = togglePass.querySelector('.login__eye--shut');
            if (eyeOpen) eyeOpen.hidden = !visible;
            if (eyeShut) eyeShut.hidden = visible;
        });
    }
});
