class CanvasEngine {
    constructor(canvasId, overlayId) {
        this.canvas = document.getElementById(canvasId);
        this.overlay = document.getElementById(overlayId);
        this.ctx = this.canvas.getContext('2d');
        this.overlayCtx = this.overlay.getContext('2d');
        this.container = document.getElementById('canvas-container');
        this.wrapper = document.getElementById('canvas-wrapper');

        this.pageWidth = 210;
        this.pageHeight = 297;
        this.dpi = 300;
        this.zoom = 1;
        this.panX = 0;
        this.panY = 0;
        this.gridSize = 10;
        this.showGrid = true;
        this.showRulers = true;

        this.pixelRatio = window.devicePixelRatio || 1;
        this.screenDPI = 96;

        this.init();
    }

    init() {
        this.updateCanvasSize();
        window.addEventListener('resize', () => this.updateCanvasSize());
    }

    updateCanvasSize() {
        const containerRect = this.container.getBoundingClientRect();
        const pageWidthPx = this.mmToScreen(this.pageWidth);
        const pageHeightPx = this.mmToScreen(this.pageHeight);

        this.canvas.width = containerRect.width * this.pixelRatio;
        this.canvas.height = containerRect.height * this.pixelRatio;
        this.canvas.style.width = containerRect.width + 'px';
        this.canvas.style.height = containerRect.height + 'px';

        this.overlay.width = containerRect.width * this.pixelRatio;
        this.overlay.height = containerRect.height * this.pixelRatio;
        this.overlay.style.width = containerRect.width + 'px';
        this.overlay.style.height = containerRect.height + 'px';

        this.canvas.style.transform = 'none';
        this.canvas.style.position = 'absolute';
        this.canvas.style.top = '0';
        this.canvas.style.left = '0';
        this.overlay.style.transform = 'none';
        this.overlay.style.position = 'absolute';
        this.overlay.style.top = '0';
        this.overlay.style.left = '0';

        this.ctx.scale(this.pixelRatio, this.pixelRatio);
        this.overlayCtx.scale(this.pixelRatio, this.pixelRatio);
    }

    mmToScreen(mm) {
        return (mm / 25.4) * this.screenDPI * this.zoom;
    }

    screenToMm(px) {
        return (px / (this.screenDPI * this.zoom)) * 25.4;
    }

    worldToScreen(x, y) {
        const containerRect = this.container.getBoundingClientRect();
        const pageWidthPx = this.mmToScreen(this.pageWidth);
        const pageHeightPx = this.mmToScreen(this.pageHeight);
        const offsetX = (containerRect.width - pageWidthPx) / 2 + this.panX;
        const offsetY = (containerRect.height - pageHeightPx) / 2 + this.panY;
        return {
            x: offsetX + this.mmToScreen(x),
            y: offsetY + this.mmToScreen(y)
        };
    }

    screenToWorld(sx, sy) {
        const containerRect = this.container.getBoundingClientRect();
        const pageWidthPx = this.mmToScreen(this.pageWidth);
        const pageHeightPx = this.mmToScreen(this.pageHeight);
        const offsetX = (containerRect.width - pageWidthPx) / 2 + this.panX;
        const offsetY = (containerRect.height - pageHeightPx) / 2 + this.panY;
        return {
            x: this.screenToMm(sx - offsetX),
            y: this.screenToMm(sy - offsetY)
        };
    }

    setPageSize(width, height) {
        this.pageWidth = width;
        this.pageHeight = height;
        this.updateCanvasSize();
    }

    setZoom(zoom) {
        this.zoom = Utils.clamp(zoom, 0.1, 10);
        document.getElementById('zoom-level').textContent = Math.round(this.zoom * 100) + '%';
    }

    zoomIn() {
        this.setZoom(this.zoom * 1.25);
    }

    zoomOut() {
        this.setZoom(this.zoom / 1.25);
    }

