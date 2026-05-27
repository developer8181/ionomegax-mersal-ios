class DesignObject {
    constructor(type, props = {}) {
        this.id = Utils.generateId();
        this.type = type;
        this.x = props.x || 0;
        this.y = props.y || 0;
        this.width = props.width || 100;
        this.height = props.height || 100;
        this.rotation = props.rotation || 0;
        this.scaleX = props.scaleX || 1;
        this.scaleY = props.scaleY || 1;
        this.fill = props.fill || '#ffffff';
        this.fillOpacity = props.fillOpacity !== undefined ? props.fillOpacity : 1;
        this.stroke = props.stroke || '#000000';
        this.strokeWidth = props.strokeWidth !== undefined ? props.strokeWidth : 1;
        this.strokeStyle = props.strokeStyle || 'solid';
        this.visible = props.visible !== undefined ? props.visible : true;
        this.locked = props.locked || false;
        this.name = props.name || type;
        this.layerId = props.layerId || null;
        this.selected = false;
        this.hasCutPath = props.hasCutPath || false;
        this.cutOffset = props.cutOffset || 2;
    }

    getBounds() {
        return {
            x: this.x,
            y: this.y,
            width: this.width * this.scaleX,
            height: this.height * this.scaleY
        };
    }

    getCenter() {
        return {
            x: this.x + (this.width * this.scaleX) / 2,
            y: this.y + (this.height * this.scaleY) / 2
        };
    }

    containsPoint(px, py) {
        const cos = Math.cos(-Utils.degToRad(this.rotation));
        const sin = Math.sin(-Utils.degToRad(this.rotation));
        const center = this.getCenter();
        const dx = px - center.x;
        const dy = py - center.y;
        const localX = dx * cos - dy * sin + center.x;
        const localY = dx * sin + dy * cos + center.y;
        const bounds = this.getBounds();
        return Utils.pointInRect(localX, localY, bounds);
    }

    clone() {
        const cloned = new this.constructor(this.type, { ...this });
        cloned.id = Utils.generateId();
        cloned.x += 10;
        cloned.y += 10;
        return cloned;
    }

    serialize() {
        return { ...this };
    }

    static deserialize(data) {
        switch (data.type) {
            case 'rect': return Object.assign(new RectObject(), data);
            case 'circle': return Object.assign(new CircleObject(), data);
            case 'line': return Object.assign(new LineObject(), data);
            case 'text': return Object.assign(new TextObject(), data);
            case 'image': return Object.assign(new ImageObject(), data);
            case 'polygon': return Object.assign(new PolygonObject(), data);
            case 'star': return Object.assign(new StarObject(), data);
            case 'path': return Object.assign(new PathObject(), data);
            default: return Object.assign(new DesignObject(data.type), data);
        }
    }
}

class RectObject extends DesignObject {
    constructor(props = {}) {
        super('rect', props);
        this.cornerRadius = props.cornerRadius || 0;
        this.name = props.name || 'مستطيل';
    }

    draw(ctx) {
        ctx.save();
        const center = this.getCenter();
        ctx.translate(center.x, center.y);
        ctx.rotate(Utils.degToRad(this.rotation));
        ctx.scale(this.scaleX, this.scaleY);

        const w = this.width;
        const h = this.height;
        const r = this.cornerRadius;

        ctx.beginPath();
        if (r > 0) {
            ctx.roundRect(-w / 2, -h / 2, w, h, r);
        } else {
            ctx.rect(-w / 2, -h / 2, w, h);
        }

        if (this.fill && this.fill !== 'none') {
            ctx.globalAlpha = this.fillOpacity;
            ctx.fillStyle = this.fill;
            ctx.fill();
        }

        if (this.strokeWidth > 0) {
            ctx.globalAlpha = 1;
            ctx.strokeStyle = this.stroke;
            ctx.lineWidth = this.strokeWidth;
            this.applyStrokeStyle(ctx);
            ctx.stroke();
        }

        ctx.restore();
    }

    applyStrokeStyle(ctx) {
        switch (this.strokeStyle) {
            case 'dashed': ctx.setLineDash([8, 4]); break;
            case 'dotted': ctx.setLineDash([2, 4]); break;
            default: ctx.setLineDash([]); break;
        }
    }
}

class CircleObject extends DesignObject {
    constructor(props = {}) {
        super('circle', props);
        this.name = props.name || 'دائرة';
    }

    draw(ctx) {
        ctx.save();
        const center = this.getCenter();
        ctx.translate(center.x, center.y);
        ctx.rotate(Utils.degToRad(this.rotation));
        ctx.scale(this.scaleX, this.scaleY);

        const rx = this.width / 2;
        const ry = this.height / 2;

        ctx.beginPath();
        ctx.ellipse(0, 0, rx, ry, 0, 0, Math.PI * 2);

        if (this.fill && this.fill !== 'none') {
            ctx.globalAlpha = this.fillOpacity;
            ctx.fillStyle = this.fill;
            ctx.fill();
        }

        if (this.strokeWidth > 0) {
            ctx.globalAlpha = 1;
            ctx.strokeStyle = this.stroke;
            ctx.lineWidth = this.strokeWidth;
            this.applyStrokeStyle(ctx);
            ctx.stroke();
        }

        ctx.restore();
    }

