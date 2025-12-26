/**
 * Sistema de Logging para Depuración en Consola del Navegador
 * Ayuda a rastrear acceso a roles, permisos y navegación
 */

class DebugLogger {
    constructor() {
        this.enabled = true;
        this.logLevel = 'DEBUG'; // DEBUG, INFO, WARNING, ERROR
        this.logs = [];
        this.maxLogs = 500;
        
        // Estilos para consola
        this.styles = {
            debug: 'color: #0066cc; font-weight: bold;',
            info: 'color: #009900; font-weight: bold;',
            warning: 'color: #ff9900; font-weight: bold;',
            error: 'color: #cc0000; font-weight: bold;',
            success: 'color: #00cc00; font-weight: bold;',
            rol: 'color: #9933cc; font-weight: bold; background: #f0f0f0; padding: 2px 4px;',
            url: 'color: #0066cc; text-decoration: underline;',
            user: 'color: #ff6600; font-weight: bold;'
        };
        
        this.init();
    }
    
    init() {
        console.log('%c🔍 Sistema de Logging Iniciado', this.styles.info);
        this.logUserInfo();
        this.logPageInfo();
        this.setupGlobalErrorHandler();
    }
    
    /**
     * Log de información del usuario
     */
    logUserInfo() {
        const userElement = document.querySelector('[data-user-id]');
        const userUsername = document.querySelector('[data-user-username]');
        const userRoles = document.querySelector('[data-user-roles]');
        
        if (userElement || userUsername) {
            const userId = userElement?.getAttribute('data-user-id') || 'Desconocido';
            const username = userUsername?.getAttribute('data-user-username') || 'Desconocido';
            const roles = userRoles?.getAttribute('data-user-roles') || 'Sin roles';
            
            console.log('%c👤 Usuario:', this.styles.user, username);
            console.log('%c🔐 Roles:', this.styles.rol, roles);
            console.log('%c🆔 ID:', this.styles.debug, userId);
        }
    }
    
    /**
     * Log de información de la página
     */
    logPageInfo() {
        const currentUrl = window.location.pathname;
        const pageTitle = document.title;
        
        console.log('%c📄 Página:', this.styles.url, currentUrl);
        console.log('%c📋 Título:', this.styles.info, pageTitle);
    }
    
    /**
     * Log de acceso a una vista
     */
    logViewAccess(viewName, allowed = true) {
        const status = allowed ? '✅ PERMITIDO' : '❌ DENEGADO';
        const style = allowed ? this.styles.success : this.styles.error;
        
        console.log(`%c${status} Vista: ${viewName}`, style);
        
        this.addLog({
            type: 'VIEW_ACCESS',
            message: `${status}: ${viewName}`,
            timestamp: new Date(),
            allowed: allowed
        });
    }
    
    /**
     * Log de validación de rol
     */
    logRoleCheck(roleName, hasRole = true) {
        const status = hasRole ? '✅' : '❌';
        const message = `${status} Rol ${roleName}: ${hasRole ? 'TIENE' : 'NO TIENE'}`;
        
        console.log(`%c${message}`, hasRole ? this.styles.success : this.styles.warning);
        
        this.addLog({
            type: 'ROLE_CHECK',
            role: roleName,
            has: hasRole,
            timestamp: new Date()
        });
    }
    
    /**
     * Log de validación de permiso
     */
    logPermissionCheck(permissionName, hasPermission = true) {
        const status = hasPermission ? '✅' : '❌';
        const message = `${status} Permiso ${permissionName}: ${hasPermission ? 'TIENE' : 'NO TIENE'}`;
        
        console.log(`%c${message}`, hasPermission ? this.styles.success : this.styles.warning);
        
        this.addLog({
            type: 'PERMISSION_CHECK',
            permission: permissionName,
            has: hasPermission,
            timestamp: new Date()
        });
    }
    
    /**
     * Log de elemento del menú
     */
    logMenuItemVisibility(menuItemName, visible = true) {
        const status = visible ? '👁️ VISIBLE' : '👁️‍🗨️ OCULTO';
        const style = visible ? this.styles.success : this.styles.warning;
        
        console.log(`%c${status} Menú: ${menuItemName}`, style);
        
        this.addLog({
            type: 'MENU_ITEM',
            item: menuItemName,
            visible: visible,
            timestamp: new Date()
        });
    }
    
    /**
     * Log de navegación
     */
    logNavigation(fromUrl, toUrl) {
        console.log(`%c🔀 Navegación: ${fromUrl} → ${toUrl}`, this.styles.info);
        
        this.addLog({
            type: 'NAVIGATION',
            from: fromUrl,
            to: toUrl,
            timestamp: new Date()
        });
    }
    
