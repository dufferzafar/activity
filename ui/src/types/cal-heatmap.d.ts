declare module 'cal-heatmap' {
  export default class CalHeatmap {
    paint(options?: any, plugins?: any[]): Promise<void> | void;
    destroy(): void;
    previous(): void;
    next(): void;
  }
}

declare module 'cal-heatmap/plugins/Tooltip' {
  const Tooltip: any;
  export default Tooltip;
}

declare module 'cal-heatmap/plugins/LegendLite' {
  const LegendLite: any;
  export default LegendLite;
}

declare module 'cal-heatmap/plugins/CalendarLabel' {
  const CalendarLabel: any;
  export default CalendarLabel;
}

declare module 'cal-heatmap/plugins/Legend' {
  const Legend: any;
  export default Legend;
}

// Optional helper types used by our code (loosely typed)
declare namespace CalHeatmapTypes {
  interface DateOptions {
    start?: Date;
    highlight?: Date[];
  }
}