    applyStrokeStyle(ctx) {
        switch (this.strokeStyle) {
            case 'dashed': ctx.setLineDash([8, 4]); break;
            case 'dotted': ctx.setLineDash([2, 4]); break;
            default: ctx.setLineDash([]); break;
        }
    }

    containsPoint(px, py) {
        const center = this.getCenter();
        const rx = (this.width * this.scaleX) / 2;
        const ry = (this.height * this.scaleY) / 2;
        const dx = px - center.x;
        const dy = py - center.y;
        return (dx * dx) / (rx * rx) + (dy * dy) / (ry * ry) <= 1;
    }
}

class LineObject extends DesignObject {
    constructor(props = {}) {
        super('line', props);
        this.x2 = props.x2 || this.x + 100;
        this.y2 = props.y2 || this.y;
        this.name = props.name || 'خط';
    }

    draw(ctx) {
        ctx.save();
        ctx.beginPath();
        ctx.moveTo(this.x, this.y);
        ctx.lineTo(this.x2, this.y2);
        ctx.strokeStyle = this.stroke;
        ctx.lineWidth = this.strokeWidth;
        this.applyStrokeStyle(ctx);
        ctx.stroke();
        ctx.restore();
    }

    applyStrokeStyle(ctx) {
        switch (this.strokeStyle) {
            case 'dashed': ctx.setLineDash([8, 4]); break;
            case 'dotted': ctx.setLineDash([2, 4]); break;
            default: ctx.setLineDash([]); break;
        }
    }

    getBounds() {
        const minX = Math.min(this.x, this.x2);
        const minY = Math.min(this.y, this.y2);
        const maxX = Math.max(this.x, this.x2);
        const maxY = Math.max(this.y, this.y2);
        return { x: minX, y: minY, width: maxX - minX || 1, height: maxY - minY || 1 };
    }

    getCenter() {
        return { x: (this.x + this.x2) / 2, y: (this.y + this.y2) / 2 };
    }

    containsPoint(px, py) {
        const dist = this.distToLine(px, py, this.x, this.y, this.x2, this.y2);
        return dist < 5 + this.strokeWidth;
    }

    distToLine(px, py, x1, y1, x2, y2) {
        const dx = x2 - x1;
        const dy = y2 - y1;
        const lenSq = dx * dx + dy * dy;
        if (lenSq === 0) return Utils.distance(px, py, x1, y1);
        let t = ((px - x1) * dx + (py - y1) * dy) / lenSq;
        t = Utils.clamp(t, 0, 1);
        return Utils.distance(px, py, x1 + t * dx, y1 + t * dy);
    }
}

class TextObject extends DesignObject {
    constructor(props = {}) {
        super('text', props);
        this.text = props.text || 'نص جديد';
        this.fontFamily = props.fontFamily || 'Cairo';
        this.fontSize = props.fontSize || 24;
        this.fontWeight = props.fontWeight || 'normal';
        this.fontStyle = props.fontStyle || 'normal';
        this.textDecoration = props.textDecoration || 'none';
        this.textAlign = props.textAlign || 'right';
        this.name = props.name || 'نص';
        this.fill = props.fill || '#000000';
    }

    draw(ctx) {
        ctx.save();
        const center = this.getCenter();
        ctx.translate(center.x, center.y);
        ctx.rotate(Utils.degToRad(this.rotation));

        ctx.font = `${this.fontStyle} ${this.fontWeight} ${this.fontSize}px "${this.fontFamily}"`;
        ctx.textAlign = this.textAlign === 'right' ? 'right' : this.textAlign === 'left' ? 'left' : 'center';
        ctx.textBaseline = 'middle';

        if (this.fill && this.fill !== 'none') {
            ctx.globalAlpha = this.fillOpacity;
            ctx.fillStyle = this.fill;
            ctx.fillText(this.text, 0, 0);
        }

        if (this.strokeWidth > 0 && this.stroke !== 'none') {
            ctx.globalAlpha = 1;
            ctx.strokeStyle = this.stroke;
            ctx.lineWidth = this.strokeWidth;
            ctx.strokeText(this.text, 0, 0);
        }

        const metrics = ctx.measureText(this.text);
        this.width = metrics.width;
        this.height = this.fontSize * 1.2;

        ctx.restore();
    }
}

class ImageObject extends DesignObject {
    constructor(props = {}) {
        super('image', props);
        this.src = props.src || '';
        this.imageElement = null;
        this.name = props.name || 'صورة';
        this.loaded = false;
    }

    loadImage(src) {
        return new Promise((resolve, reject) => {
            this.src = src;
            this.imageElement = new Image();
            this.imageElement.onload = () => {
                this.loaded = true;
                if (!this.width || this.width === 100) {
                    this.width = this.imageElement.naturalWidth;
                    this.height = this.imageElement.naturalHeight;
                }
                resolve(this);
            };
            this.imageElement.onerror = reject;
            this.imageElement.src = src;
        });
    }