    zoomToFit() {
        const containerRect = this.container.getBoundingClientRect();
        const scaleX = (containerRect.width - 40) / ((this.pageWidth / 25.4) * this.screenDPI);
        const scaleY = (containerRect.height - 40) / ((this.pageHeight / 25.4) * this.screenDPI);
        this.setZoom(Math.min(scaleX, scaleY));
        this.panX = 0;
        this.panY = 0;
    }

    clear() {
        const w = this.canvas.width / this.pixelRatio;
        const h = this.canvas.height / this.pixelRatio;
        this.ctx.clearRect(0, 0, w, h);
    }

    clearOverlay() {
        const w = this.overlay.width / this.pixelRatio;
        const h = this.overlay.height / this.pixelRatio;
        this.overlayCtx.clearRect(0, 0, w, h);
    }

    render(objects, selectedObjects = []) {
        this.clear();
        this.drawBackground();
        this.drawPage();
        if (this.showGrid) this.drawGrid();
        this.drawObjects(objects);
        this.clearOverlay();
        this.drawSelection(selectedObjects);
    }

    drawBackground() {
        const w = this.canvas.width / this.pixelRatio;
        const h = this.canvas.height / this.pixelRatio;
        this.ctx.fillStyle = '#374151';
        this.ctx.fillRect(0, 0, w, h);
    }

    drawPage() {
        const containerRect = this.container.getBoundingClientRect();
        const pageWidthPx = this.mmToScreen(this.pageWidth);
        const pageHeightPx = this.mmToScreen(this.pageHeight);
        const offsetX = (containerRect.width - pageWidthPx) / 2 + this.panX;
        const offsetY = (containerRect.height - pageHeightPx) / 2 + this.panY;

        this.ctx.save();
        this.ctx.shadowColor = 'rgba(0, 0, 0, 0.3)';
        this.ctx.shadowBlur = 20;
        this.ctx.shadowOffsetX = 5;
        this.ctx.shadowOffsetY = 5;
        this.ctx.fillStyle = '#ffffff';
        this.ctx.fillRect(offsetX, offsetY, pageWidthPx, pageHeightPx);
        this.ctx.restore();

        this.ctx.strokeStyle = '#d1d5db';
        this.ctx.lineWidth = 1;
        this.ctx.strokeRect(offsetX, offsetY, pageWidthPx, pageHeightPx);
    }

    drawGrid() {
        const containerRect = this.container.getBoundingClientRect();
        const pageWidthPx = this.mmToScreen(this.pageWidth);
        const pageHeightPx = this.mmToScreen(this.pageHeight);
        const offsetX = (containerRect.width - pageWidthPx) / 2 + this.panX;
        const offsetY = (containerRect.height - pageHeightPx) / 2 + this.panY;
        const gridPx = this.mmToScreen(this.gridSize);

        if (gridPx < 5) return;

        this.ctx.save();
        this.ctx.strokeStyle = 'rgba(200, 200, 200, 0.3)';
        this.ctx.lineWidth = 0.5;
        this.ctx.beginPath();

        for (let x = offsetX; x <= offsetX + pageWidthPx; x += gridPx) {
            this.ctx.moveTo(x, offsetY);
            this.ctx.lineTo(x, offsetY + pageHeightPx);
        }
        for (let y = offsetY; y <= offsetY + pageHeightPx; y += gridPx) {
            this.ctx.moveTo(offsetX, y);
            this.ctx.lineTo(offsetX + pageWidthPx, y);
        }

        this.ctx.stroke();
        this.ctx.restore();
    }

    drawObjects(objects) {
        this.ctx.save();
        const containerRect = this.container.getBoundingClientRect();
        const pageWidthPx = this.mmToScreen(this.pageWidth);
        const pageHeightPx = this.mmToScreen(this.pageHeight);
        const offsetX = (containerRect.width - pageWidthPx) / 2 + this.panX;
        const offsetY = (containerRect.height - pageHeightPx) / 2 + this.panY;

        this.ctx.beginPath();
        this.ctx.rect(offsetX, offsetY, pageWidthPx, pageHeightPx);
        this.ctx.clip();

        const scale = this.mmToScreen(1);
        this.ctx.translate(offsetX, offsetY);
        this.ctx.scale(scale, scale);

        for (const obj of objects) {
            if (!obj.visible) continue;
            obj.draw(this.ctx);
        }

        this.ctx.restore();
    }

