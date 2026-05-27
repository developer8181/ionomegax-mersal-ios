class ExportManager {
    constructor(app) {
        this.app = app;
    }

    exportPNG(scale = 2) {
        const canvas = document.createElement('canvas');
        const pageWidthPx = Utils.mmToPixels(this.app.engine.pageWidth, 96 * scale);
        const pageHeightPx = Utils.mmToPixels(this.app.engine.pageHeight, 96 * scale);
        canvas.width = pageWidthPx;
        canvas.height = pageHeightPx;

        const ctx = canvas.getContext('2d');
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        const mmScale = pageWidthPx / this.app.engine.pageWidth;
        ctx.scale(mmScale, mmScale);

        for (const obj of this.app.objects) {
            if (obj.visible) obj.draw(ctx);
        }

        Utils.downloadCanvas(canvas, 'design.png');
    }

    exportSVG() {
        const w = this.app.engine.pageWidth;
        const h = this.app.engine.pageHeight;
        let svg = `<?xml version="1.0" encoding="UTF-8"?>\n`;
        svg += `<svg xmlns="http://www.w3.org/2000/svg" width="${w}mm" height="${h}mm" viewBox="0 0 ${w} ${h}">\n`;

        for (const obj of this.app.objects) {
            if (!obj.visible) continue;
            svg += this.objectToSVG(obj);
        }

        const cutPaths = this.app.cutEngine.generateAllCutPaths();
        if (cutPaths.length > 0) {
            svg += `  <g id="cut-lines" stroke="#FF0066" fill="none" stroke-width="0.5">\n`;
            for (const path of cutPaths) {
                svg += this.cutPathToSVG(path);
            }
            svg += `  </g>\n`;
        }

        svg += `</svg>`;
        Utils.downloadFile(svg, 'design.svg', 'image/svg+xml');
    }

    objectToSVG(obj) {
        const transform = obj.rotation ? ` transform="rotate(${obj.rotation} ${obj.getCenter().x} ${obj.getCenter().y})"` : '';
        const fill = obj.fill && obj.fill !== 'none' ? ` fill="${obj.fill}" fill-opacity="${obj.fillOpacity}"` : ' fill="none"';
        const stroke = obj.strokeWidth > 0 ? ` stroke="${obj.stroke}" stroke-width="${obj.strokeWidth}"` : '';

        switch (obj.type) {
            case 'rect':
                return `  <rect x="${obj.x}" y="${obj.y}" width="${obj.width}" height="${obj.height}" rx="${obj.cornerRadius || 0}"${fill}${stroke}${transform}/>\n`;
            case 'circle':
                const cx = obj.x + obj.width / 2;
                const cy = obj.y + obj.height / 2;
                return `  <ellipse cx="${cx}" cy="${cy}" rx="${obj.width / 2}" ry="${obj.height / 2}"${fill}${stroke}${transform}/>\n`;
            case 'line':
                return `  <line x1="${obj.x}" y1="${obj.y}" x2="${obj.x2}" y2="${obj.y2}"${stroke}${transform}/>\n`;
            case 'text':
                return `  <text x="${obj.x + obj.width / 2}" y="${obj.y + obj.height / 2}" font-family="${obj.fontFamily}" font-size="${obj.fontSize}" font-weight="${obj.fontWeight}" text-anchor="middle" dominant-baseline="middle"${fill}${stroke}${transform}>${obj.text}</text>\n`;
            case 'polygon': {
                const points = [];
                for (let i = 0; i < obj.sides; i++) {
                    const angle = (Math.PI * 2 * i) / obj.sides - Math.PI / 2;
                    const px = obj.x + obj.width / 2 + (obj.width / 2) * Math.cos(angle);
                    const py = obj.y + obj.height / 2 + (obj.height / 2) * Math.sin(angle);
                    points.push(`${px},${py}`);
                }
                return `  <polygon points="${points.join(' ')}"${fill}${stroke}${transform}/>\n`;
            }
            case 'star': {
                const starPoints = [];
                for (let i = 0; i < obj.points * 2; i++) {
                    const angle = (Math.PI * i) / obj.points - Math.PI / 2;
                    const r = i % 2 === 0 ? obj.width / 2 : obj.width / 2 * obj.innerRadius;
                    const px = obj.x + obj.width / 2 + r * Math.cos(angle);
                    const py = obj.y + obj.height / 2 + r * Math.sin(angle);
                    starPoints.push(`${px},${py}`);
                }
                return `  <polygon points="${starPoints.join(' ')}"${fill}${stroke}${transform}/>\n`;
            }
            case 'path': {
                if (obj.points.length < 2) return '';
                let d = `M ${obj.x + obj.points[0].x} ${obj.y + obj.points[0].y}`;
                for (let i = 1; i < obj.points.length; i++) {
                    d += ` L ${obj.x + obj.points[i].x} ${obj.y + obj.points[i].y}`;
                }
                if (obj.closed) d += ' Z';
                return `  <path d="${d}"${fill}${stroke}${transform}/>\n`;
            }
            default:
                return '';
        }
    }

    cutPathToSVG(path) {
        if (path.points.length < 2) return '';
        let d = `M ${path.points[0].x} ${path.points[0].y}`;
        for (let i = 1; i < path.points.length; i++) {
            d += ` L ${path.points[i].x} ${path.points[i].y}`;
        }
        if (path.closed) d += ' Z';
        return `    <path d="${d}" stroke-dasharray="3,2"/>\n`;
    }

    exportPDF() {
        const w = this.app.engine.pageWidth;
        const h = this.app.engine.pageHeight;
        const canvas = document.createElement('canvas');
        const dpi = 300;
        canvas.width = Utils.mmToPixels(w, dpi);
        canvas.height = Utils.mmToPixels(h, dpi);

        const ctx = canvas.getContext('2d');
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        const scale = canvas.width / w;
        ctx.scale(scale, scale);

        for (const obj of this.app.objects) {
            if (obj.visible) obj.draw(ctx);
        }

        this.app.cutEngine.generateAllCutPaths();
        this.app.cutEngine.drawCutPaths(ctx);

        Utils.downloadCanvas(canvas, 'design-print.png');
    }

    saveProject() {
        const project = {
            version: '1.0',
            name: this.app.projectName || 'مشروع جديد',
            pageSize: {
                width: this.app.engine.pageWidth,
                height: this.app.engine.pageHeight
            },
            dpi: this.app.engine.dpi,
            objects: this.app.objects.map(obj => obj.serialize()),
            layers: this.app.layerManager.layers,
            cutSettings: {
                offset: this.app.cutEngine.defaultOffset,
                registrationMarks: this.app.cutEngine.registrationMarks,
                cornerStyle: this.app.cutEngine.cornerStyle
            }
        };

        const json = JSON.stringify(project, null, 2);
        Utils.downloadFile(json, (this.app.projectName || 'project') + '.printcut', 'application/json');
    }

    loadProject(jsonString) {
        try {
            const project = JSON.parse(jsonString);
            this.app.projectName = project.name;
            this.app.engine.setPageSize(project.pageSize.width, project.pageSize.height);
            this.app.objects = project.objects.map(data => DesignObject.deserialize(data));

            if (project.layers) {
                this.app.layerManager.layers = project.layers.map(l => Object.assign(new Layer(), l));
                this.app.layerManager.activeLayerId = this.app.layerManager.layers[0]?.id;
            }

            if (project.cutSettings) {
                this.app.cutEngine.defaultOffset = project.cutSettings.offset;
                this.app.cutEngine.registrationMarks = project.cutSettings.registrationMarks;
                this.app.cutEngine.cornerStyle = project.cutSettings.cornerStyle;
            }

            this.app.layerManager.updateUI();
            this.app.history.clear();
            this.app.history.pushState();
            this.app.render();
            return true;
        } catch (e) {
            console.error('Failed to load project:', e);
            alert('فشل في تحميل المشروع');
            return false;
        }
    }
}
