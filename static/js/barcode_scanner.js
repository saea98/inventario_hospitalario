/**
 * Sistema de escaneo de códigos de barras, QR y OCR
 * Soporta: Códigos 1D, QR 2D y reconocimiento de texto (OCR)
 */

class BarcodeScanner {
    constructor(inputFieldId, buttonId) {
        this.inputField = document.getElementById(inputFieldId);
        this.button = document.getElementById(buttonId);
        this.video = null;
        this.canvas = null;
        this.stream = null;
        this.isScanning = false;
        this.scannerReady = false;

        // Cargar librerías necesarias
        this.loadLibraries();

        // Event listeners
        if (this.button) {
            this.button.addEventListener('click', () => this.toggleScanner());
        }
    }

    /**
     * Cargar librerías necesarias (ZXing y Tesseract)
     */
    loadLibraries() {
        // Cargar ZXing para códigos de barras y QR
        if (!window.ZXing) {
            const script1 = document.createElement('script');
            script1.src = 'https://cdn.jsdelivr.net/npm/@zxing/library@0.20.0/umd/index.min.js';
            script1.onload = () => {
                console.log('✓ ZXing cargado');
                this.scannerReady = true;
            };
            document.head.appendChild(script1);
        }

        // Cargar Tesseract para OCR
        if (!window.Tesseract) {
            const script2 = document.createElement('script');
            script2.src = 'https://cdn.jsdelivr.net/npm/tesseract.js@4.1.1/dist/tesseract.min.js';
            script2.onload = () => {
                console.log('✓ Tesseract cargado');
            };
            document.head.appendChild(script2);
        }
    }

    /**
     * Alternar entre escaneo activado/desactivado
     */
    async toggleScanner() {
        if (this.isScanning) {
            this.stopScanner();
        } else {
            await this.startScanner();
        }
    }

    /**
     * Iniciar escaneo
     */
    async startScanner() {
        try {
            // Crear modal si no existe
            if (!document.getElementById('scannerModal')) {
                this.createScannerModal();
            }

            // Mostrar modal
            const modal = new bootstrap.Modal(document.getElementById('scannerModal'));
            modal.show();

            // Obtener acceso a la cámara
            const constraints = {
                video: {
                    facingMode: 'environment', // Cámara trasera en móviles
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                },
                audio: false
            };

            this.stream = await navigator.mediaDevices.getUserMedia(constraints);
            this.video = document.getElementById('scannerVideo');
            this.video.srcObject = this.stream;

            this.isScanning = true;
            this.button.innerHTML = '<i class="fas fa-stop-circle"></i> Detener escaneo';
            this.button.classList.remove('btn-outline-secondary');
            this.button.classList.add('btn-danger');

            // Iniciar bucle de escaneo
            this.scanFrame();

        } catch (error) {
            console.error('Error al acceder a la cámara:', error);
            alert('No se pudo acceder a la cámara. Verifica los permisos.');
            this.isScanning = false;
        }
    }