    drawSelection(selectedObjects) {
        if (selectedObjects.length === 0) return;

        const containerRect = this.container.getBoundingClientRect();
        const pageWidthPx = this.mmToScreen(this.pageWidth);
        const pageHeightPx = this.mmToScreen(this.pageHeight);
        const offsetX = (containerRect.width - pageWidthPx) / 2 + this.panX;
        const offsetY = (containerRect.height - pageHeightPx) / 2 + this.panY;
        const scale = this.mmToScreen(1);

        this.overlayCtx.save();
        this.overlayCtx.translate(offsetX, offsetY);
        this.overlayCtx.scale(scale, scale);

        for (const obj of selectedObjects) {
            const bounds = obj.getBounds();
            this.overlayCtx.save();
            const center = obj.getCenter();
            this.overlayCtx.translate(center.x, center.y);
            this.overlayCtx.rotate(Utils.degToRad(obj.rotation));
            this.overlayCtx.translate(-center.x, -center.y);

            this.overlayCtx.strokeStyle = '#2563eb';
            this.overlayCtx.lineWidth = 1.5 / scale;
            this.overlayCtx.setLineDash([4 / scale, 4 / scale]);
            this.overlayCtx.strokeRect(bounds.x, bounds.y, bounds.width, bounds.height);

            const handleSize = 6 / scale;
            this.overlayCtx.setLineDash([]);
            this.overlayCtx.fillStyle = '#ffffff';
            this.overlayCtx.strokeStyle = '#2563eb';
            this.overlayCtx.lineWidth = 1.5 / scale;

            const handles = [
                { x: bounds.x, y: bounds.y },
                { x: bounds.x + bounds.width, y: bounds.y },
                { x: bounds.x, y: bounds.y + bounds.height },
                { x: bounds.x + bounds.width, y: bounds.y + bounds.height },
                { x: bounds.x + bounds.width / 2, y: bounds.y },
                { x: bounds.x + bounds.width / 2, y: bounds.y + bounds.height },
                { x: bounds.x, y: bounds.y + bounds.height / 2 },
                { x: bounds.x + bounds.width, y: bounds.y + bounds.height / 2 },
            ];

            for (const h of handles) {
                this.overlayCtx.fillRect(h.x - handleSize / 2, h.y - handleSize / 2, handleSize, handleSize);
                this.overlayCtx.strokeRect(h.x - handleSize / 2, h.y - handleSize / 2, handleSize, handleSize);
            }

            const rotHandle = { x: bounds.x + bounds.width / 2, y: bounds.y - 20 / scale };
            this.overlayCtx.beginPath();
            this.overlayCtx.moveTo(bounds.x + bounds.width / 2, bounds.y);
            this.overlayCtx.lineTo(rotHandle.x, rotHandle.y);
            this.overlayCtx.stroke();
            this.overlayCtx.beginPath();
            this.overlayCtx.arc(rotHandle.x, rotHandle.y, handleSize / 2, 0, Math.PI * 2);
            this.overlayCtx.fill();
            this.overlayCtx.stroke();

            this.overlayCtx.restore();
        }

        this.overlayCtx.restore();
    }

    drawSelectionRect(rect) {
        this.clearOverlay();
        if (!rect) return;
        this.overlayCtx.save();
        this.overlayCtx.strokeStyle = '#2563eb';
        this.overlayCtx.lineWidth = 1;
        this.overlayCtx.setLineDash([4, 4]);
        this.overlayCtx.fillStyle = 'rgba(37, 99, 235, 0.1)';
        this.overlayCtx.fillRect(rect.x, rect.y, rect.width, rect.height);
        this.overlayCtx.strokeRect(rect.x, rect.y, rect.width, rect.height);
        this.overlayCtx.restore();
    }

    getMousePosition(e) {
        const rect = this.container.getBoundingClientRect();
        return {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        };
    }
}
