document.addEventListener('DOMContentLoaded', function () {
    var modal = document.getElementById('modal-cerrar');
    var abrir = document.querySelector('.js-cerrar-clase');
    if (!modal || !abrir) return;
    abrir.addEventListener('click', function () {
        if (abrir.disabled) return;
        modal.classList.add('is-open');
    });
    modal.querySelectorAll('[data-close]').forEach(function (el) {
        el.addEventListener('click', function () {
            modal.classList.remove('is-open');
            modal.setAttribute('aria-hidden', 'true');
        });
    });
});