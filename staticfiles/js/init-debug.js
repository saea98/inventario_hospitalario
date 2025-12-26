/**
 * Script de inicialización para agregar datos de debug al HTML
 * Se ejecuta después de que el DOM esté listo
 */

document.addEventListener('DOMContentLoaded', function() {
    // Obtener información del usuario desde el DOM
    const userElement = document.querySelector('nav.sidebar');
    
    if (userElement && window.debugLogger) {
        // Log de página cargada
        debugLogger.log('Página cargada completamente', null, 'SUCCESS');
        
        // Verificar items del menú
        const menuItems = document.querySelectorAll('.nav-link');
        debugLogger.log(`Se encontraron ${menuItems.length} items en el menú`, null, 'INFO');
        
        // Log de cada item del menú
        menuItems.forEach((item, index) => {
            const href = item.getAttribute('href');
            const text = item.textContent.trim();
            const isVisible = item.offsetParent !== null;
            
            if (isVisible && href) {
                debugLogger.logMenuItemVisibility(text, true);
            }
        });
        
        // Mostrar información de roles si está disponible
        const rolesText = document.body.textContent;
        if (rolesText.includes('Almacenero')) {
            debugLogger.logRoleCheck('Almacenero', true);
        }
    }
    
    // Interceptar clics en enlaces para logging
    document.addEventListener('click', function(e) {
        const link = e.target.closest('a[href]');
        if (link && link.href && !link.href.includes('javascript:')) {
            const currentUrl = window.location.pathname;
            const newUrl = new URL(link.href).pathname;
            
            if (currentUrl !== newUrl) {
                debugLogger.logNavigation(currentUrl, newUrl);
            }
        }
    });
    
    // Interceptar redirecciones
    const originalLocation = window.location;
    Object.defineProperty(window, 'location', {
        get: function() {
            return originalLocation;
        },
        set: function(value) {
            debugLogger.logNavigation(originalLocation.pathname, new URL(value).pathname);
            originalLocation.href = value;
        }
    });
});

// Mostrar ayuda en consola cuando se carga
console.log('%c💡 Tip: Abre la consola (F12) y escribe debugLogger.showHelp() para ver comandos disponibles', 'color: #ff9900; font-weight: bold; font-size: 12px;');
