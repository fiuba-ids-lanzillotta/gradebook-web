document.addEventListener('DOMContentLoaded', function () {
    const mostrar = document.getElementById('mostrar-crear');
    const alta = document.getElementById('equipo-crear');
    const vacio = document.getElementById('equipo-vacio');

    if (mostrar && alta && vacio) {
        mostrar.addEventListener('click', () => {
            vacio.hidden = true;
            alta.hidden = false;
        });
    }

    const sumar = document.getElementById('sumar-padron');
    const lista = document.getElementById('padrones');

    if (sumar && lista) {
        let numero = 1;

        sumar.addEventListener('click', () => {
            numero += 1;
            const campo = document.createElement('label');
            campo.textContent = `Integrante ${numero}`;
            const input = document.createElement('input');
            input.type = 'text';
            input.name = 'padron';
            input.placeholder = 'Padrón';
            input.autocomplete = 'off';
            campo.appendChild(input);
            lista.appendChild(campo);
        });
    }

    const abrirSalir = document.getElementById('abrir-salir');
    const modalSalir = document.getElementById('modal-salir');
    const cerrarSalir = document.getElementById('cerrar-salir');

    if (abrirSalir && modalSalir) {
        abrirSalir.addEventListener('click', () => { modalSalir.hidden = false; });
    }
    if (cerrarSalir && modalSalir) {
        cerrarSalir.addEventListener('click', () => { modalSalir.hidden = true; });
    }

    const nombre = document.getElementById('equipo-nombre');
    const editar = document.getElementById('equipo-editar');
    const formulario = document.getElementById('equipo-renombrar');

    if (nombre && editar && formulario) {
        editar.addEventListener('click', () => {
            nombre.hidden = true;
            editar.hidden = true;
            formulario.hidden = false;
            const campo = formulario.querySelector('input');
            if (campo) campo.focus();
        });
    }
});
