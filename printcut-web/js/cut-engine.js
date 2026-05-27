class CutEngine {
    constructor(app) {
        this.app = app;
        this.cutPaths = [];
        this.registrationMarks = true;
        this.defaultOffset = 2;
        this.cornerStyle = 'round';
    }

    generateCutContour(obj, offset = null) {
        offset = offset || this.defaultOffset;
        const bounds = obj.getBounds();

        const cutPath = {
            id: Utils.generateId(),
            objectId: obj.id,
            type: 'contour',
            offset: offset,
            points: [],
            closed: true
        };

        if (obj.type === 'circle') {
            const center = obj.getCenter();
            const rx = (bounds.width / 2) + offset;
            const ry = (bounds.height / 2) + offset;
            const segments = 64;
            for (let i = 0; i < segments; i++) {
                const angle = (Math.PI * 2 * i) / segments;
                cutPath.points.push({
                    x: center.x + rx * Math.cos(angle),
                    y: center.y + ry * Math.sin(angle)
                });
            }
        } else if (obj.type === 'rect' && obj.cornerRadius > 0) {
            const r = obj.cornerRadius + offset;
            cutPath.points = this.generateRoundedRectPath(
                bounds.x - offset,
                bounds.y - offset,
                bounds.width + offset * 2,
                bounds.height + offset * 2,
                r
            );
        } else {
            switch (this.cornerStyle) {
                case 'round':
                    cutPath.points = this.generateRoundedRectPath(
                        bounds.x - offset,
                        bounds.y - offset,
                        bounds.width + offset * 2,
                        bounds.height + offset * 2,
                        offset
                    );
                    break;
                case 'miter':
                    cutPath.points = [
                        { x: bounds.x - offset, y: bounds.y - offset },
                        { x: bounds.x + bounds.width + offset, y: bounds.y - offset },
                        { x: bounds.x + bounds.width + offset, y: bounds.y + bounds.height + offset },
                        { x: bounds.x - offset, y: bounds.y + bounds.height + offset }
                    ];
                    break;
                case 'bevel':
                    cutPath.points = [
                        { x: bounds.x, y: bounds.y - offset },
                        { x: bounds.x + bounds.width, y: bounds.y - offset },
                        { x: bounds.x + bounds.width + offset, y: bounds.y },
                        { x: bounds.x + bounds.width + offset, y: bounds.y + bounds.height },
                        { x: bounds.x + bounds.width, y: bounds.y + bounds.height + offset },
                        { x: bounds.x, y: bounds.y + bounds.height + offset },
                        { x: bounds.x - offset, y: bounds.y + bounds.height },
                        { x: bounds.x - offset, y: bounds.y }
                    ];
                    break;
            }
        }

        return cutPath;
    }

    generateRoundedRectPath(x, y, w, h, r) {
        const points = [];
        const segments = 8;

        for (let i = 0; i <= segments; i++) {
            const angle = -Math.PI / 2 + (Math.PI / 2) * (i / segments);
            points.push({ x: x + w - r + r * Math.cos(angle), y: y + r + r * Math.sin(angle) });
        }
        for (let i = 0; i <= segments; i++) {
            const angle = 0 + (Math.PI / 2) * (i / segments);
            points.push({ x: x + w - r + r * Math.cos(angle), y: y + h - r + r * Math.sin(angle) });
        }
        for (let i = 0; i <= segments; i++) {
            const angle = Math.PI / 2 + (Math.PI / 2) * (i / segments);
            points.push({ x: x + r + r * Math.cos(angle), y: y + h - r + r * Math.sin(angle) });
        }
        for (let i = 0; i <= segments; i++) {
            const angle = Math.PI + (Math.PI / 2) * (i / segments);
            points.push({ x: x + r + r * Math.cos(angle), y: y + r + r * Math.sin(angle) });
        }

        return points;
    }

    generateAllCutPaths() {
        this.cutPaths = [];
        for (const obj of this.app.objects) {
            if (obj.hasCutPath) {
                const cutPath = this.generateCutContour(obj, obj.cutOffset);
                this.cutPaths.push(cutPath);
            }
        }
        return this.cutPaths;
    }

    generateRegistrationMarks(pageWidth, pageHeight, margin = 5) {
        const markSize = 8;
        const marks = [];

        const positions = [
            { x: margin, y: margin },
            { x: pageWidth - margin, y: margin },
            { x: margin, y: pageHeight - margin },
            { x: pageWidth - margin, y: pageHeight - margin }
        ];

        for (const pos of positions) {
            marks.push({
                type: 'registration',
                x: pos.x,
                y: pos.y,
                size: markSize
            });
        }

        return marks;
    }

    drawCutPaths(ctx) {
        ctx.save();
        ctx.strokeStyle = '#ff0066';
        ctx.lineWidth = 0.5;
        ctx.setLineDash([3, 2]);

        for (const path of this.cutPaths) {
            if (path.points.length < 2) continue;
            ctx.beginPath();
            ctx.moveTo(path.points[0].x, path.points[0].y);
            for (let i = 1; i < path.points.length; i++) {
                ctx.lineTo(path.points[i].x, path.points[i].y);
            }
            if (path.closed) ctx.closePath();
            ctx.stroke();
        }

        if (this.registrationMarks) {
            const marks = this.generateRegistrationMarks(
                this.app.engine.pageWidth,
                this.app.engine.pageHeight
            );
            ctx.setLineDash([]);
            ctx.strokeStyle = '#000000';
            ctx.lineWidth = 0.3;
            for (const mark of marks) {
                this.drawRegistrationMark(ctx, mark.x, mark.y, mark.size);
            }
        }

        ctx.restore();
    }

    drawRegistrationMark(ctx, x, y, size) {
        ctx.beginPath();
        ctx.moveTo(x - size / 2, y);
        ctx.lineTo(x + size / 2, y);
        ctx.moveTo(x, y - size / 2);
        ctx.lineTo(x, y + size / 2);
        ctx.stroke();
        ctx.beginPath();
        ctx.arc(x, y, size / 4, 0, Math.PI * 2);
        ctx.stroke();
    }

    getTotalCutLength() {
        let total = 0;
        for (const path of this.cutPaths) {
            for (let i = 1; i < path.points.length; i++) {
                total += Utils.distance(
                    path.points[i - 1].x, path.points[i - 1].y,
                    path.points[i].x, path.points[i].y
                );
            }
            if (path.closed && path.points.length > 2) {
                const last = path.points[path.points.length - 1];
                const first = path.points[0];
                total += Utils.distance(last.x, last.y, first.x, first.y);
            }
        }
        return total;
    }

    showPreview() {
        this.generateAllCutPaths();
        const modal = document.getElementById('modal-cut-preview');
        modal.classList.add('active');

        const canvas = document.getElementById('cut-preview-canvas');
        const ctx = canvas.getContext('2d');
        canvas.width = 760;
        canvas.height = 400;

        const scale = Math.min(
            (canvas.width - 40) / this.app.engine.pageWidth,
            (canvas.height - 40) / this.app.engine.pageHeight
        );

        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#f8f9fa';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        const offsetX = (canvas.width - this.app.engine.pageWidth * scale) / 2;
        const offsetY = (canvas.height - this.app.engine.pageHeight * scale) / 2;

        ctx.save();
        ctx.translate(offsetX, offsetY);
        ctx.scale(scale, scale);

        ctx.fillStyle = '#ffffff';
        ctx.strokeStyle = '#dee2e6';
        ctx.fillRect(0, 0, this.app.engine.pageWidth, this.app.engine.pageHeight);
        ctx.strokeRect(0, 0, this.app.engine.pageWidth, this.app.engine.pageHeight);

        for (const obj of this.app.objects) {
            if (obj.visible) {
                ctx.globalAlpha = 0.3;
                obj.draw(ctx);
                ctx.globalAlpha = 1;
            }
        }

        this.drawCutPaths(ctx);
        ctx.restore();

        document.getElementById('cut-lines-count').textContent = this.cutPaths.length;
        document.getElementById('cut-total-length').textContent = this.getTotalCutLength().toFixed(1);
    }

    exportCutData() {
        this.generateAllCutPaths();
        return {
            paths: this.cutPaths,
            registrationMarks: this.registrationMarks ?
                this.generateRegistrationMarks(this.app.engine.pageWidth, this.app.engine.pageHeight) : [],
            pageSize: {
                width: this.app.engine.pageWidth,
                height: this.app.engine.pageHeight
            },
            totalLength: this.getTotalCutLength()
        };
    }
}
