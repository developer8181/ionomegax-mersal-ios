import type { HpglPath, HpglPoint } from "./hpgl";
import { isContourElement } from "./contour";

/** Extract polylines from cut-layer paths for HPGL export. */
export function extractCutPaths(svg: SVGSVGElement): HpglPath[] {
  const paths: HpglPath[] = [];
  const candidates = svg.querySelectorAll(
    '[data-layer-mode="cut"], [data-contour="true"], [data-reg-mark="true"]'
  );

  candidates.forEach((el) => {
    if (el instanceof SVGPathElement) {
      const pts = samplePathElement(el, 40);
      if (pts.length >= 2) {
        paths.push({ points: pts, closed: true });
      }
    } else if (
      el instanceof SVGRectElement ||
      el instanceof SVGCircleElement ||
      el instanceof SVGLineElement
    ) {
      const pts = elementToPolygon(el);
      if (pts.length >= 2) paths.push({ points: pts, closed: true });
    }
  });

  return paths;
}

function samplePathElement(path: SVGPathElement, samples: number): HpglPoint[] {
  const len = path.getTotalLength();
  if (len === 0) return [];
  const pts: HpglPoint[] = [];
  for (let i = 0; i <= samples; i++) {
    const p = path.getPointAtLength((len * i) / samples);
    pts.push({ x: p.x, y: p.y });
  }
  return pts;
}

function elementToPolygon(el: SVGGraphicsElement): HpglPoint[] {
  if (el instanceof SVGRectElement) {
    const x = num(el.getAttribute("x"));
    const y = num(el.getAttribute("y"));
    const w = num(el.getAttribute("width"));
    const h = num(el.getAttribute("height"));
    return rectPoints(x, y, w, h);
  }
  if (el instanceof SVGCircleElement) {
    const cx = num(el.getAttribute("cx"));
    const cy = num(el.getAttribute("cy"));
    const r = num(el.getAttribute("r"));
    const pts: HpglPoint[] = [];
    for (let i = 0; i < 32; i++) {
      const a = (2 * Math.PI * i) / 32;
      pts.push({ x: cx + r * Math.cos(a), y: cy + r * Math.sin(a) });
    }
    return pts;
  }
  if (el instanceof SVGLineElement) {
    return [
      { x: num(el.getAttribute("x1")), y: num(el.getAttribute("y1")) },
      { x: num(el.getAttribute("x2")), y: num(el.getAttribute("y2")) },
    ];
  }
  if (el instanceof SVGPathElement && !isContourElement(el)) {
    return samplePathElement(el, 32);
  }
  return [];
}

function rectPoints(x: number, y: number, w: number, h: number): HpglPoint[] {
  return [
    { x, y },
    { x: x + w, y },
    { x: x + w, y: y + h },
    { x, y: y + h },
    { x, y },
  ];
}

function num(v: string | null): number {
  return v ? parseFloat(v) : 0;
}