    draw(ctx) {
        if (!this.loaded || !this.imageElement) return;

        ctx.save();
        const center = this.getCenter();
        ctx.translate(center.x, center.y);
        ctx.rotate(Utils.degToRad(this.rotation));
        ctx.scale(this.scaleX, this.scaleY);
        ctx.globalAlpha = this.fillOpacity;
        ctx.drawImage(this.imageElement, -this.width / 2, -this.height / 2, this.width, this.height);
        ctx.restore();
    }
}

class PolygonObject extends DesignObject {
    constructor(props = {}) {
        super('polygon', props);
        this.sides = props.sides || 6;
        this.name = props.name || 'مضلع';
    }

    draw(ctx) {
        ctx.save();
        const center = this.getCenter();
        ctx.translate(center.x, center.y);
        ctx.rotate(Utils.degToRad(this.rotation));
        ctx.scale(this.scaleX, this.scaleY);

        const rx = this.width / 2;
        const ry = this.height / 2;

        ctx.beginPath();
        for (let i = 0; i < this.sides; i++) {
            const angle = (Math.PI * 2 * i) / this.sides - Math.PI / 2;
            const x = rx * Math.cos(angle);
            const y = ry * Math.sin(angle);
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.closePath();

        if (this.fill && this.fill !== 'none') {
            ctx.globalAlpha = this.fillOpacity;
            ctx.fillStyle = this.fill;
            ctx.fill();
        }

        if (this.strokeWidth > 0) {
            ctx.globalAlpha = 1;
            ctx.strokeStyle = this.stroke;
            ctx.lineWidth = this.strokeWidth;
            ctx.stroke();
        }

        ctx.restore();
    }
}

class StarObject extends DesignObject {
    constructor(props = {}) {
        super('star', props);
        this.points = props.points || 5;
        this.innerRadius = props.innerRadius || 0.4;
        this.name = props.name || 'نجمة';
    }

    draw(ctx) {
        ctx.save();
        const center = this.getCenter();
        ctx.translate(center.x, center.y);
        ctx.rotate(Utils.degToRad(this.rotation));
        ctx.scale(this.scaleX, this.scaleY);

        const outerRx = this.width / 2;
        const outerRy = this.height / 2;
        const innerRx = outerRx * this.innerRadius;
        const innerRy = outerRy * this.innerRadius;

        ctx.beginPath();
        for (let i = 0; i < this.points * 2; i++) {
            const angle = (Math.PI * i) / this.points - Math.PI / 2;
            const rx = i % 2 === 0 ? outerRx : innerRx;
            const ry = i % 2 === 0 ? outerRy : innerRy;
            const x = rx * Math.cos(angle);
            const y = ry * Math.sin(angle);
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.closePath();

        if (this.fill && this.fill !== 'none') {
            ctx.globalAlpha = this.fillOpacity;
            ctx.fillStyle = this.fill;
            ctx.fill();
        }

        if (this.strokeWidth > 0) {
            ctx.globalAlpha = 1;
            ctx.strokeStyle = this.stroke;
            ctx.lineWidth = this.strokeWidth;
            ctx.stroke();
        }

        ctx.restore();
    }
}

class PathObject extends DesignObject {
    constructor(props = {}) {
        super('path', props);
        this.points = props.points || [];
        this.closed = props.closed || false;
        this.name = props.name || 'مسار';
    }

    draw(ctx) {
        if (this.points.length < 2) return;

        ctx.save();
        ctx.translate(this.x, this.y);
        ctx.rotate(Utils.degToRad(this.rotation));

        ctx.beginPath();
        ctx.moveTo(this.points[0].x, this.points[0].y);
        for (let i = 1; i < this.points.length; i++) {
            const p = this.points[i];
            if (p.cp1 && p.cp2) {
                ctx.bezierCurveTo(p.cp1.x, p.cp1.y, p.cp2.x, p.cp2.y, p.x, p.y);
            } else {
                ctx.lineTo(p.x, p.y);
            }
        }
        if (this.closed) ctx.closePath();

        if (this.fill && this.fill !== 'none' && this.closed) {
            ctx.globalAlpha = this.fillOpacity;
            ctx.fillStyle = this.fill;
            ctx.fill();
        }

        if (this.strokeWidth > 0) {
            ctx.globalAlpha = 1;
            ctx.strokeStyle = this.stroke;
            ctx.lineWidth = this.strokeWidth;
            ctx.stroke();
        }

        ctx.restore();
    }

    getBounds() {
        if (this.points.length === 0) return { x: this.x, y: this.y, width: 0, height: 0 };
        const bounds = Utils.getBoundingBox(this.points);
        return {
            x: this.x + bounds.x,
            y: this.y + bounds.y,
            width: bounds.width,
            height: bounds.height
        };
    }
}
