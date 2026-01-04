/**
 * Sistema de escaneo de códigos de barras, QR y OCR - Versión 2
 * Soporta: Códigos 1D, QR 2D y reconocimiento de texto (OCR)
 * Mejorado para mejor compatibilidad móvil
 */

class BarcodeScanner {
    constructor(inputFieldId, buttonId) {
        this.inputFieldId = inputFieldId;
        this.buttonId = buttonId;
        this.inputField = null;
        this.button = null;
        this.video = null;
        this.canvas = null;
        this.stream = null;
        this.isScanning = false;
        this.scannerReady = false;
        this.codeReader = null;

        this.init();
    }

    init() {
        // Esperar a que los elementos estén disponibles
        const maxRetries = 10;
        let retries = 0;

        const checkElements = () => {
            this.inputField = document.getElementById(this.inputFieldId);
            this.button = document.getElementById(this.buttonId);

            if (!this.inputField || !this.button) {
                retries++;
                if (retries < maxRetries) {
                    console.log(`[BarcodeScanner] Reintentando... (${retries}/${maxRetries})`);
                    setTimeout(checkElements, 100);
                } else {
                    console.error(`[BarcodeScanner] No se encontraron elementos después de ${maxRetries} intentos`);
                }
                return;
            }

            console.log(`[BarcodeScanner] ✓ Elementos encontrados para ${this.inputFieldId}`);
            this.setupButton();
            this.loadLibraries();
        };

        checkElements();
    }

