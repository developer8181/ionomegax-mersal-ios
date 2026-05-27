class PrintCutApp {
    constructor() {
        this.objects = [];
        this.selectedObjects = [];
        this.projectName = 'مشروع جديد';
        this.clipboard = [];

        this.engine = new CanvasEngine('main-canvas', 'overlay-canvas');
        this.toolManager = new ToolManager(this);
        this.layerManager = new LayerManager(this);
        this.cutEngine = new CutEngine(this);
        this.history = new HistoryManager(this);
        this.exportManager = new ExportManager(this);

        this.init();
    }

    init() {
        this.setupEventListeners();
        this.engine.zoomToFit();
        this.history.pushState();
        this.render();
        this.updateDimensionsDisplay();
    }

    setupEventListeners() {
        const container = document.getElementById('canvas-container');
        container.addEventListener('mousedown', (e) => this.toolManager.onMouseDown(e));
        container.addEventListener('mousemove', (e) => this.toolManager.onMouseMove(e));
        container.addEventListener('mouseup', (e) => this.toolManager.onMouseUp(e));
        container.addEventListener('mouseleave', (e) => this.toolManager.onMouseUp(e));

        container.addEventListener('wheel', (e) => {
            e.preventDefault();
            if (e.ctrlKey) {
                if (e.deltaY < 0) this.engine.zoomIn();
                else this.engine.zoomOut();
            } else {
                this.engine.panX -= e.deltaX;
                this.engine.panY -= e.deltaY;
            }
            this.render();
        });

        document.querySelectorAll('.tool-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.toolManager.setTool(btn.dataset.tool);
            });
        });

        this.setupMenuActions();
        this.setupKeyboardShortcuts();
        this.setupPropertyListeners();
        this.setupLayerActions();
        this.setupModalActions();
        this.setupFileInputs();
        this.setupZoomControls();
    }

    setupMenuActions() {
        document.getElementById('btn-new')?.addEventListener('click', () => this.showNewProjectModal());
        document.getElementById('btn-save')?.addEventListener('click', () => this.exportManager.saveProject());
        document.getElementById('btn-open')?.addEventListener('click', () => document.getElementById('file-input-project').click());
        document.getElementById('btn-import-image')?.addEventListener('click', () => document.getElementById('file-input-image').click());
        document.getElementById('btn-export-png')?.addEventListener('click', () => this.exportManager.exportPNG());
        document.getElementById('btn-export-svg')?.addEventListener('click', () => this.exportManager.exportSVG());
        document.getElementById('btn-export-pdf')?.addEventListener('click', () => this.exportManager.exportPDF());

        document.getElementById('btn-undo')?.addEventListener('click', () => this.history.undo());
        document.getElementById('btn-redo')?.addEventListener('click', () => this.history.redo());
        document.getElementById('btn-copy')?.addEventListener('click', () => this.copy());
        document.getElementById('btn-paste')?.addEventListener('click', () => this.paste());
        document.getElementById('btn-delete')?.addEventListener('click', () => this.deleteSelected());
        document.getElementById('btn-select-all')?.addEventListener('click', () => this.selectAll());

        document.getElementById('btn-zoom-in')?.addEventListener('click', () => { this.engine.zoomIn(); this.render(); });
        document.getElementById('btn-zoom-out')?.addEventListener('click', () => { this.engine.zoomOut(); this.render(); });
        document.getElementById('btn-zoom-fit')?.addEventListener('click', () => { this.engine.zoomToFit(); this.render(); });
        document.getElementById('btn-toggle-grid')?.addEventListener('click', () => { this.engine.showGrid = !this.engine.showGrid; this.render(); });

        document.getElementById('btn-group')?.addEventListener('click', () => this.groupSelected());
        document.getElementById('btn-bring-front')?.addEventListener('click', () => this.bringToFront());
        document.getElementById('btn-send-back')?.addEventListener('click', () => this.sendToBack());
        document.getElementById('btn-align-left')?.addEventListener('click', () => this.alignObjects('left'));
        document.getElementById('btn-align-center')?.addEventListener('click', () => this.alignObjects('center'));
        document.getElementById('btn-align-right')?.addEventListener('click', () => this.alignObjects('right'));

        document.getElementById('btn-cut-contour')?.addEventListener('click', () => this.addCutContour());
        document.getElementById('btn-cut-preview')?.addEventListener('click', () => this.cutEngine.showPreview());
        document.getElementById('btn-print')?.addEventListener('click', () => this.printDesign());

        document.getElementById('generate-cut-lines')?.addEventListener('click', () => this.generateCutLines());
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') return;

            if (e.ctrlKey || e.metaKey) {
                switch (e.key.toLowerCase()) {
                    case 'z': e.preventDefault(); if (e.shiftKey) this.history.redo(); else this.history.undo(); break;
                    case 'y': e.preventDefault(); this.history.redo(); break;
                    case 'c': e.preventDefault(); this.copy(); break;
                    case 'v': e.preventDefault(); this.paste(); break;
                    case 'a': e.preventDefault(); this.selectAll(); break;
                    case 'g': e.preventDefault(); this.groupSelected(); break;
                    case 's': e.preventDefault(); this.exportManager.saveProject(); break;
                    case 'd': e.preventDefault(); this.duplicateSelected(); break;
                }
            } else {
                switch (e.key) {
                    case 'Delete':
                    case 'Backspace': this.deleteSelected(); break;
                    case 'v': case 'V': this.toolManager.setTool('select'); break;
                    case 'h': case 'H': this.toolManager.setTool('move'); break;
                    case 'r': case 'R': this.toolManager.setTool('rect'); break;
                    case 'c': case 'C': this.toolManager.setTool('circle'); break;
                    case 'l': case 'L': this.toolManager.setTool('line'); break;
                    case 't': case 'T': this.toolManager.setTool('text'); break;
                    case 'p': case 'P': this.toolManager.setTool('pen'); break;
                    case 'b': case 'B': this.toolManager.setTool('pencil'); break;
                    case 'i': case 'I': this.toolManager.setTool('eyedropper'); break;
                    case 'Escape': this.clearSelection(); this.render(); break;
                }
            }
        });
    }

    setupPropertyListeners() {
        const propInputs = ['prop-x', 'prop-y', 'prop-w', 'prop-h', 'prop-rotation',
            'prop-fill', 'prop-stroke', 'prop-stroke-width', 'prop-fill-opacity'];

        for (const id of propInputs) {
            const el = document.getElementById(id);
            if (!el) continue;
            el.addEventListener('change', () => this.applyProperties());
            el.addEventListener('input', () => {
                if (el.type === 'color' || el.type === 'range') this.applyProperties();
            });
        }

        document.getElementById('prop-fill-opacity')?.addEventListener('input', (e) => {
            document.querySelector('.opacity-value').textContent = e.target.value + '%';
        });

        document.getElementById('prop-stroke-style')?.addEventListener('change', () => this.applyProperties());
        document.getElementById('prop-font-family')?.addEventListener('change', () => this.applyProperties());
        document.getElementById('prop-font-size')?.addEventListener('change', () => this.applyProperties());

        document.getElementById('prop-bold')?.addEventListener('click', (e) => {
            e.currentTarget.classList.toggle('active');
            this.applyProperties();
        });
        document.getElementById('prop-italic')?.addEventListener('click', (e) => {
            e.currentTarget.classList.toggle('active');
            this.applyProperties();
        });
    }

    setupLayerActions() {
        document.getElementById('add-layer')?.addEventListener('click', () => {
            this.layerManager.addLayer();
        });
        document.getElementById('delete-layer')?.addEventListener('click', () => {
            this.layerManager.deleteLayer(this.layerManager.activeLayerId);
        });
        document.getElementById('duplicate-layer')?.addEventListener('click', () => {
            this.layerManager.duplicateLayer(this.layerManager.activeLayerId);
        });
        document.getElementById('move-layer-up')?.addEventListener('click', () => {
            this.layerManager.moveLayerUp(this.layerManager.activeLayerId);
        });
        document.getElementById('move-layer-down')?.addEventListener('click', () => {
            this.layerManager.moveLayerDown(this.layerManager.activeLayerId);
        });
    }

    setupModalActions() {
        document.querySelectorAll('.modal-close, .modal-close-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                btn.closest('.modal').classList.remove('active');
            });
        });

        document.getElementById('page-size')?.addEventListener('change', (e) => {
            const customSize = document.getElementById('custom-size');
            customSize.style.display = e.target.value === 'custom' ? 'flex' : 'none';
        });

        document.querySelectorAll('.orientation-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.orientation-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            });
        });

        document.getElementById('create-new-project')?.addEventListener('click', () => this.createNewProject());
        document.getElementById('cancel-new-project')?.addEventListener('click', () => {
            document.getElementById('modal-new-project').classList.remove('active');
        });
    }

    setupFileInputs() {
        document.getElementById('file-input-image')?.addEventListener('change', (e) => this.handleImageImport(e));
        document.getElementById('file-input-project')?.addEventListener('change', (e) => this.handleProjectOpen(e));
        document.getElementById('file-input-svg')?.addEventListener('change', (e) => this.handleSVGImport(e));
    }

    setupZoomControls() {
        document.getElementById('zoom-in-btn')?.addEventListener('click', () => { this.engine.zoomIn(); this.render(); });
        document.getElementById('zoom-out-btn')?.addEventListener('click', () => { this.engine.zoomOut(); this.render(); });
        document.getElementById('zoom-fit-btn')?.addEventListener('click', () => { this.engine.zoomToFit(); this.render(); });
    }

    addObject(obj) {
        obj.layerId = this.layerManager.activeLayerId;
        this.objects.push(obj);
        this.layerManager.updateUI();
        this.render();
    }

    selectObject(obj, addToSelection = false) {
        if (!addToSelection) {
            this.selectedObjects.forEach(o => o.selected = false);
            this.selectedObjects = [];
        }
        obj.selected = true;
        if (!this.selectedObjects.includes(obj)) {
            this.selectedObjects.push(obj);
        }
        this.updateProperties();
        this.updateSelectionStatus();
        this.render();
    }

    deselectObject(obj) {
        obj.selected = false;
        this.selectedObjects = this.selectedObjects.filter(o => o !== obj);
        this.updateProperties();
        this.updateSelectionStatus();
        this.render();
    }

    clearSelection() {
        this.selectedObjects.forEach(o => o.selected = false);
        this.selectedObjects = [];
        this.updateProperties();
        this.updateSelectionStatus();
    }

    selectAll() {
        this.objects.forEach(obj => {
            if (obj.visible && !obj.locked) {
                obj.selected = true;
                if (!this.selectedObjects.includes(obj)) {
                    this.selectedObjects.push(obj);
                }
            }
        });
        this.updateProperties();
        this.updateSelectionStatus();
        this.render();
    }

    deleteSelected() {
        if (this.selectedObjects.length === 0) return;
        this.objects = this.objects.filter(obj => !this.selectedObjects.includes(obj));
        this.clearSelection();
        this.layerManager.updateUI();
        this.history.pushState();
        this.render();
    }

    copy() {
        this.clipboard = this.selectedObjects.map(obj => obj.serialize());
    }

    paste() {
        if (this.clipboard.length === 0) return;
        this.clearSelection();
        for (const data of this.clipboard) {
            const obj = DesignObject.deserialize(data);
            obj.id = Utils.generateId();
            obj.x += 5;
            obj.y += 5;
            obj.layerId = this.layerManager.activeLayerId;
            this.objects.push(obj);
            this.selectObject(obj, true);
        }
        this.clipboard = this.clipboard.map(data => {
            data.x += 5;
            data.y += 5;
            return data;
        });
        this.history.pushState();
        this.layerManager.updateUI();
        this.render();
    }

    duplicateSelected() {
        if (this.selectedObjects.length === 0) return;
        const newObjects = this.selectedObjects.map(obj => obj.clone());
        this.clearSelection();
        for (const obj of newObjects) {
            this.objects.push(obj);
            this.selectObject(obj, true);
        }
        this.history.pushState();
        this.layerManager.updateUI();
        this.render();
    }

    bringToFront() {
        for (const obj of this.selectedObjects) {
            const idx = this.objects.indexOf(obj);
            if (idx !== -1) {
                this.objects.splice(idx, 1);
                this.objects.push(obj);
            }
        }
        this.history.pushState();
        this.render();
    }

    sendToBack() {
        for (const obj of this.selectedObjects) {
            const idx = this.objects.indexOf(obj);
            if (idx !== -1) {
                this.objects.splice(idx, 1);
                this.objects.unshift(obj);
            }
        }
        this.history.pushState();
        this.render();
    }

    alignObjects(alignment) {
        if (this.selectedObjects.length < 2) return;
        const bounds = this.selectedObjects.map(o => o.getBounds());
        switch (alignment) {
            case 'left': {
                const minX = Math.min(...bounds.map(b => b.x));
                this.selectedObjects.forEach(o => { o.x = minX; });
                break;
            }
            case 'center': {
                const minX = Math.min(...bounds.map(b => b.x));
                const maxX = Math.max(...bounds.map(b => b.x + b.width));
                const center = (minX + maxX) / 2;
                this.selectedObjects.forEach(o => { o.x = center - o.getBounds().width / 2; });
                break;
            }
            case 'right': {
                const maxX = Math.max(...bounds.map(b => b.x + b.width));
                this.selectedObjects.forEach(o => { o.x = maxX - o.getBounds().width; });
                break;
            }
        }
        this.history.pushState();
        this.render();
    }

    addCutContour() {
        for (const obj of this.selectedObjects) {
            obj.hasCutPath = true;
            obj.cutOffset = this.cutEngine.defaultOffset;
        }
        this.cutEngine.generateAllCutPaths();
        this.render();
        this.history.pushState();
    }

    generateCutLines() {
        const cutType = document.getElementById('cut-type').value;
        const margin = parseFloat(document.getElementById('cut-margin').value) || 2;
        this.cutEngine.defaultOffset = margin;
        this.cutEngine.registrationMarks = document.getElementById('reg-marks').checked;
        this.cutEngine.cornerStyle = document.getElementById('prop-cut-corners')?.value || 'round';

        if (cutType === 'contour') {
            this.objects.forEach(obj => {
                obj.hasCutPath = true;
                obj.cutOffset = margin;
            });
        }

        this.cutEngine.generateAllCutPaths();
        this.render();
        this.history.pushState();
    }

    render() {
        const visibleObjects = this.layerManager.getObjectsByLayer();
        this.engine.render(visibleObjects, this.selectedObjects);

        if (this.cutEngine.cutPaths.length > 0) {
            const containerRect = this.engine.container.getBoundingClientRect();
            const pageWidthPx = this.engine.mmToScreen(this.engine.pageWidth);
            const pageHeightPx = this.engine.mmToScreen(this.engine.pageHeight);
            const offsetX = (containerRect.width - pageWidthPx) / 2 + this.engine.panX;
            const offsetY = (containerRect.height - pageHeightPx) / 2 + this.engine.panY;
            const scale = this.engine.mmToScreen(1);

            this.engine.ctx.save();
            this.engine.ctx.translate(offsetX, offsetY);
            this.engine.ctx.scale(scale, scale);
            this.cutEngine.drawCutPaths(this.engine.ctx);
            this.engine.ctx.restore();
        }
    }

    updateProperties() {
        if (this.selectedObjects.length === 0) {
            document.getElementById('text-properties').style.display = 'none';
            return;
        }

        const obj = this.selectedObjects[0];
        const bounds = obj.getBounds();

        document.getElementById('prop-x').value = obj.x.toFixed(1);
        document.getElementById('prop-y').value = obj.y.toFixed(1);
        document.getElementById('prop-w').value = bounds.width.toFixed(1);
        document.getElementById('prop-h').value = bounds.height.toFixed(1);
        document.getElementById('prop-rotation').value = obj.rotation;
        document.getElementById('prop-fill').value = obj.fill || '#ffffff';
        document.getElementById('prop-stroke').value = obj.stroke || '#000000';
        document.getElementById('prop-stroke-width').value = obj.strokeWidth;
        document.getElementById('prop-fill-opacity').value = Math.round(obj.fillOpacity * 100);
        document.querySelector('.opacity-value').textContent = Math.round(obj.fillOpacity * 100) + '%';

        if (obj.strokeStyle) {
            document.getElementById('prop-stroke-style').value = obj.strokeStyle;
        }

        const textProps = document.getElementById('text-properties');
        if (obj.type === 'text') {
            textProps.style.display = 'block';
            document.getElementById('prop-font-family').value = obj.fontFamily;
            document.getElementById('prop-font-size').value = obj.fontSize;
            if (obj.fontWeight === 'bold') document.getElementById('prop-bold').classList.add('active');
            else document.getElementById('prop-bold').classList.remove('active');
            if (obj.fontStyle === 'italic') document.getElementById('prop-italic').classList.add('active');
            else document.getElementById('prop-italic').classList.remove('active');
        } else {
            textProps.style.display = 'none';
        }
    }

    applyProperties() {
        if (this.selectedObjects.length === 0) return;

        for (const obj of this.selectedObjects) {
            obj.x = parseFloat(document.getElementById('prop-x').value) || 0;
            obj.y = parseFloat(document.getElementById('prop-y').value) || 0;
            obj.width = parseFloat(document.getElementById('prop-w').value) || 1;
            obj.height = parseFloat(document.getElementById('prop-h').value) || 1;
            obj.rotation = parseFloat(document.getElementById('prop-rotation').value) || 0;
            obj.fill = document.getElementById('prop-fill').value;
            obj.stroke = document.getElementById('prop-stroke').value;
            obj.strokeWidth = parseFloat(document.getElementById('prop-stroke-width').value) || 0;
            obj.fillOpacity = parseInt(document.getElementById('prop-fill-opacity').value) / 100;
            obj.strokeStyle = document.getElementById('prop-stroke-style').value;

            if (obj.type === 'text') {
                obj.fontFamily = document.getElementById('prop-font-family').value;
                obj.fontSize = parseInt(document.getElementById('prop-font-size').value) || 24;
                obj.fontWeight = document.getElementById('prop-bold').classList.contains('active') ? 'bold' : 'normal';
                obj.fontStyle = document.getElementById('prop-italic').classList.contains('active') ? 'italic' : 'normal';
            }

            obj.scaleX = 1;
            obj.scaleY = 1;
        }

        this.render();
    }

    updateSelectionStatus() {
        const statusEl = document.getElementById('status-selection');
        if (this.selectedObjects.length === 0) {
            statusEl.textContent = 'لا يوجد تحديد';
        } else if (this.selectedObjects.length === 1) {
            statusEl.textContent = `محدد: ${this.selectedObjects[0].name}`;
        } else {
            statusEl.textContent = `محدد: ${this.selectedObjects.length} عناصر`;
        }
    }

    updateDimensionsDisplay() {
        document.getElementById('canvas-dimensions').textContent =
            `${this.engine.pageWidth} × ${this.engine.pageHeight} mm`;
    }

    showNewProjectModal() {
        document.getElementById('modal-new-project').classList.add('active');
    }

    createNewProject() {
        const name = document.getElementById('project-name').value || 'مشروع جديد';
        const pageSize = document.getElementById('page-size').value;
        const orientation = document.querySelector('.orientation-btn.active')?.dataset.orientation || 'portrait';
        const dpi = parseInt(document.getElementById('project-dpi').value) || 300;

        let width, height;
        if (pageSize === 'custom') {
            width = parseFloat(document.getElementById('custom-width').value) || 210;
            height = parseFloat(document.getElementById('custom-height').value) || 297;
        } else {
            const size = Utils.pageSizes[pageSize];
            width = size.width;
            height = size.height;
        }

        if (orientation === 'landscape') {
            [width, height] = [height, width];
        }

        this.projectName = name;
        this.objects = [];
        this.selectedObjects = [];
        this.engine.setPageSize(width, height);
        this.engine.dpi = dpi;
        this.engine.zoomToFit();

        this.layerManager.layers = [];
        this.layerManager.addLayer('الطبقة الرئيسية');

        this.cutEngine.cutPaths = [];
        this.history.clear();
        this.history.pushState();

        this.updateDimensionsDisplay();
        this.render();

        document.getElementById('modal-new-project').classList.remove('active');
    }

    handleImageImport(e) {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = async (event) => {
            const imgObj = new ImageObject({
                x: 20,
                y: 20,
                name: file.name
            });
            await imgObj.loadImage(event.target.result);

            const maxDim = Math.min(this.engine.pageWidth, this.engine.pageHeight) * 0.8;
            if (imgObj.width > maxDim || imgObj.height > maxDim) {
                const scale = maxDim / Math.max(imgObj.width, imgObj.height);
                imgObj.width *= scale;
                imgObj.height *= scale;
            }

            const pageWidthMm = this.engine.pageWidth;
            const pageHeightMm = this.engine.pageHeight;
            imgObj.width = Utils.pixelsToMm(imgObj.width, 96);
            imgObj.height = Utils.pixelsToMm(imgObj.height, 96);

            if (imgObj.width > pageWidthMm * 0.8) {
                const scale = (pageWidthMm * 0.8) / imgObj.width;
                imgObj.width *= scale;
                imgObj.height *= scale;
            }

            imgObj.x = (pageWidthMm - imgObj.width) / 2;
            imgObj.y = (pageHeightMm - imgObj.height) / 2;

            this.addObject(imgObj);
            this.selectObject(imgObj, false);
            this.history.pushState();
            this.render();
        };
        reader.readAsDataURL(file);
        e.target.value = '';
    }

    handleProjectOpen(e) {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (event) => {
            this.exportManager.loadProject(event.target.result);
        };
        reader.readAsText(file);
        e.target.value = '';
    }

    handleSVGImport(e) {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (event) => {
            const parser = new DOMParser();
            const svgDoc = parser.parseFromString(event.target.result, 'image/svg+xml');
            this.importSVGElements(svgDoc);
        };
        reader.readAsText(file);
        e.target.value = '';
    }

    importSVGElements(svgDoc) {
        const rects = svgDoc.querySelectorAll('rect');
        const circles = svgDoc.querySelectorAll('circle, ellipse');
        const paths = svgDoc.querySelectorAll('path');
        const texts = svgDoc.querySelectorAll('text');

        rects.forEach(el => {
            const obj = new RectObject({
                x: parseFloat(el.getAttribute('x')) || 0,
                y: parseFloat(el.getAttribute('y')) || 0,
                width: parseFloat(el.getAttribute('width')) || 50,
                height: parseFloat(el.getAttribute('height')) || 50,
                fill: el.getAttribute('fill') || '#ffffff',
                stroke: el.getAttribute('stroke') || '#000000',
                strokeWidth: parseFloat(el.getAttribute('stroke-width')) || 1,
                cornerRadius: parseFloat(el.getAttribute('rx')) || 0
            });
            this.addObject(obj);
        });

        circles.forEach(el => {
            const cx = parseFloat(el.getAttribute('cx')) || 0;
            const cy = parseFloat(el.getAttribute('cy')) || 0;
            const rx = parseFloat(el.getAttribute('rx') || el.getAttribute('r')) || 25;
            const ry = parseFloat(el.getAttribute('ry') || el.getAttribute('r')) || 25;
            const obj = new CircleObject({
                x: cx - rx,
                y: cy - ry,
                width: rx * 2,
                height: ry * 2,
                fill: el.getAttribute('fill') || '#ffffff',
                stroke: el.getAttribute('stroke') || '#000000',
                strokeWidth: parseFloat(el.getAttribute('stroke-width')) || 1
            });
            this.addObject(obj);
        });

        texts.forEach(el => {
            const obj = new TextObject({
                x: parseFloat(el.getAttribute('x')) || 0,
                y: parseFloat(el.getAttribute('y')) || 0,
                text: el.textContent || 'نص',
                fontSize: parseFloat(el.getAttribute('font-size')) || 24,
                fontFamily: el.getAttribute('font-family') || 'Cairo',
                fill: el.getAttribute('fill') || '#000000'
            });
            this.addObject(obj);
        });

        this.history.pushState();
        this.render();
    }

    printDesign() {
        const printCanvas = document.createElement('canvas');
        const scale = 3;
        printCanvas.width = Utils.mmToPixels(this.engine.pageWidth, 96 * scale);
        printCanvas.height = Utils.mmToPixels(this.engine.pageHeight, 96 * scale);

        const ctx = printCanvas.getContext('2d');
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, printCanvas.width, printCanvas.height);

        const mmScale = printCanvas.width / this.engine.pageWidth;
        ctx.scale(mmScale, mmScale);

        for (const obj of this.objects) {
            if (obj.visible) obj.draw(ctx);
        }

        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <html>
            <head><title>طباعة - ${this.projectName}</title></head>
            <body style="margin:0;display:flex;justify-content:center;align-items:center;min-height:100vh;">
                <img src="${printCanvas.toDataURL()}" style="max-width:100%;max-height:100vh;">
                <script>window.onload=function(){window.print();}</script>
            </body>
            </html>
        `);
    }

    groupSelected() {
        // Simplified grouping - just ensures they stay together visually
        if (this.selectedObjects.length < 2) return;
        this.history.pushState();
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    window.app = new PrintCutApp();
});
