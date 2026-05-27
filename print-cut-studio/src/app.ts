import { createContourForElement } from "./lib/contour";
import { pathsToHpgl, downloadText } from "./lib/hpgl";
import { extractCutPaths } from "./lib/path-extract";
import {
  createRegistrationMarksSvg,
  removeRegistrationMarks,
} from "./lib/registration";
import { downloadSvg, serializeSvg } from "./lib/svg-export";

let bedWidthMm = 300;
let bedHeightMm = 400;
let selected: SVGElement | null = null;
let dragState: { el: SVGElement; ox: number; oy: number; mx: number; my: number } | null =
  null;

const svg = (): SVGSVGElement =>
  document.getElementById("design-canvas") as unknown as SVGSVGElement;
const designLayer = () =>
  svg().querySelector("#design-layer") as SVGGElement | null;

function initCanvas(): void {
  const el = svg();
  el.innerHTML = "";
  el.setAttribute("width", `${bedWidthMm}mm`);
  el.setAttribute("height", `${bedHeightMm}mm`);
  el.setAttribute("viewBox", `0 0 ${bedWidthMm} ${bedHeightMm}`);

  const outline = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  outline.setAttribute("class", "bed-outline");
  outline.setAttribute("x", "0");
  outline.setAttribute("y", "0");
  outline.setAttribute("width", String(bedWidthMm));
  outline.setAttribute("height", String(bedHeightMm));

  const layer = document.createElementNS("http://www.w3.org/2000/svg", "g");
  layer.setAttribute("id", "design-layer");

  const contourLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");
  contourLayer.setAttribute("id", "contour-layer");

  el.append(outline, layer, contourLayer);
  clearSelection();
}

