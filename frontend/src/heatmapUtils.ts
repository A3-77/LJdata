import { WEIGHT_BANDS } from "./constants";
import type { ContributionHeatmap } from "./types";

export function sumHeatmapByProvince(heatmap: ContributionHeatmap | null | undefined) {
  const totals = new Map<string, { name: string; value: number; tickets: number; weight: number }>();
  for (const cell of heatmap?.cells ?? []) {
    const current = totals.get(cell.destination_province) ?? {
      name: cell.destination_province,
      value: 0,
      tickets: 0,
      weight: 0,
    };
    current.value += cell.value;
    current.tickets += cell.ticket_count ?? 0;
    current.weight += cell.weight_total ?? 0;
    totals.set(cell.destination_province, current);
  }
  return [...totals.values()].sort((a, b) => Math.abs(b.value) - Math.abs(a.value));
}

export function sumHeatmapByWeightBand(heatmap: ContributionHeatmap | null | undefined) {
  const totals = new Map<string, { name: string; value: number; tickets: number; weight: number }>();
  for (const cell of heatmap?.cells ?? []) {
    const current = totals.get(cell.weight_band) ?? {
      name: cell.weight_band,
      value: 0,
      tickets: 0,
      weight: 0,
    };
    current.value += cell.value;
    current.tickets += cell.ticket_count ?? 0;
    current.weight += cell.weight_total ?? 0;
    totals.set(cell.weight_band, current);
  }
  return WEIGHT_BANDS
    .map((weightBand) => totals.get(weightBand))
    .filter((item): item is { name: string; value: number; tickets: number; weight: number } => Boolean(item));
}
