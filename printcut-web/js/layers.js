class Layer {
    constructor(name = 'طبقة جديدة') {
        this.id = Utils.generateId();
        this.name = name;
        this.visible = true;
        this.locked = false;
        this.opacity = 1;
    }
}

class LayerManager {
    constructor(app) {
        this.app = app;
        this.layers = [];
        this.activeLayerId = null;
        this.init();
    }

    init() {
        this.addLayer('الطبقة الرئيسية');
    }

    addLayer(name) {
        const layer = new Layer(name || `طبقة ${this.layers.length + 1}`);
        this.layers.push(layer);
        this.activeLayerId = layer.id;
        this.updateUI();
        return layer;
    }

    deleteLayer(id) {
        if (this.layers.length <= 1) return;
        const index = this.layers.findIndex(l => l.id === id);
        if (index === -1) return;

        this.app.objects = this.app.objects.filter(obj => obj.layerId !== id);
        this.layers.splice(index, 1);

        if (this.activeLayerId === id) {
            this.activeLayerId = this.layers[Math.max(0, index - 1)].id;
        }
        this.updateUI();
        this.app.render();
    }

    duplicateLayer(id) {
        const source = this.layers.find(l => l.id === id);
        if (!source) return;

        const newLayer = this.addLayer(source.name + ' (نسخة)');
        const objectsInLayer = this.app.objects.filter(obj => obj.layerId === id);
        for (const obj of objectsInLayer) {
            const clone = obj.clone();
            clone.layerId = newLayer.id;
            this.app.objects.push(clone);
        }
        this.app.render();
    }

    moveLayerUp(id) {
        const index = this.layers.findIndex(l => l.id === id);
        if (index <= 0) return;
        [this.layers[index - 1], this.layers[index]] = [this.layers[index], this.layers[index - 1]];
        this.updateUI();
        this.app.render();
    }

    moveLayerDown(id) {
        const index = this.layers.findIndex(l => l.id === id);
        if (index >= this.layers.length - 1) return;
        [this.layers[index], this.layers[index + 1]] = [this.layers[index + 1], this.layers[index]];
        this.updateUI();
        this.app.render();
    }

    toggleVisibility(id) {
        const layer = this.layers.find(l => l.id === id);
        if (layer) {
            layer.visible = !layer.visible;
            this.app.objects.forEach(obj => {
                if (obj.layerId === id) obj.visible = layer.visible;
            });
            this.updateUI();
            this.app.render();
        }
    }

    toggleLock(id) {
        const layer = this.layers.find(l => l.id === id);
        if (layer) {
            layer.locked = !layer.locked;
            this.app.objects.forEach(obj => {
                if (obj.layerId === id) obj.locked = layer.locked;
            });
            this.updateUI();
        }
    }

    setActive(id) {
        this.activeLayerId = id;
        this.updateUI();
    }

    getActiveLayer() {
        return this.layers.find(l => l.id === this.activeLayerId);
    }

    getObjectsByLayer() {
        const ordered = [];
        for (const layer of this.layers) {
            if (!layer.visible) continue;
            const layerObjects = this.app.objects.filter(obj => obj.layerId === layer.id);
            ordered.push(...layerObjects);
        }
        return ordered;
    }

    updateUI() {
        const listEl = document.getElementById('layers-list');
        if (!listEl) return;

        listEl.innerHTML = '';
        for (let i = this.layers.length - 1; i >= 0; i--) {
            const layer = this.layers[i];
            const item = document.createElement('div');
            item.className = `layer-item ${layer.id === this.activeLayerId ? 'active' : ''}`;
            item.dataset.layerId = layer.id;

            const objectCount = this.app.objects.filter(obj => obj.layerId === layer.id).length;

            item.innerHTML = `
                <span class="layer-visibility" data-action="visibility">
                    <i class="fas ${layer.visible ? 'fa-eye' : 'fa-eye-slash'}"></i>
                </span>
                <span class="layer-name">${layer.name} (${objectCount})</span>
                <span class="layer-lock" data-action="lock">
                    <i class="fas ${layer.locked ? 'fa-lock' : 'fa-unlock'}"></i>
                </span>
            `;

            item.addEventListener('click', (e) => {
                const action = e.target.closest('[data-action]');
                if (action) {
                    if (action.dataset.action === 'visibility') {
                        this.toggleVisibility(layer.id);
                    } else if (action.dataset.action === 'lock') {
                        this.toggleLock(layer.id);
                    }
                } else {
                    this.setActive(layer.id);
                }
            });

            listEl.appendChild(item);
        }
    }
}
