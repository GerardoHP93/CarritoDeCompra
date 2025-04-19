// static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    // Función para mostrar/ocultar el carrito lateral
    window.toggleCart = function() {
        const cartSidebar = document.getElementById('cartSidebar');
        if (cartSidebar) {
            cartSidebar.classList.toggle('active');
            
            // Añadir/quitar clase al body para evitar scroll cuando el carrito está abierto
            document.body.classList.toggle('cart-open');
        }
    };

    // Cerrar carrito si se hace clic fuera
    document.addEventListener('click', function(event) {
        const cartSidebar = document.getElementById('cartSidebar');
        const cartButton = document.querySelector('.cart-button');
        
        if (cartSidebar && cartSidebar.classList.contains('active') && 
            !cartSidebar.contains(event.target) && 
            cartButton && !cartButton.contains(event.target)) {
            toggleCart();
        }
    });

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

// Función global para mostrar notificación Toast
window.showToast = function(message, type = 'info') {
    // Si SweetAlert2 está disponible
    if (typeof Swal !== 'undefined') {
        const Toast = Swal.mixin({
            toast: true,
            position: 'top-end',
            showConfirmButton: false,
            timer: 3000,
            timerProgressBar: true,
            didOpen: (toast) => {
                toast.addEventListener('mouseenter', Swal.stopTimer)
                toast.addEventListener('mouseleave', Swal.resumeTimer)
            }
        });
        
        Toast.fire({
            icon: type,
            title: message
        });
    } else {
        // Crear un toast manualmente si SweetAlert2 no está disponible
        const toastContainer = document.getElementById('toast-container') || createToastContainer();
        const toast = document.createElement('div');
        toast.className = `toast-notification toast-${type}`;
        toast.textContent = message;
        
        toastContainer.appendChild(toast);
        
        // Eliminar después de 3 segundos
        setTimeout(() => {
            toast.classList.add('hide');
            setTimeout(() => {
                toast.remove();
            }, 300);
        }, 3000);
    }
};

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
    return container;
}

// Funciones para actualizar el carrito via AJAX
document.addEventListener('DOMContentLoaded', function() {
    // Manejar el eliminar productos desde sidebar
    document.querySelectorAll('.remove-item-btn').forEach(button => {
        button.addEventListener('click', function() {
            const productId = this.getAttribute('data-product-id');
            const cartItem = this.closest('.cart-item');
            
            // Petición AJAX para eliminar
            fetch(`/cart/remove-ajax/${productId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Actualizar contador de carrito
                    updateCartCounter(data.cart_count);
                    
                    // Actualizar total
                    const totalElement = document.querySelector('.cart-total .fw-bold');
                    if (totalElement) {
                        totalElement.textContent = `$${data.cart_total.toFixed(2)}`;
                    }
                    
                    // Eliminar elemento del DOM
                    cartItem.remove();
                    
                    // Verificar si el carrito quedó vacío
                    const cartItems = document.querySelectorAll('.cart-item');
                    if (cartItems.length === 0) {
                        // Mostrar mensaje de carrito vacío
                        const cartBody = document.querySelector('.cart-sidebar-body');
                        cartBody.innerHTML = `
                            <div class="cart-empty text-center py-5">
                                <i class="bi bi-cart3 display-4 text-muted"></i>
                                <p class="mt-3">Tu carrito está vacío</p>
                                <a href="/products/" class="btn btn-outline-primary btn-sm">
                                    Ir a la tienda
                                </a>
                            </div>
                        `;
                        
                        // Ocultar footer
                        const cartFooter = document.querySelector('.cart-sidebar-footer');
                        if (cartFooter) {
                            cartFooter.innerHTML = '';
                        }
                    }
                    
                    // Mostrar notificación Toast
                    showToast('Producto eliminado', 'success');
                } else {
                    showToast('Error al eliminar producto', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('Error al procesar la solicitud', 'error');
            });
        });
    });
    
    // Manejar cambios en cantidad desde sidebar
    document.querySelectorAll('.sidebar-quantity').forEach(input => {
        input.addEventListener('change', function() {
            const productId = this.getAttribute('data-product-id');
            const quantity = this.value;
            const form = this.closest('form');
            
            // Construir FormData
            const formData = new FormData(form);
            
            // Petición AJAX para actualizar
            fetch(`/cart/update-ajax/${productId}/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Actualizar contador de carrito
                    updateCartCounter(data.cart_count);
                    
                    // Actualizar total
                    const totalElement = document.querySelector('.cart-total .fw-bold');
                    if (totalElement) {
                        totalElement.textContent = `$${data.cart_total.toFixed(2)}`;
                    }
                    
                    // NO mostrar notificación al actualizar cantidad
                } else if (data.status === 'warning') {
                    // Revertir al valor máximo y mostrar advertencia solo para errores de stock
                    this.value = data.max_stock || 1;
                    showToast(data.message, 'warning');
                } else {
                    showToast('Error al actualizar carrito', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('Error al procesar la solicitud', 'error');
            });
        });
    });
    
    // Función para actualizar el contador del carrito
    function updateCartCounter(count) {
        const counter = document.querySelector('.cart-button .badge');
        if (counter) {
            counter.textContent = count > 0 ? count : '';
        }
    }
});