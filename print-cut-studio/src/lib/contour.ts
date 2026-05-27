const CONTOUR_ATTR = "data-contour";

/** Approximate contour by stroking shape bounds with offset (mm). */
export function createContourForElement(
  el: SVGGraphicsElement,
  offsetMm: number
): SVGPathElement | null {
  const bbox = el.getBBox();
  if (bbox.width <= 0 && bbox.height <= 0) return null;

  const pad = offsetMm;
  const x = bbox.x - pad;
  const y = bbox.y - pad;
  const w = bbox.width + pad * 2;
  const h = bbox.height + pad * 2;
  const r = Math.min(w, h) * 0.08;

  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute(CONTOUR_ATTR, "true");
  path.setAttribute("data-layer-mode", "cut");
  path.setAttribute(
    "d",
    roundedRectPath(x, y, w, h, Math.min(r, pad * 2))
  );
  path.setAttribute("stroke-width", "0.25");
  path.setAttribute("fill", "none");
  return path;
}

function roundedRectPath(
  x: number,
  y: number,
  w: number,
  h: number,
  r: number
): string {
  r = Math.max(0, Math.min(r, w / 2, h / 2));
  if (r === 0) {
    return `M ${x} ${y} H ${x + w} V ${y + h} H ${x} Z`;
  }
  return [
    `M ${x + r} ${y}`,
    `H ${x + w - r}`,
    `Q ${x + w} ${y} ${x + w} ${y + r}`,
    `V ${y + h - r}`,
    `Q ${x + w} ${y + h} ${x + w - r} ${y + h}`,
    `H ${x + r}`,
    `Q ${x} ${y + h} ${x} ${y + h - r}`,
    `V ${y + r}`,
    `Q ${x} ${y} ${x + r} ${y}`,
    "Z",
  ].join(" ");
}

export function isContourElement(el: Element): boolean {
  return el.getAttribute(CONTOUR_ATTR) === "true";
}
