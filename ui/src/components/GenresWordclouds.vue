<script setup lang="ts">
import { onMounted, ref, computed } from 'vue';
import type { RuntimeSummaryEntry } from '../types/trakt';
import { loadRuntimeSummary } from '../services/traktRuntimeData';
import { aggregateGenresByMonth, type MonthlyGenres } from '../services/traktGenreAggregation';
import dayjs from 'dayjs';
import MonthlyWordcloud from './MonthlyWordcloud.vue';

const entries = ref<RuntimeSummaryEntry[]>([]);
const isLoading = ref(true);
const error = ref<string | null>(null);

onMounted(async () => {
  try {
    const data = await loadRuntimeSummary();
    entries.value = data;
  } catch (e: any) {
    error.value = e?.message ?? String(e);
  } finally {
    isLoading.value = false;
  }
});

const monthly = computed<MonthlyGenres[]>(() => aggregateGenresByMonth(entries.value));

const years = computed(() => {
  const set = new Set<number>();
  for (const m of monthly.value) {
    if (m.year >= 2019) set.add(m.year);
  }
  return Array.from(set).sort((a, b) => a - b);
});

function monthsForYear(year: number): MonthlyGenres[] {
  const byMonth: Record<number, MonthlyGenres> = {};
  for (const m of monthly.value) {
    if (m.year === year) byMonth[m.month] = m;
  }
  // Return 1..12 with empty arrays when missing
  const result: MonthlyGenres[] = [];
  for (let i = 1; i <= 12; i++) {
    result.push(byMonth[i] ?? { year, month: i, genres: [] });
  }
  return result;
}
</script>

<template>
  <section>
    <div v-if="isLoading">Loading…</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div v-for="y in years" :key="y" class="year-section">
        <h2 class="year-heading">{{ y }} Subgenres</h2>
        <div class="months-grid">
          <MonthlyWordcloud
            v-for="m in monthsForYear(y)"
            :key="m.month"
            :year="y"
            :month="m.month"
            :genres="m.genres"
            :title="dayjs(`${y}-${String(m.month).padStart(2,'0')}-01`).format('MMM')"
          />
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.error { color: #b00020; }
.year-section { margin: 1.5rem 0 2.25rem; }
.year-heading { margin: 0 0 0.5rem; font-weight: 700; }
.months-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}
@media (min-width: 1024px) {
  .months-grid { grid-template-columns: repeat(6, minmax(0, 1fr)); }
}
</style> 