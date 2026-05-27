const REG_GROUP_ID = "registration-marks";

export interface RegMarkOptions {
  bedWidthMm: number;
  bedHeightMm: number;
  sizeMm: number;
  thicknessMm: number;
  marginMm: number;
}

/** L-shaped registration marks at four corners (standard print-and-cut). */
export function createRegistrationMarksSvg(opts: RegMarkOptions): string {
  const { bedWidthMm: w, bedHeightMm: h, sizeMm: s, thicknessMm: t, marginMm: m } =
    opts;
  const corners = [
    { x: m, y: m, hx: 1, vy: 1 },
    { x: w - m, y: m, hx: -1, vy: 1 },
    { x: m, y: h - m, hx: 1, vy: -1 },
    { x: w - m, y: h - m, hx: -1, vy: -1 },
  ];

  const marks = corners
    .map(({ x, y, hx, vy }) => {
      const x2 = x + hx * s;
      const y2 = y + vy * s;
      return `<path data-reg-mark="true" d="M ${x} ${y} L ${x2} ${y} M ${x} ${y} L ${x} ${y2}" stroke-width="${t}" />`;
    })
    .join("\n");

  return `<g id="${REG_GROUP_ID}" data-reg-group="true">${marks}</g>`;
}

export function removeRegistrationMarks(svg: SVGSVGElement): void {
  svg.querySelector(`#${REG_GROUP_ID}`)?.remove();
}

export function hasRegistrationMarks(svg: SVGSVGElement): boolean {
  return svg.querySelector(`#${REG_GROUP_ID}`) !== null;
}
