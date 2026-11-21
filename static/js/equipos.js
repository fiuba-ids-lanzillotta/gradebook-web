document.addEventListener('DOMContentLoaded', function () {
    const busqueda = document.getElementById('equipos-q');
    const tutor = document.getElementById('equipos-tutor');

    const evaluacion = document.getElementById('equipos-evaluacion');

    if (busqueda && tutor) {
        const aplicar = () => {
            const texto = busqueda.value.trim().toLowerCase();
            const tutorId = tutor.value;
            const evaluacionNombre = evaluacion ? evaluacion.value : '';
            const filas = document.querySelectorAll('.equipos__tabla tbody tr');
            let visibles = 0;

            filas.forEach((fila) => {
                const nombre = (fila.dataset.nombre || '').toLowerCase();
                const coincideNombre = !texto || nombre.includes(texto);
                const coincideTutor = !tutorId || (tutorId === 'sin' ? !fila.dataset.tutor : fila.dataset.tutor === tutorId);
                const coincideEvaluacion = !evaluacionNombre || fila.dataset.evaluacion === evaluacionNombre;
                const visible = coincideNombre && coincideTutor && coincideEvaluacion;
                fila.hidden = !visible;
                if (visible) visibles += 1;
            });

            const aviso = document.getElementById('equipos-sin-resultado');
            if (aviso) aviso.hidden = visibles !== 0;
        };

        busqueda.addEventListener('input', aplicar);
        tutor.addEventListener('change', aplicar);
        if (evaluacion) evaluacion.addEventListener('change', aplicar);
    }

    const nombre = document.getElementById('equipo-nombre');
    const editar = document.getElementById('equipo-editar-nombre');
    const formulario = document.getElementById('equipo-renombrar');

    if (editar && nombre && formulario) {
        editar.addEventListener('click', () => {
            nombre.hidden = true;
            editar.hidden = true;
            formulario.hidden = false;
            const campo = formulario.querySelector('input');
            if (campo) campo.focus();
        });
    }

    const datosAlumnos = document.getElementById('equipo-candidatos');
    const buscarAlumno = document.getElementById('equipo-alumno');
    const listaAlumnos = document.getElementById('equipo-alumno-lista');
    const alumnoId = document.getElementById('equipo-alumno-id');
    const alumnoPadron = document.getElementById('equipo-alumno-padron');
    const agregarAlumno = document.getElementById('equipo-alumno-agregar');

    if (datosAlumnos && buscarAlumno && listaAlumnos && (alumnoId || alumnoPadron)) {
        const LIMITE = 6;
        let candidatos = [];
        let indiceActivo = 0;
        let consultaPropia = false;

        try {
            candidatos = JSON.parse(datosAlumnos.textContent || '[]');
        } catch (error) {
            candidatos = [];
        }

        const etiqueta = (fila) => `${fila.apellido || ''} ${fila.nombre || ''} · ${fila.padron || ''}`.trim();

        const coincide = (fila, consulta) => {
            const texto = `${fila.apellido || ''} ${fila.nombre || ''} ${fila.padron || ''}`.toLowerCase();

            return consulta.split(/\s+/).filter(Boolean).every((parte) => texto.includes(parte));
        };

        const cerrarLista = () => {
            listaAlumnos.hidden = true;
            listaAlumnos.replaceChildren();
            buscarAlumno.setAttribute('aria-expanded', 'false');
        };

        const elegir = (fila) => {
            if (alumnoId) alumnoId.value = fila.id;
            if (alumnoPadron) alumnoPadron.value = fila.padron || '';
            buscarAlumno.value = etiqueta(fila);
            if (agregarAlumno) agregarAlumno.disabled = false;
            cerrarLista();
        };

        const visibles = () => {
            const consulta = consultaPropia ? buscarAlumno.value.trim().toLowerCase() : '';
            const base = consulta ? candidatos.filter((fila) => coincide(fila, consulta)) : candidatos;

            return base.slice(0, LIMITE);
        };

        const pintar = () => {
            const filas = visibles();
            listaAlumnos.replaceChildren();
            indiceActivo = 0;

            if (!filas.length) {
                const vacio = document.createElement('li');
                vacio.className = 'equipo__alumno-vacio';
                vacio.textContent = 'Sin coincidencias';
                listaAlumnos.appendChild(vacio);
            }

            filas.forEach((fila, indice) => {
                const item = document.createElement('li');
                const boton = document.createElement('button');
                boton.type = 'button';
                boton.className = 'equipo__alumno-opcion' + (indice === 0 ? ' is-activa' : '');
                boton.setAttribute('role', 'option');
                boton.textContent = etiqueta(fila);
                boton.addEventListener('mousedown', (evento) => {
                    evento.preventDefault();
                    elegir(fila);
                });
                item.appendChild(boton);
                listaAlumnos.appendChild(item);
            });

            listaAlumnos.hidden = false;
            buscarAlumno.setAttribute('aria-expanded', 'true');
        };

        buscarAlumno.addEventListener('focus', () => {
            consultaPropia = false;
            pintar();
        });

        buscarAlumno.addEventListener('input', () => {
            consultaPropia = true;
            if (alumnoId) alumnoId.value = '';
            if (alumnoPadron) alumnoPadron.value = '';
            if (agregarAlumno) agregarAlumno.disabled = true;
            pintar();
        });

        buscarAlumno.addEventListener('keydown', (evento) => {
            const botones = listaAlumnos.querySelectorAll('.equipo__alumno-opcion');

            if (evento.key === 'ArrowDown' && botones.length) {
                evento.preventDefault();
                indiceActivo = Math.min(indiceActivo + 1, botones.length - 1);
            } else if (evento.key === 'ArrowUp' && botones.length) {
                evento.preventDefault();
                indiceActivo = Math.max(indiceActivo - 1, 0);
            } else if (evento.key === 'Enter') {
                evento.preventDefault();
                const filas = visibles();
                if (filas[indiceActivo]) elegir(filas[indiceActivo]);
                return;
            } else if (evento.key === 'Escape') {
                cerrarLista();
                return;
            } else {
                return;
            }

            botones.forEach((boton, indice) => {
                boton.classList.toggle('is-activa', indice === indiceActivo);
            });
        });

        buscarAlumno.addEventListener('blur', cerrarLista);
    }

    const modal = document.getElementById('modal-transferir');

    if (!modal) return;

    const cerrar = () => {
        modal.classList.remove('is-open');
        modal.setAttribute('aria-hidden', 'true');
    };

    modal.querySelectorAll('[data-close]').forEach((elemento) => {
        elemento.addEventListener('click', cerrar);
    });

    document.querySelectorAll('.js-transferir').forEach((boton) => {
        boton.addEventListener('click', () => {
            const alumno = document.getElementById('transferir-alumno');
            const form = document.getElementById('form-transferir');
            if (alumno) alumno.textContent = `${boton.dataset.nombre || ''} (${boton.dataset.padron || ''})`.trim();
            if (form) form.action = boton.dataset.url || '#';
            modal.classList.add('is-open');
            modal.setAttribute('aria-hidden', 'false');
        });
    });
});
