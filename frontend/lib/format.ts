export function fmt(n: number, digits = 2) {
  return Number.isFinite(n) ? n.toFixed(digits) : "-";
}
