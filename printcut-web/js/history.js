class HistoryManager {
    constructor(app) {
        this.app = app;
        this.states = [];
        this.currentIndex = -1;
        this.maxStates = 50;
    }

    pushState() {
        this.states = this.states.slice(0, this.currentIndex + 1);

        const state = {
            objects: this.app.objects.map(obj => obj.serialize()),
            timestamp: Date.now()
        };

        this.states.push(state);
        if (this.states.length > this.maxStates) {
            this.states.shift();
        }
        this.currentIndex = this.states.length - 1;
    }

    undo() {
        if (this.currentIndex <= 0) return;
        this.currentIndex--;
        this.restoreState(this.states[this.currentIndex]);
    }

    redo() {
        if (this.currentIndex >= this.states.length - 1) return;
        this.currentIndex++;
        this.restoreState(this.states[this.currentIndex]);
    }

    restoreState(state) {
        this.app.objects = state.objects.map(data => DesignObject.deserialize(data));
        this.app.clearSelection();
        this.app.layerManager.updateUI();
        this.app.render();
    }

    canUndo() {
        return this.currentIndex > 0;
    }

    canRedo() {
        return this.currentIndex < this.states.length - 1;
    }

    clear() {
        this.states = [];
        this.currentIndex = -1;
    }
}
