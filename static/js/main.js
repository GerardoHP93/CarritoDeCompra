// static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    // Función para mostrar/ocultar el carrito lateral
    window.toggleCart = function() {
        const cartSidebar = document.querySelector('.cart-sidebar');
        if (cartSidebar) {
            cartSidebar.classList.toggle('active');
        }
    };

    // Mostrar alertas SweetAlert para los mensajes Django
    const messages = document.querySelectorAll('.messages .alert');
    if (messages.length > 0) {
        messages.forEach(function(message) {
            const messageType = message.classList.contains('alert-success') ? 'success' : 
                               message.classList.contains('alert-danger') ? 'error' :
                               message.classList.contains('alert-warning') ? 'warning' : 'info';
            
            // Eliminar el mensaje después de mostrar SweetAlert
            setTimeout(function() {
                message.style.opacity = '0';
                setTimeout(function() {
                    message.remove();
                }, 300);
            }, 5000);
        });
    }
});