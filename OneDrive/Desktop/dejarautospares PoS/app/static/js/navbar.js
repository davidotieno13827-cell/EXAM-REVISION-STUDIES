document.addEventListener('DOMContentLoaded', function () {
    var navCollapse = document.getElementById('navbarSupportedContent');
    var bsCollapse = navCollapse ? new bootstrap.Collapse(navCollapse, { toggle: false }) : null;
    document.querySelectorAll('.navbar-nav .nav-link').forEach(function (el) {
        el.addEventListener('click', function () {
            if (bsCollapse && window.getComputedStyle(document.querySelector('.navbar-toggler')).display !== 'none') {
                bsCollapse.hide();
            }
        });
    });
});
