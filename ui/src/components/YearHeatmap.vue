<script setup lang="ts">
import { computed, onMounted, onBeforeUnmount } from 'vue';
import CalHeatmap from 'cal-heatmap';
import Tooltip from 'cal-heatmap/plugins/Tooltip';
// import Legend from 'cal-heatmap/plugins/Legend';
// import LegendLite from 'cal-heatmap/plugins/LegendLite';
import CalendarLabel from 'cal-heatmap/plugins/CalendarLabel';
import 'cal-heatmap/cal-heatmap.css';
import dayjs from 'dayjs';
import localeData from 'dayjs/plugin/localeData';

dayjs.extend(localeData);

type DatedEntry = { date: string; [key: string]: any };

const props = withDefaults(defineProps<{ 
  year: number;
  entries: DatedEntry[];
  psychEvents?: Record<string, { description: string; prescription?: string[] }>;
  yField?: string;
  valueLabel?: string;
}>(), {
  yField: 'total_runtime',
  valueLabel: 'min',
});

const elementId = computed(() => `cal-heatmap-${props.year}`);

let cal: CalHeatmap | null = null;

onMounted(() => {
  const yearEntries = props.entries.filter((e) => {
    const y = new Date(String(e.date) + 'T00:00:00Z').getUTCFullYear();
    return y === props.year;
  });
  const maxValue = Math.max(
    1,
    yearEntries.reduce((max, e) => {
      const v = Number(e[props.yField as string] ?? 0);
      return v > max ? v : max;
    }, 0),
  );

  // Collect highlight dates for this year from psych events
  const highlightDates: Date[] = [];
  if (props.psychEvents) {
    for (const d of Object.keys(props.psychEvents)) {
      const dateObj = new Date(d + 'T00:00:00Z');
      const y = dateObj.getUTCFullYear();
      if (y === props.year) highlightDates.push(dateObj);
    }
  }

  // Normalize entries to provide a real Date object in UTC to Cal-Heatmap
  const renderEntries = yearEntries.map((e: any) => ({
    ...e,
    __xDate: new Date(String(e.date) + 'T00:00:00Z'),
  }));

  cal = new CalHeatmap();
  cal.paint(
    {
      itemSelector: `#${elementId.value}`,
      theme: 'light',
      date: {
        // Use UTC to avoid TZ shifting to previous day/month
        start: new Date(Date.UTC(props.year, 0, 1)),
        highlight: highlightDates,
      },
      range: 12,
      domain: {
        type: 'month',
        gutter: 4,
        label: { text: 'MMM', textAlign: 'middle', position: 'top' },
      },
      subDomain: { type: 'day', width: 14, height: 14, radius: 4 },
      scale: {
        color: {
          type: 'quantize',
          scheme: 'YlOrRd',
          domain: [0, maxValue],
        },
      },
      data: {
        source: renderEntries,
        type: 'json',
        x: '__xDate',
        y: props.yField,
      },
    },
    [
      [
        Tooltip,
        {
          text: function (_date: Date, value: number | null, dayjsDate: any) {
            const base = `${value ?? 0} ${props.valueLabel} on ${dayjsDate.format('LL')}`;
            return base;
            // Disable psych tooltip for now
            // const key = dayjsDate.format('YYYY-MM-DD');
            // const ev = props.psychEvents?.[key];
            // if (!ev) return base;
            // return `${base}<br/>${ev.description}`;
          },
        },
      ],
      // [
      //   Legend,
      //   {
      //     includeBlank: true,
      //     radius: 6,
      //     itemSelector: `#${elementId.value}-legend`,
      //   },
      // ],
      [
        CalendarLabel,
        {
          width: 36,
          textAlign: 'start',
          text: () => dayjs().localeData().weekdaysShort().map((d: string, i: number) => (i % 2 === 0 ? '' : d)),
          padding: [28, 0, 0, 0],
        },
      ],
    ],
  );
});

onBeforeUnmount(() => {
  if (cal) {
    cal.destroy();
    cal = null;
  }
});
</script>

<template>
  <div class="year-heatmap">
    <div class="year-title">{{ year }}</div>
    <div :id="elementId"></div>
    <div :id="`${elementId}-legend`" class="legend"></div>
  </div>
</template>

<style scoped>
.year-heatmap {
  margin: 1.25rem 0 2.25rem;
}
.year-title {
  font-weight: 600;
  margin: 0 0 0.5rem 0;
}

/* Make highlighted days clearly visible in light theme */
:deep(.highlight) {
  stroke: #ff00ef;
  stroke-width: 3px;
}
</style> 