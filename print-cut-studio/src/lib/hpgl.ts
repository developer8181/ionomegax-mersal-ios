import { mmToUnits } from "./units";

export interface HpglPoint {
  x: number;
  y: number;
}

export interface HpglPath {
  points: HpglPoint[];
  closed?: boolean;
}

/** Build HPGL-2 style command string from paths in mm (origin top-left, Y down). */
export function pathsToHpgl(
  paths: HpglPath[],
  options: { bedHeightMm: number } = { bedHeightMm: 400 }
): string {
  const lines: string[] = ["IN;", "SP1;"];
  const flipY = (y: number) => options.bedHeightMm - y;

  for (const path of paths) {
    if (path.points.length < 2) continue;
    const first = path.points[0];
    lines.push(
      `PU${mmToUnits(first.x)},${mmToUnits(flipY(first.y))};`
    );
    for (let i = 1; i < path.points.length; i++) {
      const p = path.points[i];
      lines.push(`PD${mmToUnits(p.x)},${mmToUnits(flipY(p.y))};`);
    }
    if (path.closed && path.points.length > 2) {
      lines.push(
        `PD${mmToUnits(first.x)},${mmToUnits(flipY(first.y))};`
      );
    }
    lines.push("PU;");
  }
  lines.push("SP0;");
  return lines.join("\n");
}

export function downloadText(filename: string, content: string, mime: string): void {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
