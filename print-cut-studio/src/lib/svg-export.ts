export type ExportMode = "print" | "cut" | "all";

export function serializeSvg(
  svg: SVGSVGElement,
  mode: ExportMode
): string {
  const clone = svg.cloneNode(true) as SVGSVGElement;
  filterByMode(clone, mode);
  clone.removeAttribute("class");
  const w = svg.getAttribute("width") ?? "300mm";
  const h = svg.getAttribute("height") ?? "400mm";
  clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
  clone.setAttribute("width", w);
  clone.setAttribute("height", h);
  const xml = new XMLSerializer().serializeToString(clone);
  return `<?xml version="1.0" encoding="UTF-8"?>\n${xml}`;
}

function filterByMode(root: SVGSVGElement, mode: ExportMode): void {
  const all = root.querySelectorAll("[data-layer-mode]");
  all.forEach((el) => {
    const layer = el.getAttribute("data-layer-mode");
    if (mode === "print" && layer === "cut") {
      el.remove();
    } else if (mode === "cut" && layer === "print") {
      el.remove();
    }
  });
  if (mode === "cut") {
    root.querySelectorAll("[data-selectable]").forEach((el) => {
      if (el.getAttribute("data-layer-mode") !== "cut" && !el.hasAttribute("data-contour")) {
        const modeAttr = el.getAttribute("data-layer-mode");
        if (modeAttr === "both" || !modeAttr) {
          /* keep geometry for cut export if marked both */
        } else {
          el.remove();
        }
      }
    });
  }
}

export function downloadSvg(filename: string, content: string): void {
  const blob = new Blob([content], { type: "image/svg+xml;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
