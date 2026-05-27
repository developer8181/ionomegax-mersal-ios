/** Plotter HPGL: 1 unit = 0.025 mm (40 units per mm) */
export const UNITS_PER_MM = 40;

export function mmToUnits(mm: number): number {
  return Math.round(mm * UNITS_PER_MM);
}

export function unitsToMm(units: number): number {
  return units / UNITS_PER_MM;
}
