<script setup lang="ts">
import { onMounted, ref } from 'vue';
import YearHeatmap from './YearHeatmap.vue';
import type { YTMusicSummaryEntry } from '../types/ytmusic';
import { loadSearchSummary, groupYears } from '../services/ytmusicData';

const isLoading = ref(true);
const error = ref<string | null>(null);
const entries = ref<YTMusicSummaryEntry[]>([]);
const years = ref<number[]>([]);
const psychEvents = ref<Record<string, { description: string; prescription?: string[] }>>({});

onMounted(async () => {
  try {
    const data = await loadSearchSummary('/activity/data/youtube.search.summary.json');
    entries.value = data;
    years.value = groupYears(data).filter((y) => y >= 2019);

    const psych = await fetch('/activity/data/psych.history.json', { cache: 'no-cache' }).then((r) => r.json());
    if (Array.isArray(psych)) {
      psychEvents.value = Object.fromEntries(
        psych.map((p: any) => [String(p.date), { description: String(p.description ?? ''), prescription: p.prescription ?? [] }]),
      );
    }
  } catch (e: any) {
    error.value = e?.message ?? String(e);
  } finally {
    isLoading.value = false;
  }
});
</script>

<template>
  <div>
    <div v-if="isLoading">Loading…</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <YearHeatmap v-for="y in years" :key="y" :year="y" :entries="entries" :psych-events="psychEvents" y-field="count" value-label="searches" />
    </div>
  </div>
  
</template>

<style scoped>
.error {
  color: #b00020;
}
</style>


