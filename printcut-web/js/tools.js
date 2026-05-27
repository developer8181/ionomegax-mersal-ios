class ToolManager {
    constructor(app) {
        this.app = app;
        this.currentTool = 'select';
        this.isDrawing = false;
        this.startPoint = null;
        this.currentPoint = null;
        this.tempObject = null;
        this.dragOffset = null;
        this.resizeHandle = null;
        this.isResizing = false;
        this.isDragging = false;
        this.isPanning = false;
        this.panStart = null;
        this.pencilPoints = [];
    }

    setTool(tool) {
        this.currentTool = tool;
        this.isDrawing = false;
        this.tempObject = null;
        document.querySelectorAll('.tool-btn').forEach(btn => btn.classList.remove('active'));
        const btn = document.querySelector(`[data-tool="${tool}"]`);
        if (btn) btn.classList.add('active');

        const textProps = document.getElementById('text-properties');
        const cutProps = document.getElementById('cut-properties');
        if (textProps) textProps.style.display = tool === 'text' ? 'block' : 'none';
        if (cutProps) cutProps.style.display = (tool === 'cut-path' || tool === 'contour') ? 'block' : 'none';

        this.updateCursor();
        this.updateStatusTool();
    }

    updateCursor() {
        const container = document.getElementById('canvas-container');
        switch (this.currentTool) {
            case 'select': container.style.cursor = 'default'; break;
            case 'move': container.style.cursor = 'grab'; break;
            case 'text': container.style.cursor = 'text'; break;
            case 'eyedropper': container.style.cursor = 'crosshair'; break;
            case 'measure': container.style.cursor = 'crosshair'; break;
            default: container.style.cursor = 'crosshair'; break;
        }
    }

    updateStatusTool() {
        const toolNames = {
            select: 'أداة التحديد',
            move: 'أداة التحريك',
            pen: 'أداة القلم',
            pencil: 'الرسم الحر',
            line: 'خط مستقيم',
            rect: 'مستطيل',
            circle: 'دائرة',
            polygon: 'مضلع',
            star: 'نجمة',
            text: 'نص',
            image: 'صورة',
            'cut-path': 'مسار القص',
            contour: 'كنتور القص',
            eyedropper: 'قطارة اللون',
            measure: 'أداة القياس'
        };
        document.getElementById('status-tool').textContent = toolNames[this.currentTool] || this.currentTool;
    }

    onMouseDown(e) {
        const pos = this.app.engine.getMousePosition(e);
        const worldPos = this.app.engine.screenToWorld(pos.x, pos.y);
        this.startPoint = { screen: pos, world: worldPos };
        this.currentPoint = { screen: pos, world: worldPos };

        switch (this.currentTool) {
            case 'select': this.handleSelectDown(e, worldPos); break;
            case 'move': this.handlePanStart(pos); break;
            case 'rect': this.handleShapeStart(worldPos, 'rect'); break;
            case 'circle': this.handleShapeStart(worldPos, 'circle'); break;
            case 'line': this.handleLineStart(worldPos); break;
            case 'polygon': this.handleShapeStart(worldPos, 'polygon'); break;
            case 'star': this.handleShapeStart(worldPos, 'star'); break;
            case 'text': this.handleTextClick(worldPos); break;
            case 'pencil': this.handlePencilStart(worldPos); break;
            case 'image': this.handleImageClick(); break;
            case 'cut-path':
            case 'contour': this.handleCutPathStart(worldPos); break;
        }
    }

    onMouseMove(e) {
        const pos = this.app.engine.getMousePosition(e);
        const worldPos = this.app.engine.screenToWorld(pos.x, pos.y);
        this.currentPoint = { screen: pos, world: worldPos };

        document.getElementById('status-position').textContent =
            `X: ${worldPos.x.toFixed(1)} Y: ${worldPos.y.toFixed(1)}`;

        switch (this.currentTool) {
            case 'select': this.handleSelectMove(worldPos, pos); break;
            case 'move': this.handlePanMove(pos); break;
            case 'rect':
            case 'circle':
            case 'polygon':
            case 'star': this.handleShapeMove(worldPos); break;
            case 'line': this.handleLineMove(worldPos); break;
            case 'pencil': this.handlePencilMove(worldPos); break;
        }
    }

    onMouseUp(e) {
        const pos = this.app.engine.getMousePosition(e);
        const worldPos = this.app.engine.screenToWorld(pos.x, pos.y);

        switch (this.currentTool) {
            case 'select': this.handleSelectUp(worldPos); break;
            case 'move': this.handlePanEnd(); break;
            case 'rect':
            case 'circle':
            case 'polygon':
            case 'star': this.handleShapeEnd(worldPos); break;
            case 'line': this.handleLineEnd(worldPos); break;
            case 'pencil': this.handlePencilEnd(); break;
        }

        this.isDrawing = false;
        this.isResizing = false;
        this.isDragging = false;
    }

    handleSelectDown(e, worldPos) {
        const handle = this.getResizeHandle(worldPos);
        if (handle) {
            this.isResizing = true;
            this.resizeHandle = handle;
            return;
        }

        const hitObject = this.hitTest(worldPos);
        if (hitObject) {
            if (e.shiftKey) {
                if (this.app.selectedObjects.includes(hitObject)) {
                    this.app.deselectObject(hitObject);
                } else {
                    this.app.selectObject(hitObject, true);
                }
            } else {
                if (!this.app.selectedObjects.includes(hitObject)) {
                    this.app.selectObject(hitObject, false);
                }
            }
            this.isDragging = true;
            this.dragOffset = {
                x: worldPos.x - hitObject.x,
                y: worldPos.y - hitObject.y
            };
        } else {
            this.app.clearSelection();
            this.isDrawing = true;
        }
    }

    handleSelectMove(worldPos, screenPos) {
        if (this.isResizing && this.app.selectedObjects.length > 0) {
            const obj = this.app.selectedObjects[0];
            this.resizeObject(obj, worldPos);
            this.app.render();
        } else if (this.isDragging && this.app.selectedObjects.length > 0) {
            const dx = worldPos.x - this.startPoint.world.x;
            const dy = worldPos.y - this.startPoint.world.y;
            for (const obj of this.app.selectedObjects) {
                obj.x += dx;
                obj.y += dy;
            }
            this.startPoint.world = worldPos;
            this.app.render();
            this.app.updateProperties();
        } else if (this.isDrawing) {
            const rect = {
                x: Math.min(this.startPoint.screen.x, screenPos.x),
                y: Math.min(this.startPoint.screen.y, screenPos.y),
                width: Math.abs(screenPos.x - this.startPoint.screen.x),
                height: Math.abs(screenPos.y - this.startPoint.screen.y)
            };
            this.app.engine.drawSelectionRect(rect);
        }
    }

    handleSelectUp(worldPos) {
        if (this.isDrawing) {
            const startWorld = this.startPoint.world;
            const selRect = {
                x: Math.min(startWorld.x, worldPos.x),
                y: Math.min(startWorld.y, worldPos.y),
                width: Math.abs(worldPos.x - startWorld.x),
                height: Math.abs(worldPos.y - startWorld.y)
            };
            if (selRect.width > 1 && selRect.height > 1) {
                for (const obj of this.app.objects) {
                    if (!obj.visible || obj.locked) continue;
                    const bounds = obj.getBounds();
                    if (Utils.rectIntersects(selRect, bounds)) {
                        this.app.selectObject(obj, true);
                    }
                }
            }
            this.app.engine.clearOverlay();
        }
        if (this.isDragging || this.isResizing) {
            this.app.history.pushState();
        }
        this.app.render();
    }

    handlePanStart(pos) {
        this.isPanning = true;
        this.panStart = pos;
        document.getElementById('canvas-container').style.cursor = 'grabbing';
    }

    handlePanMove(pos) {
        if (!this.isPanning) return;
        const dx = pos.x - this.panStart.x;
        const dy = pos.y - this.panStart.y;
        this.app.engine.panX += dx;
        this.app.engine.panY += dy;
        this.panStart = pos;
        this.app.render();
    }

    handlePanEnd() {
        this.isPanning = false;
        document.getElementById('canvas-container').style.cursor = 'grab';
    }

    handleShapeStart(worldPos, type) {
        this.isDrawing = true;
        const props = {
            x: worldPos.x,
            y: worldPos.y,
            width: 0,
            height: 0,
            fill: document.getElementById('prop-fill').value,
            stroke: document.getElementById('prop-stroke').value,
            strokeWidth: parseFloat(document.getElementById('prop-stroke-width').value)
        };

        switch (type) {
            case 'rect': this.tempObject = new RectObject(props); break;
            case 'circle': this.tempObject = new CircleObject(props); break;
            case 'polygon': this.tempObject = new PolygonObject(props); break;
            case 'star': this.tempObject = new StarObject(props); break;
        }
    }

    handleShapeMove(worldPos) {
        if (!this.isDrawing || !this.tempObject) return;
        const w = worldPos.x - this.startPoint.world.x;
        const h = worldPos.y - this.startPoint.world.y;

        this.tempObject.x = w >= 0 ? this.startPoint.world.x : worldPos.x;
        this.tempObject.y = h >= 0 ? this.startPoint.world.y : worldPos.y;
        this.tempObject.width = Math.abs(w);
        this.tempObject.height = Math.abs(h);

        this.app.render();
        this.tempObject.draw(this.getTransformedContext());
    }

    handleShapeEnd(worldPos) {
        if (!this.isDrawing || !this.tempObject) return;
        if (this.tempObject.width > 1 && this.tempObject.height > 1) {
            this.app.addObject(this.tempObject);
            this.app.selectObject(this.tempObject, false);
            this.app.history.pushState();
        }
        this.tempObject = null;
    }

    handleLineStart(worldPos) {
        this.isDrawing = true;
        this.tempObject = new LineObject({
            x: worldPos.x,
            y: worldPos.y,
            x2: worldPos.x,
            y2: worldPos.y,
            stroke: document.getElementById('prop-stroke').value,
            strokeWidth: parseFloat(document.getElementById('prop-stroke-width').value)
        });
    }

    handleLineMove(worldPos) {
        if (!this.isDrawing || !this.tempObject) return;
        this.tempObject.x2 = worldPos.x;
        this.tempObject.y2 = worldPos.y;
        this.app.render();
        this.tempObject.draw(this.getTransformedContext());
    }

    handleLineEnd(worldPos) {
        if (!this.isDrawing || !this.tempObject) return;
        const dist = Utils.distance(this.tempObject.x, this.tempObject.y, worldPos.x, worldPos.y);
        if (dist > 1) {
            this.tempObject.x2 = worldPos.x;
            this.tempObject.y2 = worldPos.y;
            const bounds = this.tempObject.getBounds();
            this.tempObject.width = bounds.width;
            this.tempObject.height = bounds.height;
            this.app.addObject(this.tempObject);
            this.app.selectObject(this.tempObject, false);
            this.app.history.pushState();
        }
        this.tempObject = null;
    }

    handleTextClick(worldPos) {
        const text = prompt('أدخل النص:', 'نص جديد');
        if (!text) return;
        const obj = new TextObject({
            x: worldPos.x,
            y: worldPos.y,
            text: text,
            fontFamily: document.getElementById('prop-font-family').value,
            fontSize: parseInt(document.getElementById('prop-font-size').value),
            fill: document.getElementById('prop-fill').value
        });
        this.app.addObject(obj);
        this.app.selectObject(obj, false);
        this.app.history.pushState();
        this.app.render();
    }

    handlePencilStart(worldPos) {
        this.isDrawing = true;
        this.pencilPoints = [{ x: worldPos.x, y: worldPos.y }];
    }

    handlePencilMove(worldPos) {
        if (!this.isDrawing) return;
        this.pencilPoints.push({ x: worldPos.x, y: worldPos.y });
        this.app.render();

        const ctx = this.getTransformedContext();
        ctx.beginPath();
        ctx.moveTo(this.pencilPoints[0].x, this.pencilPoints[0].y);
        for (let i = 1; i < this.pencilPoints.length; i++) {
            ctx.lineTo(this.pencilPoints[i].x, this.pencilPoints[i].y);
        }
        ctx.strokeStyle = document.getElementById('prop-stroke').value;
        ctx.lineWidth = parseFloat(document.getElementById('prop-stroke-width').value);
        ctx.stroke();
    }

    handlePencilEnd() {
        if (!this.isDrawing || this.pencilPoints.length < 2) return;
        const simplified = this.simplifyPoints(this.pencilPoints);
        const bounds = Utils.getBoundingBox(simplified);
        const relativePoints = simplified.map(p => ({
            x: p.x - bounds.x,
            y: p.y - bounds.y
        }));
        const path = new PathObject({
            x: bounds.x,
            y: bounds.y,
            width: bounds.width,
            height: bounds.height,
            points: relativePoints,
            stroke: document.getElementById('prop-stroke').value,
            strokeWidth: parseFloat(document.getElementById('prop-stroke-width').value)
        });
        this.app.addObject(path);
        this.app.selectObject(path, false);
        this.app.history.pushState();
        this.pencilPoints = [];
        this.app.render();
    }

    handleImageClick() {
        document.getElementById('file-input-image').click();
    }

    handleCutPathStart(worldPos) {
        const hitObject = this.hitTest(worldPos);
        if (hitObject) {
            hitObject.hasCutPath = true;
            hitObject.cutOffset = parseFloat(document.getElementById('prop-cut-offset')?.value || 2);
            this.app.render();
            this.app.history.pushState();
        }
    }

    hitTest(worldPos) {
        for (let i = this.app.objects.length - 1; i >= 0; i--) {
            const obj = this.app.objects[i];
            if (!obj.visible || obj.locked) continue;
            if (obj.containsPoint(worldPos.x, worldPos.y)) {
                return obj;
            }
        }
        return null;
    }

    getResizeHandle(worldPos) {
        if (this.app.selectedObjects.length !== 1) return null;
        const obj = this.app.selectedObjects[0];
        const bounds = obj.getBounds();
        const handleSize = 3 / this.app.engine.zoom;

        const handles = [
            { name: 'nw', x: bounds.x, y: bounds.y },
            { name: 'ne', x: bounds.x + bounds.width, y: bounds.y },
            { name: 'sw', x: bounds.x, y: bounds.y + bounds.height },
            { name: 'se', x: bounds.x + bounds.width, y: bounds.y + bounds.height },
            { name: 'n', x: bounds.x + bounds.width / 2, y: bounds.y },
            { name: 's', x: bounds.x + bounds.width / 2, y: bounds.y + bounds.height },
            { name: 'w', x: bounds.x, y: bounds.y + bounds.height / 2 },
            { name: 'e', x: bounds.x + bounds.width, y: bounds.y + bounds.height / 2 },
        ];

        for (const h of handles) {
            if (Math.abs(worldPos.x - h.x) < handleSize && Math.abs(worldPos.y - h.y) < handleSize) {
                return h.name;
            }
        }
        return null;
    }

    resizeObject(obj, worldPos) {
        const bounds = obj.getBounds();
        switch (this.resizeHandle) {
            case 'se':
                obj.width = Math.max(1, worldPos.x - obj.x);
                obj.height = Math.max(1, worldPos.y - obj.y);
                break;
            case 'nw':
                obj.width = Math.max(1, bounds.x + bounds.width - worldPos.x);
                obj.height = Math.max(1, bounds.y + bounds.height - worldPos.y);
                obj.x = worldPos.x;
                obj.y = worldPos.y;
                break;
            case 'ne':
                obj.width = Math.max(1, worldPos.x - obj.x);
                obj.height = Math.max(1, bounds.y + bounds.height - worldPos.y);
                obj.y = worldPos.y;
                break;
            case 'sw':
                obj.width = Math.max(1, bounds.x + bounds.width - worldPos.x);
                obj.height = Math.max(1, worldPos.y - obj.y);
                obj.x = worldPos.x;
                break;
            case 'n':
                obj.height = Math.max(1, bounds.y + bounds.height - worldPos.y);
                obj.y = worldPos.y;
                break;
            case 's':
                obj.height = Math.max(1, worldPos.y - obj.y);
                break;
            case 'w':
                obj.width = Math.max(1, bounds.x + bounds.width - worldPos.x);
                obj.x = worldPos.x;
                break;
            case 'e':
                obj.width = Math.max(1, worldPos.x - obj.x);
                break;
        }
        this.app.updateProperties();
    }

    getTransformedContext() {
        const containerRect = this.app.engine.container.getBoundingClientRect();
        const pageWidthPx = this.app.engine.mmToScreen(this.app.engine.pageWidth);
        const pageHeightPx = this.app.engine.mmToScreen(this.app.engine.pageHeight);
        const offsetX = (containerRect.width - pageWidthPx) / 2 + this.app.engine.panX;
        const offsetY = (containerRect.height - pageHeightPx) / 2 + this.app.engine.panY;
        const scale = this.app.engine.mmToScreen(1);

        const ctx = this.app.engine.ctx;
        ctx.save();
        ctx.translate(offsetX, offsetY);
        ctx.scale(scale, scale);
        return ctx;
    }

    simplifyPoints(points, tolerance = 1) {
        if (points.length <= 2) return points;
        const result = [points[0]];
        let lastAdded = points[0];
        for (let i = 1; i < points.length - 1; i++) {
            if (Utils.distance(lastAdded.x, lastAdded.y, points[i].x, points[i].y) > tolerance) {
                result.push(points[i]);
                lastAdded = points[i];
            }
        }
        result.push(points[points.length - 1]);
        return result;
    }
}