function nextId(): string {
  return `el-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
}

function makeSelectable(el: SVGElement, layerMode = "both"): void {
  el.setAttribute("data-selectable", "true");
  el.setAttribute("data-layer-mode", layerMode);
  el.setAttribute("id", nextId());
  el.addEventListener("pointerdown", onPointerDown);
}

function onPointerDown(e: PointerEvent): void {
  const target = (e.target as SVGElement).closest(
    "[data-selectable]"
  ) as SVGElement | null;
  if (!target || target.getAttribute("data-reg-mark")) return;
  e.stopPropagation();
  selectElement(target);
  const pt = clientToSvg(e.clientX, e.clientY);
  dragState = {
    el: target,
    ox: parseFloat(target.getAttribute("data-x") ?? "0") || getTranslateX(target),
    oy: parseFloat(target.getAttribute("data-y") ?? "0") || getTranslateY(target),
    mx: pt.x,
    my: pt.y,
  };
  target.setPointerCapture(e.pointerId);
}

function onPointerMove(e: PointerEvent): void {
  if (!dragState) return;
  const pt = clientToSvg(e.clientX, e.clientY);
  const dx = pt.x - dragState.mx;
  const dy = pt.y - dragState.my;
  const nx = dragState.ox + dx;
  const ny = dragState.oy + dy;
  setTranslate(dragState.el, nx, ny);
  dragState.el.setAttribute("data-x", String(nx));
  dragState.el.setAttribute("data-y", String(ny));
}

function onPointerUp(): void {
  dragState = null;
}

function getTranslateX(el: SVGElement): number {
  const t = el.getAttribute("transform") ?? "";
  const m = /translate\(\s*([-\d.]+)/.exec(t);
  return m ? parseFloat(m[1]) : 0;
}

function getTranslateY(el: SVGElement): number {
  const t = el.getAttribute("transform") ?? "";
  const m = /translate\(\s*[-\d.]+\s*,?\s*([-\d.]+)/.exec(t);
  return m ? parseFloat(m[1]) : 0;
}

function setTranslate(el: SVGElement, x: number, y: number): void {
  el.setAttribute("transform", `translate(${x}, ${y})`);
}

function clientToSvg(clientX: number, clientY: number): { x: number; y: number } {
  const el = svg();
  const pt = el.createSVGPoint();
  pt.x = clientX;
  pt.y = clientY;
  const ctm = el.getScreenCTM();
  if (!ctm) return { x: 0, y: 0 };
  const svgPt = pt.matrixTransform(ctm.inverse());
  return { x: svgPt.x, y: svgPt.y };
}

function selectElement(el: SVGElement | null): void {
  selected?.classList.remove("selected");
  selected = el;
  selected?.classList.add("selected");
  const info = document.getElementById("selection-info");
  const del = document.getElementById("btn-delete") as HTMLButtonElement;
  if (!el) {
    if (info) info.textContent = "لا يوجد تحديد";
    if (del) del.disabled = true;
    return;
  }
  const mode = el.getAttribute("data-layer-mode") ?? "both";
  if (info) info.textContent = `${el.tagName} — ${mode}`;
  if (del) del.disabled = false;
}

function clearSelection(): void {
  selectElement(null);
}

function addRect(): void {
  const r = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  r.setAttribute("x", String(bedWidthMm / 2 - 40));
  r.setAttribute("y", String(bedHeightMm / 2 - 25));
  r.setAttribute("width", "80");
  r.setAttribute("height", "50");
  r.setAttribute("fill", "#3b82f6");
  r.setAttribute("stroke", "#1e40af");
  r.setAttribute("stroke-width", "0.5");
  makeSelectable(r);
  designLayer()?.appendChild(r);
  selectElement(r);
}

function addCircle(): void {
  const c = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  c.setAttribute("cx", String(bedWidthMm / 2));
  c.setAttribute("cy", String(bedHeightMm / 2));
  c.setAttribute("r", "35");
  c.setAttribute("fill", "#a855f7");
  c.setAttribute("stroke", "#6b21a8");
  c.setAttribute("stroke-width", "0.5");
  makeSelectable(c);
  designLayer()?.appendChild(c);
  selectElement(c);
}

function addText(): void {
  const t = document.createElementNS("http://www.w3.org/2000/svg", "text");
  t.setAttribute("x", String(bedWidthMm / 2 - 30));
  t.setAttribute("y", String(bedHeightMm / 2));
  t.setAttribute("font-size", "14");
  t.setAttribute("font-family", "Arial, sans-serif");
  t.setAttribute("fill", "#111");
  t.textContent = "ملصق";
  makeSelectable(t);
  designLayer()?.appendChild(t);
  selectElement(t);
}

async function importSvgFile(file: File): Promise<void> {
  const text = await file.text();
  const parser = new DOMParser();
  const doc = parser.parseFromString(text, "image/svg+xml");
  const imported = doc.querySelector("svg");
  if (!imported) {
    alert("ملف SVG غير صالح");
    return;
  }
  const layer = designLayer();
  if (!layer) return;
  imported.querySelectorAll("path, rect, circle, ellipse, line, polyline, polygon, text").forEach((node) => {
    const cloned = node.cloneNode(true) as SVGElement;
    makeSelectable(cloned, "both");
    layer.appendChild(cloned);
  });
}

function applyLayerModeToSelected(): void {
  if (!selected) return;
  const mode = (document.getElementById("layer-mode") as HTMLSelectElement).value;
  selected.setAttribute("data-layer-mode", mode);
  if (mode === "cut") {
    selected.setAttribute("fill", "none");
  }
  selectElement(selected);
}

function generateContour(): void {
  if (!selected) {
    alert("حدد عنصراً لإنشاء خط القص حوله");
    return;
  }
  const offset = parseFloat(
    (document.getElementById("contour-offset") as HTMLInputElement).value
  );
  const contour = createContourForElement(
    selected as SVGGraphicsElement,
    offset
  );
  if (!contour) return;
  document.getElementById("contour-layer")?.appendChild(contour);
}

function addRegMarks(): void {
  removeRegistrationMarks(svg());
  const size = parseFloat((document.getElementById("reg-size") as HTMLInputElement).value);
  const thickness = parseFloat(
    (document.getElementById("reg-thickness") as HTMLInputElement).value
  );
  const margin = parseFloat((document.getElementById("reg-margin") as HTMLInputElement).value);
  const fragment = document.createRange().createContextualFragment(
    createRegistrationMarksSvg({
      bedWidthMm,
      bedHeightMm,
      sizeMm: size,
      thicknessMm: thickness,
      marginMm: margin,
    })
  );
  svg().appendChild(fragment);
}

function deleteSelected(): void {
  if (!selected) return;
  selected.remove();
  clearSelection();
}

function reorderSelected(toFront: boolean): void {
  if (!selected) return;
  const parent = selected.parentElement;
  if (!parent) return;
  if (toFront) parent.appendChild(selected);
  else parent.insertBefore(selected, parent.firstChild);
}

function resizeBed(): void {
  bedWidthMm = parseFloat((document.getElementById("bed-width") as HTMLInputElement).value);
  bedHeightMm = parseFloat((document.getElementById("bed-height") as HTMLInputElement).value);
  const layer = designLayer();
  const contour = svg().querySelector("#contour-layer");
  const children = layer ? Array.from(layer.childNodes) : [];
  const contours = contour ? Array.from(contour.childNodes) : [];
  initCanvas();
  children.forEach((c) => designLayer()?.appendChild(c));
  contours.forEach((c) => document.getElementById("contour-layer")?.appendChild(c));
}

function bindUi(): void {
  document.getElementById("btn-add-rect")?.addEventListener("click", addRect);
  document.getElementById("btn-add-circle")?.addEventListener("click", addCircle);
  document.getElementById("btn-add-text")?.addEventListener("click", addText);
  document.getElementById("btn-resize-bed")?.addEventListener("click", resizeBed);
  document.getElementById("btn-contour")?.addEventListener("click", generateContour);
  document.getElementById("btn-reg-marks")?.addEventListener("click", addRegMarks);
  document.getElementById("btn-clear-reg")?.addEventListener("click", () =>
    removeRegistrationMarks(svg())
  );
  document.getElementById("btn-delete")?.addEventListener("click", deleteSelected);
  document.getElementById("btn-bring-front")?.addEventListener("click", () =>
    reorderSelected(true)
  );
  document.getElementById("btn-send-back")?.addEventListener("click", () =>
    reorderSelected(false)
  );
  document.getElementById("layer-mode")?.addEventListener("change", applyLayerModeToSelected);

  document.getElementById("import-svg")?.addEventListener("change", (e) => {
    const input = e.target as HTMLInputElement;
    const file = input.files?.[0];
    if (file) void importSvgFile(file);
    input.value = "";
  });

  document.getElementById("btn-export-print-svg")?.addEventListener("click", () => {
    downloadSvg("print.svg", serializeSvg(svg(), "print"));
  });
  document.getElementById("btn-export-cut-svg")?.addEventListener("click", () => {
    downloadSvg("cut.svg", serializeSvg(svg(), "cut"));
  });
  document.getElementById("btn-export-hpgl")?.addEventListener("click", () => {
    const paths = extractCutPaths(svg());
    if (paths.length === 0) {
      alert("لا توجد مسارات قص. أنشئ خط قص أو عيّن طبقة «قص فقط».");
      return;
    }
    const hpgl = pathsToHpgl(paths, { bedHeightMm });
    downloadText("cut.hpgl", hpgl, "text/plain");
  });
  document.getElementById("btn-print")?.addEventListener("click", () => window.print());

  svg().addEventListener("pointerdown", (e) => {
    if ((e.target as Element) === svg() || (e.target as Element).classList.contains("bed-outline")) {
      clearSelection();
    }
  });
  window.addEventListener("pointermove", onPointerMove);
  window.addEventListener("pointerup", onPointerUp);
}

export function startApp(): void {
  initCanvas();
  bindUi();
}
