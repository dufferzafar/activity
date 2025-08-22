<script setup lang="ts">
import { computed } from 'vue';
import type { GenreCount } from '../types/trakt';
import { computeFontSize, hashHue } from '../services/traktGenreAggregation';
import dayjs from 'dayjs';

const props = defineProps<{
  year: number;
  month: number; // 1-12
  genres: GenreCount[];
  title?: string;
}>();

const stats = computed(() => {
  const counts = props.genres.map((g) => g.count);
  const min = counts.length ? Math.min(...counts) : 0;
  const max = counts.length ? Math.max(...counts) : 0;
  return { min, max };
});

const monthLabel = computed(() =>
  props.title ?? dayjs(`${props.year}-${String(props.month).padStart(2, '0')}-01`).format('MMM')
);

function colorFor(name: string): string {
  const h = hashHue(name);
  return `hsl(${h} 60% 50%)`;
}
</script>

<template>
  <div class="month-cloud">
    <div class="month-title">{{ monthLabel }}</div>
    <div v-if="!genres.length" class="empty">No data</div>
    <div v-else class="words">
      <span
        v-for="g in genres"
        :key="g.name"
        class="word"
        :style="{ fontSize: computeFontSize(g.count, stats.min, stats.max, 8, 24) + 'px', color: colorFor(g.name) }"
        :title="`${g.name}: ${g.count}`"
      >
        {{ g.name }}
      </span>
    </div>
  </div>
</template>

<style scoped>
.month-cloud {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 8px 10px;
  background: #fff;
}
.month-title {
  font-weight: 600;
  margin-bottom: 8px;
  color: #000;
}
.words {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 10px;
  align-items: center;
}
.word {
  line-height: 1.1;
}
.empty {
  color: #9ca3af;
  font-style: italic;
}
</style> 