<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import YearHeatmap from '../components/YearHeatmap.vue';

// Services
import { loadRuntimeSummary as loadTrakt, groupYears as groupYearsTrakt } from '../services/traktRuntimeData';
import { loadSearchSummary as loadYoutube, groupYears as groupYearsYT } from '../services/ytmusicData';
import { loadPhotosSummary, groupYears as groupYearsPhotos } from '../services/googlePhotosData';
import { loadWhatsAppSummary, groupYears as groupYearsWhatsApp } from '../services/whatsappData';
import { loadCallsSummary, groupYears as groupYearsCalls } from '../services/callsData';

type DataSourceId = 'trakt' | 'ytmusic-search' | 'ytmusic-watch' | 'youtube-search' | 'youtube-watch' | 'photos' | 'whatsapp' | 'calls';

interface DataSourceConfig {
  id: DataSourceId;
  label: string;
  yField: string;
  valueLabel: string;
  load: () => Promise<any[]>; // entries must include { date: string, [yField]: number }
  groupYears: (entries: any[]) => number[];
}

const sources: DataSourceConfig[] = [
  {
    id: 'trakt',
    label: 'Trakt.tv runtime (min)',
    yField: 'total_runtime',
    valueLabel: 'min',
    load: () => loadTrakt('/activity/data/trakt.history.summary.json'),
    groupYears: groupYearsTrakt,
  },
  {
    id: 'ytmusic-search',
    label: 'YouTube Music searches',
    yField: 'count',
    valueLabel: 'searches',
    load: () => loadYoutube('/activity/data/ytmusic.search.summary.json'),
    groupYears: groupYearsYT,
  },
  {
    id: 'ytmusic-watch',
    label: 'YouTube Music Songs',
    yField: 'count',
    valueLabel: 'songs',
    load: () => loadYoutube('/activity/data/ytmusic.watch.summary.json'),
    groupYears: groupYearsYT,
  },
  {
    id: 'youtube-search',
    label: 'YouTube searches',
    yField: 'count',
    valueLabel: 'searches',
    load: () => loadYoutube('/activity/data/youtube.search.summary.json'),
    groupYears: groupYearsYT,
  },
  {
    id: 'youtube-watch',
    label: 'YouTube Videos',
    yField: 'count',
    valueLabel: 'videos',
    load: () => loadYoutube('/activity/data/youtube.watch.summary.json'),
    groupYears: groupYearsYT,
  },
  {
    id: 'photos',
    label: 'Google Photos items',
    yField: 'count',
    valueLabel: 'photos',
    load: () => loadPhotosSummary('/activity/data/googlephotos.summary.json'),
    groupYears: groupYearsPhotos,
  },
  {
    id: 'whatsapp',
    label: 'WhatsApp messages sent',
    yField: 'msgs_sent',
    valueLabel: 'msgs',
    load: () => loadWhatsAppSummary('/activity/data/whatsapp.history.summary.json'),
    groupYears: groupYearsWhatsApp,
  },
  {
    id: 'calls',
    label: 'iPhone Calls (minutes)',
    yField: 'total_minutes',
    valueLabel: 'min',
    load: () => loadCallsSummary('/activity/data/calls.history.summary.json'),
    groupYears: groupYearsCalls,
  },
];

const selectedId = ref<DataSourceId>('trakt');
const entries = ref<any[]>([]);
const years = ref<number[]>([]);
const isLoading = ref<boolean>(true);
const error = ref<string | null>(null);
const psychEvents = ref<Record<string, { description: string; prescription?: string[] }>>({});

async function loadPsych() {
  try {
    const psych = await fetch('/activity/data/psych.history.summary.json', { cache: 'no-cache' }).then((r) => r.json());
    if (Array.isArray(psych)) {
      psychEvents.value = Object.fromEntries(
        psych.map((p: any) => [String(p.date), { description: String(p.description ?? ''), prescription: p.prescription ?? [] }]),
      );
    }
  } catch (_) {
    // ignore psych errors
  }
}

async function loadSelected() {
  isLoading.value = true;
  error.value = null;
  try {
    const cfg = sources.find((s) => s.id === selectedId.value)!;
    const data = await cfg.load();
    entries.value = data;
    years.value = cfg.groupYears(data).filter((y) => y >= 2019);
  } catch (e: any) {
    error.value = e?.message ?? String(e);
  } finally {
    isLoading.value = false;
  }
}

onMounted(async () => {
  await Promise.all([loadPsych(), loadSelected()]);
});

watch(selectedId, () => {
  loadSelected();
});

function currentConfig(): DataSourceConfig {
  return sources.find((s) => s.id === selectedId.value)!;
}
</script>

<template>
  <main class="home">
    <h1>Activity Analytics</h1>
    <div class="controls">
      <label for="source">Data source</label>
      <select id="source" v-model="selectedId">
        <option v-for="s in sources" :key="s.id" :value="s.id">{{ s.label }}</option>
      </select>
    </div>

    <div v-if="isLoading">Loading…</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <YearHeatmap
        v-for="y in years"
        :key="y"
        :year="y"
        :entries="entries"
        :psych-events="psychEvents"
        :y-field="currentConfig().yField"
        :value-label="currentConfig().valueLabel"
      />
    </div>
  </main>
</template>

<style scoped>
.home {
  max-width: 1100px;
  margin: 2rem auto;
  text-align: left;
}
.controls {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0.75rem 0 1.25rem;
}
label { font-weight: 600; }
select { padding: 6px 8px; }
.error { color: #b00020; }
</style>


