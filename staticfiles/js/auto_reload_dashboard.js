/**
 * Auto-Reload Manager para Dashboard de Movimientos
 */

class AutoReloadManager {
    constructor() {
        this.reloadInterval = null;
        this.isEnabled = false;
        this.currentInterval = 0;
        this.nextReloadTime = null;
        this.countdownInterval = null;
        this.init();
    }
    
    init() {
        // Cargar preferencias guardadas
        const savedInterval = localStorage.getItem('dashboardReloadInterval');
        const savedEnabled = localStorage.getItem('dashboardReloadEnabled') === 'true';
        
        if (savedInterval) {
            document.getElementById('reloadInterval').value = savedInterval;
        }
        
        if (savedEnabled && savedInterval && savedInterval !== '0') {
            document.getElementById('toggleAutoReload').checked = true;
            this.startAutoReload(parseInt(savedInterval));
        }
        
        // Event listeners
        document.getElementById('toggleAutoReload').addEventListener('change', (e) => {
            this.toggleAutoReload(e.target.checked);
        });
        
        document.getElementById('reloadInterval').addEventListener('change', (e) => {
            const interval = parseInt(e.target.value);
            localStorage.setItem('dashboardReloadInterval', interval);
            
            if (this.isEnabled) {
                this.stopAutoReload();
                if (interval > 0) {
                    this.startAutoReload(interval);
                }
            }
        });
        
        document.getElementById('btnReloadNow').addEventListener('click', () => {
            this.reloadNow();
        });
    }
    
    toggleAutoReload(enabled) {
        localStorage.setItem('dashboardReloadEnabled', enabled);
        
        if (enabled) {
            const interval = parseInt(document.getElementById('reloadInterval').value);
            if (interval > 0) {
                this.startAutoReload(interval);
            } else {
                alert('Selecciona un intervalo valido');
                document.getElementById('toggleAutoReload').checked = false;
            }
        } else {
            this.stopAutoReload();
        }
    }
    
    startAutoReload(seconds) {
        this.isEnabled = true;
        this.currentInterval = seconds;
        console.log('[AutoReload] Iniciado con intervalo de ' + seconds + 's');
        this.scheduleNextReload();
    }
    
    scheduleNextReload() {
        if (this.reloadInterval) clearTimeout(this.reloadInterval);
        if (this.countdownInterval) clearInterval(this.countdownInterval);
        
        this.nextReloadTime = Date.now() + (this.currentInterval * 1000);
        
        this.updateCountdown();
        this.countdownInterval = setInterval(() => this.updateCountdown(), 1000);
        
        this.reloadInterval = setTimeout(() => {
            this.reloadNow();
        }, this.currentInterval * 1000);
    }
    
    updateCountdown() {
        if (!this.nextReloadTime) return;
        
        const now = Date.now();
        const remaining = Math.max(0, Math.floor((this.nextReloadTime - now) / 1000));
        const nextUpdateEl = document.getElementById('nextUpdate');
        
        if (nextUpdateEl) {
            if (remaining === 0) {
                nextUpdateEl.textContent = 'Recargando...';
            } else {
                nextUpdateEl.textContent = 'En ' + remaining + 's';
            }
        }
    }
    
    reloadNow() {
        console.log('[AutoReload] Recargando pagina...');
        
        const now = new Date();
        const timeStr = now.toLocaleTimeString('es-ES');
        document.getElementById('lastUpdate').textContent = timeStr;
        
        window.location.reload();
    }
    
    stopAutoReload() {
        this.isEnabled = false;
        
        if (this.reloadInterval) {
            clearTimeout(this.reloadInterval);
            this.reloadInterval = null;
        }
        if (this.countdownInterval) {
            clearInterval(this.countdownInterval);
            this.countdownInterval = null;
        }
        
        document.getElementById('nextUpdate').textContent = '-';
        console.log('[AutoReload] Detenido');
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    new AutoReloadManager();
});