    /**
     * Log de error
     */
    logError(errorMessage, errorDetails = null) {
        console.error(`%c❌ ERROR: ${errorMessage}`, this.styles.error);
        
        if (errorDetails) {
            console.error('%c📋 Detalles:', this.styles.debug, errorDetails);
        }
        
        this.addLog({
            type: 'ERROR',
            message: errorMessage,
            details: errorDetails,
            timestamp: new Date()
        });
    }
    
    /**
     * Log de advertencia
     */
    logWarning(warningMessage, details = null) {
        console.warn(`%c⚠️ ADVERTENCIA: ${warningMessage}`, this.styles.warning);
        
        if (details) {
            console.warn('%c📋 Detalles:', this.styles.debug, details);
        }
        
        this.addLog({
            type: 'WARNING',
            message: warningMessage,
            details: details,
            timestamp: new Date()
        });
    }
    
    /**
     * Log genérico
     */
    log(message, details = null, level = 'INFO') {
        const style = this.styles[level.toLowerCase()] || this.styles.info;
        console.log(`%c${message}`, style);
        
        if (details) {
            console.log('%c📋 Detalles:', this.styles.debug, details);
        }
        
        this.addLog({
            type: level,
            message: message,
            details: details,
            timestamp: new Date()
        });
    }
    
    /**
     * Agregar log al historial
     */
    addLog(logEntry) {
        this.logs.push(logEntry);
        
        // Mantener el tamaño máximo del historial
        if (this.logs.length > this.maxLogs) {
            this.logs.shift();
        }
    }
    
    /**
     * Mostrar tabla de roles del usuario
     */
    showUserRolesTable() {
        const rolesElement = document.querySelector('[data-user-roles]');
        if (rolesElement) {
            const roles = rolesElement.getAttribute('data-user-roles').split(',');
            console.table(roles.map(role => ({ Rol: role.trim() })));
        }
    }
    
    /**
     * Mostrar tabla de items del menú
     */
    showMenuItemsTable() {
        const menuItems = [];
        document.querySelectorAll('[data-menu-item]').forEach(item => {
            menuItems.push({
                'Nombre': item.getAttribute('data-menu-item'),
                'URL': item.getAttribute('href'),
                'Visible': item.offsetParent !== null ? 'Sí' : 'No'
            });
        });
        
        if (menuItems.length > 0) {
            console.table(menuItems);
        } else {
            console.warn('No se encontraron items de menú con atributo data-menu-item');
        }
    }
    
    /**
     * Mostrar historial de logs
     */
    showLogs() {
        console.log('%c📊 HISTORIAL DE LOGS', this.styles.info);
        console.table(this.logs);
    }
    
    /**
     * Exportar logs como JSON
     */
    exportLogs() {
        const logsJson = JSON.stringify(this.logs, null, 2);
        console.log('%c📥 Logs exportados (copia el siguiente JSON):', this.styles.info);
        console.log(logsJson);
        return logsJson;
    }
    
    /**
     * Limpiar logs
     */
    clearLogs() {
        this.logs = [];
        console.log('%c🗑️ Logs limpios', this.styles.success);
    }
    
    /**
     * Configurar manejador global de errores
     */
    setupGlobalErrorHandler() {
        window.addEventListener('error', (event) => {
            this.logError(event.message, {
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno
            });
        });
        
        window.addEventListener('unhandledrejection', (event) => {
            this.logError('Promise rechazada sin manejar', event.reason);
        });
    }
    
    /**
     * Mostrar ayuda de comandos disponibles
     */
    showHelp() {
        console.log('%c📚 COMANDOS DISPONIBLES', this.styles.info);
        console.log(`
        debugLogger.logViewAccess(viewName, allowed)     - Log de acceso a vista
        debugLogger.logRoleCheck(roleName, hasRole)      - Log de validación de rol
        debugLogger.logPermissionCheck(perm, hasPerm)    - Log de validación de permiso
        debugLogger.logMenuItemVisibility(name, visible) - Log de visibilidad de menú
        debugLogger.logNavigation(from, to)              - Log de navegación
        debugLogger.logError(message, details)           - Log de error
        debugLogger.logWarning(message, details)         - Log de advertencia
        debugLogger.log(message, details, level)         - Log genérico
        
        debugLogger.showUserRolesTable()                 - Mostrar tabla de roles
        debugLogger.showMenuItemsTable()                 - Mostrar tabla de menú
        debugLogger.showLogs()                           - Mostrar historial de logs
        debugLogger.exportLogs()                         - Exportar logs como JSON
        debugLogger.clearLogs()                          - Limpiar logs
        debugLogger.showHelp()                           - Mostrar esta ayuda
        `);
    }
}

// Crear instancia global
const debugLogger = new DebugLogger();

// Hacer disponible globalmente
window.debugLogger = debugLogger;

// Mostrar mensaje de bienvenida
console.log('%c✨ Sistema de Debug Cargado', 'color: #00cc00; font-size: 14px; font-weight: bold;');
console.log('%cEscribe: debugLogger.showHelp() para ver los comandos disponibles', 'color: #0066cc; font-style: italic;');
