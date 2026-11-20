document.addEventListener('DOMContentLoaded', function () {
    const form = document.querySelector('.cursada-filtro');
    const datos = document.getElementById('cursadas-filtro-datos');

    if (!form || !datos) return;

    const LIMITE = 6;
    let cursadas = [];

    try {
        cursadas = JSON.parse(datos.textContent || '[]');
    } catch (error) {
        cursadas = [];
    }

    const campo = form.querySelector('.cursada-filtro__campo');
    const input = document.getElementById('cursada-filtro-buscar');
    const lista = document.getElementById('cursada-filtro-lista');
    const oculto = document.getElementById('cursada-filtro-id');
    const marca = form.querySelector('.cursada-filtro__marca');
    const etiquetaElegida = input.value;
    let indiceActivo = 0;
    let consultaPropia = false;

    const etiqueta = (fila) => {
        const codigo = fila.codigo ? ` · ${fila.codigo}` : '';

        return `${fila.cuatrimestre}C ${fila.anio}${codigo}`;
    };

    const coincide = (fila, consulta) => {
        const texto = etiqueta(fila).toLowerCase();

        return consulta.split(/\s+/).filter(Boolean).every((parte) => texto.includes(parte));
    };

    const conVigentePrimero = (filas) => {
        const vigentes = filas.filter((fila) => fila.vigente);
        const resto = filas.filter((fila) => !fila.vigente);

        return vigentes.concat(resto);
    };

    const visibles = () => {
        const consulta = consultaPropia ? input.value.trim().toLowerCase() : '';
        const base = consulta ? cursadas.filter((fila) => coincide(fila, consulta)) : cursadas;

        return conVigentePrimero(base).slice(0, LIMITE);
    };

    const cerrar = () => {
        lista.hidden = true;
        lista.replaceChildren();
        input.setAttribute('aria-expanded', 'false');
    };

    const pintar = () => {
        const filas = visibles();
        lista.replaceChildren();
        indiceActivo = 0;

        if (!filas.length) {
            const vacio = document.createElement('li');
            vacio.className = 'cursada-filtro__vacio';
            vacio.textContent = 'Sin coincidencias';
            lista.appendChild(vacio);
        }

        filas.forEach((fila, indice) => {
            const opcion = document.createElement('li');
            const boton = document.createElement('button');
            boton.type = 'button';
            boton.className = 'cursada-filtro__opcion' + (indice === 0 ? ' is-activa' : '');
            boton.setAttribute('role', 'option');

            const texto = document.createElement('span');
            texto.textContent = etiqueta(fila);
            boton.appendChild(texto);

            if (fila.vigente) {
                const punto = document.createElement('span');
                punto.className = 'cursada-filtro__marca';
                punto.title = 'Vigente';
                boton.appendChild(punto);
            }

            boton.addEventListener('mousedown', (evento) => {
                evento.preventDefault();
                elegir(fila);
            });
            opcion.appendChild(boton);
            lista.appendChild(opcion);
        });

        lista.hidden = false;
        input.setAttribute('aria-expanded', 'true');
    };

    const marcarActiva = () => {
        const botones = lista.querySelectorAll('.cursada-filtro__opcion');
        botones.forEach((boton, indice) => {
            boton.classList.toggle('is-activa', indice === indiceActivo);
        });
    };

    const elegir = (fila) => {
        oculto.value = fila.id;
        input.value = etiqueta(fila);
        if (marca) marca.hidden = !fila.vigente;
        form.submit();
    };

    campo.addEventListener('click', (evento) => {
        if (evento.target === input) return;

        input.focus();
        pintar();
    });

    input.addEventListener('focus', () => {
        consultaPropia = false;
        input.select();
        pintar();
    });

    input.addEventListener('input', () => {
        consultaPropia = true;
        pintar();
    });

    input.addEventListener('keydown', (evento) => {
        const botones = lista.querySelectorAll('.cursada-filtro__opcion');

        if (evento.key === 'ArrowDown' && botones.length) {
            evento.preventDefault();
            indiceActivo = Math.min(indiceActivo + 1, botones.length - 1);
            marcarActiva();
        } else if (evento.key === 'ArrowUp' && botones.length) {
            evento.preventDefault();
            indiceActivo = Math.max(indiceActivo - 1, 0);
            marcarActiva();
        } else if (evento.key === 'Enter') {
            evento.preventDefault();
            const filas = visibles();
            if (filas[indiceActivo]) elegir(filas[indiceActivo]);
        } else if (evento.key === 'Escape') {
            input.value = etiquetaElegida;
            cerrar();
        }
    });

    input.addEventListener('blur', () => {
        input.value = etiquetaElegida;
        cerrar();
    });
});