    setupButton() {
        if (!this.button) return;

        // Asegurar que el botón sea visible
        this.button.style.display = 'block';
        this.button.style.cursor = 'pointer';
        this.button.style.padding = '0.375rem 0.75rem';
        this.button.style.fontSize = '1rem';

        this.button.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log(`[BarcodeScanner] Click en botón ${this.buttonId}`);
            this.toggleScanner();
        });

        console.log(`[BarcodeScanner] Botón ${this.buttonId} configurado`);
    }

    loadLibraries() {
        // Cargar ZXing para códigos de barras y QR
        if (!window.ZXing) {
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/@zxing/library@0.20.0/umd/index.min.js';
            script.onload = () => {
                console.log('[BarcodeScanner] ✓ ZXing cargado');
                this.scannerReady = true;
                this.initZXing();
            };
            script.onerror = () => {
                console.error('[BarcodeScanner] ✗ Error cargando ZXing');
            };
            document.head.appendChild(script);
        } else {
            this.scannerReady = true;
            this.initZXing();
        }
    }

    initZXing() {
        try {
            const codeReader = new window.ZXing.BrowserMultiFormatReader();
            this.codeReader = codeReader;
            console.log('[BarcodeScanner] ✓ ZXing inicializado');
        } catch (e) {
            console.error('[BarcodeScanner] Error inicializando ZXing:', e);
        }
    }

    async toggleScanner() {
        if (this.isScanning) {
            this.stopScanner();
        } else {
            this.startScanner();
        }
    }

    async startScanner() {
        console.log('[BarcodeScanner] Iniciando escaneo...');
        this.isScanning = true;

        // Crear modal
        this.createModal();

        // Obtener acceso a cámara
        try {
            const constraints = {
                video: {
                    facingMode: 'environment', // Cámara trasera
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                },
                audio: false
            };

            this.stream = await navigator.mediaDevices.getUserMedia(constraints);
            console.log('[BarcodeScanner] ✓ Cámara accedida');

            this.video = document.getElementById('scannerVideo');
            if (this.video) {
                this.video.srcObject = this.stream;
                this.video.onloadedmetadata = () => {
                    this.video.play().catch(e => {
                        console.error('[BarcodeScanner] Error reproduciendo video:', e);
                    });
                };
            }

            // Iniciar detección
            this.detectCodes();

        } catch (error) {
            console.error('[BarcodeScanner] Error accediendo cámara:', error);
            alert('No se pudo acceder a la cámara. Verifica los permisos.');
            this.stopScanner();
        }
    }

    async detectCodes() {
        if (!this.isScanning || !this.codeReader) {
            return;
        }

        try {
            this.canvas = document.getElementById('scannerCanvas');
            this.video = document.getElementById('scannerVideo');

            if (!this.canvas || !this.video) {
                console.warn('[BarcodeScanner] Canvas o video no encontrados');
                return;
            }

            const ctx = this.canvas.getContext('2d');
            this.canvas.width = this.video.videoWidth || 640;
            this.canvas.height = this.video.videoHeight || 480;

            // Dibujar frame del video
            ctx.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);

            try {
                // Intentar decodificar
                const result = await this.codeReader.decodeFromCanvas(this.canvas);
                if (result) {
                    console.log('[BarcodeScanner] ✓ Código detectado:', result.getText());
                    this.handleDetection(result.getText());
                    return;
                }
            } catch (e) {
                // Sin código detectado, continuar buscando
            }

            // Continuar buscando
            if (this.isScanning) {
                requestAnimationFrame(() => this.detectCodes());
            }

        } catch (error) {
            console.error('[BarcodeScanner] Error detectando códigos:', error);
            if (this.isScanning) {
                setTimeout(() => this.detectCodes(), 100);
            }
        }
    }

    handleDetection(code) {
        if (!this.inputField) return;

        console.log('[BarcodeScanner] Código leído:', code);
        this.inputField.value = code;

        // Mostrar notificación
        this.showNotification(`✓ Código leído: ${code}`);

        // Cerrar scanner
        this.stopScanner();

        // Opcional: Hacer submit del formulario
        const form = this.inputField.closest('form');
        if (form) {
            form.submit();
        }
    }

    stopScanner() {
        console.log('[BarcodeScanner] Deteniendo escaneo...');
        this.isScanning = false;

        // Detener stream de cámara
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }

        // Cerrar modal
        const modal = document.getElementById('scannerModal');
        if (modal) {
            const bsModal = window.bootstrap?.Modal?.getInstance(modal);
            if (bsModal) {
                bsModal.hide();
            } else {
                modal.style.display = 'none';
            }
        }
    }

    createModal() {
        // Verificar si ya existe
        if (document.getElementById('scannerModal')) {
            const modal = new window.bootstrap.Modal(document.getElementById('scannerModal'));
            modal.show();
            return;
        }

        const modal = document.createElement('div');
        modal.id = 'scannerModal';
        modal.className = 'modal fade';
        modal.tabIndex = '-1';
        modal.innerHTML = `
            <div class="modal-dialog modal-fullscreen-sm-down modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-camera"></i> Escanear Código
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body p-0">
                        <div style="position: relative; width: 100%; background: #000; aspect-ratio: 16/9;">
                            <video id="scannerVideo" 
                                   style="width: 100%; height: 100%; display: block; object-fit: cover;"
                                   playsinline autoplay muted></video>
                            <canvas id="scannerCanvas" style="display: none;"></canvas>
                            
                            <!-- Overlay con línea de escaneo -->
                            <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; 
                                        pointer-events: none; display: flex; align-items: center; 
                                        justify-content: center;">
                                <div style="width: 80%; height: 40%; border: 3px solid #00ff00; 
                                           border-radius: 10px; box-shadow: inset 0 0 10px rgba(0,255,0,0.3);
                                           animation: pulse 1.5s infinite;"></div>
                            </div>
                        </div>
                        <div class="p-3 text-center text-muted">
                            <small>Apunta el código de barras, QR o texto hacia la cámara</small>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                            <i class="fas fa-times"></i> Cancelar
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Agregar estilos
        const style = document.createElement('style');
        style.textContent = `
            @keyframes pulse {
                0%, 100% { box-shadow: inset 0 0 10px rgba(0,255,0,0.3); }
                50% { box-shadow: inset 0 0 20px rgba(0,255,0,0.6); }
            }
        `;
        document.head.appendChild(style);

        // Mostrar modal
        const bsModal = new window.bootstrap.Modal(modal);
        bsModal.show();

        // Detener escaneo al cerrar
        modal.addEventListener('hidden.bs.modal', () => {
            this.stopScanner();
        });
    }

    showNotification(message) {
        const notification = document.createElement('div');
        notification.className = 'alert alert-success position-fixed top-0 end-0 m-3';
        notification.style.zIndex = '9999';
        notification.innerHTML = message;
        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
}

/**
 * Inicializar escaners cuando el DOM esté listo
 */
console.log('[BarcodeScanner v2] Script cargado');

function initScanners() {
    console.log('[BarcodeScanner v2] Inicializando escaners...');

    // Escanear para el campo de búsqueda general
    if (document.getElementById('search')) {
        new BarcodeScanner('search', 'btnScanSearch');
    }

    // Escanear para el campo de búsqueda por CNIS
    if (document.getElementById('search_cnis')) {
        new BarcodeScanner('search_cnis', 'btnScanCNIS');
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initScanners);
} else {
    initScanners();
}
