import { useEffect, useRef } from "react";
import type { DependencyList } from "react";
import { BarChart, HeatmapChart } from "echarts/charts";
import { GridComponent, TooltipComponent, VisualMapComponent } from "echarts/components";
import * as echarts from "echarts/core";
import type { EChartsType } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { PERIOD_MONTH } from "./constants";
import { countWan, moneyWan } from "./format";
import type { ContributionHeatmap, RankItem } from "./types";

echarts.use([BarChart, HeatmapChart, GridComponent, TooltipComponent, VisualMapComponent, CanvasRenderer]);

function useChart(
  optionFactory: () => Record<string, unknown>,
  deps: DependencyList,
) {
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!ref.current) {
      return;
    }
    const chart: EChartsType = echarts.init(ref.current);
    chart.setOption(optionFactory());

    const resize = () => chart.resize();
    window.addEventListener("resize", resize);
    return () => {
      window.removeEventListener("resize", resize);
      chart.dispose();
    };
  }, deps);

  return ref;
}

export function RankChart({ items }: { items: RankItem[] }) {
  const ref = useChart(
    () => ({
      grid: { top: 8, right: 88, bottom: 24, left: 138 },
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "shadow" },
        formatter: (params: any) => {
          const item = params?.[0];
          return `${item.name}<br/>总贡献：${moneyWan(Number(item.value) * 10000)}`;
        },
      },
      xAxis: {
        type: "value",
        axisLabel: { formatter: (value: number) => `${value.toFixed(0)}万` },
        splitLine: { lineStyle: { color: "#eef2f7" } },
      },
      yAxis: {
        type: "category",
        inverse: true,
        data: items.map((item) => item.name),
        axisLabel: {
          width: 120,
          overflow: "truncate",
          color: "#334155",
        },
      },
      series: [
        {
          type: "bar",
          data: items.map((item) => Number((item.total_contribution / 10000).toFixed(2))),
          barWidth: 14,
          itemStyle: { color: "#2454d6", borderRadius: [0, 4, 4, 0] },
          label: {
            show: true,
            position: "right",
            color: "#17202f",
            formatter: (params: any) => `${Number(params.value).toLocaleString("zh-CN", { maximumFractionDigits: 1 })}万`,
          },
        },
      ],
    }),
    [items],
  );

  if (!items.length) {
    return <div className="empty-panel">暂无排行图数据</div>;
  }

  return <div ref={ref} className="chart chart-rank" role="img" aria-label="加盟商总贡献排行图" />;
}

export function HeatmapChartView({ heatmap }: { heatmap: ContributionHeatmap | null | undefined }) {
  const values = heatmap?.cells.map((cell) => cell.value / 10000) ?? [];
  const min = Math.min(0, ...values);
  const max = Math.max(0, ...values);
  const ref = useChart(
    () => {
      const provinces = heatmap?.provinces ?? [];
      const weightBands = heatmap?.weight_bands ?? [];
      const cellMap = new Map(
        (heatmap?.cells ?? []).map((cell) => [`${cell.destination_province}::${cell.weight_band}`, cell]),
      );

      return {
        grid: { top: 12, right: 18, bottom: 64, left: 74 },
        tooltip: {
          position: "top",
          formatter: (params: any) => {
            const [x, y] = params.value as [number, number, number];
            const province = provinces[y];
            const weightBand = weightBands[x];
            const cell = cellMap.get(`${province}::${weightBand}`);
            return [
              `${PERIOD_MONTH} / 区域贡献`,
              `目的省份：${province}`,
              `公斤段：${weightBand}`,
              `贡献总额：${moneyWan(cell?.value)}`,
              `票量：${countWan(cell?.ticket_count)}`,
            ].join("<br/>");
          },
        },
        xAxis: {
          type: "category",
          data: weightBands,
          axisLabel: { color: "#334155", interval: 0 },
          splitArea: { show: true },
        },
        yAxis: {
          type: "category",
          inverse: true,
          data: provinces,
          axisLabel: { color: "#334155" },
          splitArea: { show: true },
        },
        visualMap: {
          min,
          max,
          calculable: true,
          orient: "horizontal",
          left: "center",
          bottom: 8,
          text: ["高", "低"],
          inRange: { color: ["#b33a2e", "#f8fafc", "#147a46"] },
        },
        series: [
          {
            type: "heatmap",
            data: provinces.flatMap((province, y) => (
              weightBands.map((weightBand, x) => {
                const cell = cellMap.get(`${province}::${weightBand}`);
                return [x, y, Number(((cell?.value ?? 0) / 10000).toFixed(2))];
              })
            )),
            emphasis: {
              itemStyle: {
                borderColor: "#17202f",
                borderWidth: 1,
              },
            },
          },
        ],
      };
    },
    [heatmap, min, max],
  );

  if (!heatmap?.provinces.length || !heatmap.weight_bands.length) {
    return <div className="empty-panel">暂无热力图数据</div>;
  }

  return <div ref={ref} className="chart chart-heatmap" role="img" aria-label="目的省份与公斤段贡献热力图" />;
}
