const Utils = {
    generateId() {
        return 'obj_' + Date.now().toString(36) + Math.random().toString(36).substr(2, 9);
    },

    mmToPixels(mm, dpi = 300) {
        return (mm / 25.4) * dpi;
    },

    pixelsToMm(px, dpi = 300) {
        return (px / dpi) * 25.4;
    },

    degToRad(degrees) {
        return degrees * (Math.PI / 180);
    },

    radToDeg(radians) {
        return radians * (180 / Math.PI);
    },

    clamp(value, min, max) {
        return Math.min(Math.max(value, min), max);
    },

    distance(x1, y1, x2, y2) {
        return Math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2);
    },

    lerp(a, b, t) {
        return a + (b - a) * t;
    },

    pointInRect(px, py, rect) {
        return px >= rect.x && px <= rect.x + rect.width &&
               py >= rect.y && py <= rect.y + rect.height;
    },

    rectIntersects(a, b) {
        return !(a.x + a.width < b.x || b.x + b.width < a.x ||
                 a.y + a.height < b.y || b.y + b.height < a.y);
    },

    rotatePoint(px, py, cx, cy, angle) {
        const cos = Math.cos(angle);
        const sin = Math.sin(angle);
        const dx = px - cx;
        const dy = py - cy;
        return {
            x: cx + dx * cos - dy * sin,
            y: cy + dx * sin + dy * cos
        };
    },

    getBoundingBox(points) {
        let minX = Infinity, minY = Infinity;
        let maxX = -Infinity, maxY = -Infinity;
        for (const p of points) {
            minX = Math.min(minX, p.x);
            minY = Math.min(minY, p.y);
            maxX = Math.max(maxX, p.x);
            maxY = Math.max(maxY, p.y);
        }
        return { x: minX, y: minY, width: maxX - minX, height: maxY - minY };
    },

    snapToGrid(value, gridSize) {
        return Math.round(value / gridSize) * gridSize;
    },

    debounce(fn, delay) {
        let timer;
        return function(...args) {
            clearTimeout(timer);
            timer = setTimeout(() => fn.apply(this, args), delay);
        };
    },

    downloadFile(content, filename, mimeType) {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    },

    downloadCanvas(canvas, filename) {
        const url = canvas.toDataURL('image/png');
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
    },

    pageSizes: {
        a4: { width: 210, height: 297 },
        a3: { width: 297, height: 420 },
        letter: { width: 216, height: 279 },
        a5: { width: 148, height: 210 },
    }
};