    /**
     * Detener escaneo
     */
    stopScanner() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
        }

        this.isScanning = false;
        this.button.innerHTML = '<i class="fas fa-camera"></i> Escanear';
        this.button.classList.remove('btn-danger');
        this.button.classList.add('btn-outline-secondary');

        // Cerrar modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('scannerModal'));
        if (modal) {
            modal.hide();
        }
    }

    /**
     * Procesar cada frame de video
     */
    async scanFrame() {
        if (!this.isScanning) return;

        const canvas = document.getElementById('scannerCanvas');
        const context = canvas.getContext('2d');

        // Dibujar frame actual
        context.drawImage(this.video, 0, 0, canvas.width, canvas.height);

        try {
            // Intentar leer código de barras/QR
            const result = await this.decodeBarcode(canvas);
            if (result) {
                this.handleScanResult(result);
                return;
            }
        } catch (error) {
            // No es un código válido, continuar
        }

        // Intentar OCR si no se encontró código
        try {
            const ocrResult = await this.performOCR(canvas);
            if (ocrResult && ocrResult.trim().length > 0) {
                this.handleScanResult(ocrResult.trim());
                return;
            }
        } catch (error) {
            // Error en OCR, continuar
        }

        // Continuar escaneando
        requestAnimationFrame(() => this.scanFrame());
    }

    /**
     * Decodificar código de barras/QR
     */
    async decodeBarcode(canvas) {
        if (!window.ZXing) return null;

        try {
            const imageData = canvas.getContext('2d').getImageData(
                0, 0, canvas.width, canvas.height
            );

            const codeReader = new ZXing.BrowserMultiFormatReader();
            const luminanceSource = new ZXing.HTMLCanvasElementLuminanceSource(canvas);
            const binaryBitmap = new ZXing.BinaryBitmap(
                new ZXing.HybridBinarizer(luminanceSource)
            );

            const result = codeReader.decodeFromCanvas(canvas);
            return result ? result.text : null;

        } catch (error) {
            return null;
        }
    }

    /**
     * Realizar OCR en la imagen
     */
    async performOCR(canvas) {
        if (!window.Tesseract) return null;

        try {
            const worker = await Tesseract.createWorker('spa'); // Español
            const result = await worker.recognize(canvas);
            await worker.terminate();

            return result.data.text;

        } catch (error) {
            console.error('Error en OCR:', error);
            return null;
        }
    }

    /**
     * Manejar resultado del escaneo
     */
    handleScanResult(result) {
        console.log('✓ Escaneo exitoso:', result);

        // Llenar el campo de entrada
        this.inputField.value = result;

        // Mostrar notificación
        this.showNotification(`✓ Código leído: ${result}`);

        // Detener escaneo
        this.stopScanner();

        // Opcional: hacer focus en el campo
        this.inputField.focus();
    }

    /**
     * Mostrar notificación visual
     */
    showNotification(message) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-success alert-dismissible fade show';
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        const container = document.querySelector('.card-body') || document.body;
        container.insertBefore(alert, container.firstChild);

        setTimeout(() => alert.remove(), 3000);
    }

    /**
     * Crear modal para el escaneo
     */
    createScannerModal() {
        const modal = document.createElement('div');
        modal.id = 'scannerModal';
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog modal-fullscreen-sm-down">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-camera"></i> Escanear código
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body p-0">
                        <div style="position: relative; width: 100%; background: #000;">
                            <video id="scannerVideo" 
                                   style="width: 100%; height: auto; display: block;"
                                   playsinline></video>
                            <canvas id="scannerCanvas" 
                                    style="display: none; width: 100%; height: auto;"></canvas>
                            
                            <!-- Overlay con línea de escaneo -->
                            <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; 
                                        pointer-events: none; display: flex; align-items: center; 
                                        justify-content: center;">
                                <div style="width: 80%; height: 40%; border: 3px solid #00ff00; 
                                           border-radius: 10px; box-shadow: inset 0 0 10px rgba(0,255,0,0.3);
                                           animation: pulse 1.5s infinite;">
                                </div>
                            </div>

                            <!-- Indicadores de esquinas -->
                            <div style="position: absolute; top: 10%; left: 10%; width: 30px; height: 30px; 
                                       border-top: 3px solid #00ff00; border-left: 3px solid #00ff00;"></div>
                            <div style="position: absolute; top: 10%; right: 10%; width: 30px; height: 30px; 
                                       border-top: 3px solid #00ff00; border-right: 3px solid #00ff00;"></div>
                            <div style="position: absolute; bottom: 10%; left: 10%; width: 30px; height: 30px; 
                                       border-bottom: 3px solid #00ff00; border-left: 3px solid #00ff00;"></div>
                            <div style="position: absolute; bottom: 10%; right: 10%; width: 30px; height: 30px; 
                                       border-bottom: 3px solid #00ff00; border-right: 3px solid #00ff00;"></div>
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

        // Agregar estilos de animación
        const style = document.createElement('style');
        style.textContent = `
            @keyframes pulse {
                0%, 100% { box-shadow: inset 0 0 10px rgba(0,255,0,0.3); }
                50% { box-shadow: inset 0 0 20px rgba(0,255,0,0.6); }
            }
        `;
        document.head.appendChild(style);
    }
}

/**
 * Inicializar escaners cuando el DOM esté listo
 */
document.addEventListener('DOMContentLoaded', function() {
    // Escanear para el campo de búsqueda general
    if (document.getElementById('search')) {
        new BarcodeScanner('search', 'btnScanSearch');
    }

    // Escanear para el campo de búsqueda por CNIS
    if (document.getElementById('search_cnis')) {
        new BarcodeScanner('search_cnis', 'btnScanCNIS');
    }
});
