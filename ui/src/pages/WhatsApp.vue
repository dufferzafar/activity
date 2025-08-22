<script setup lang="ts">
import WhatsAppHeatmaps from '../components/WhatsAppHeatmaps.vue'
</script>

<template>
  <main>
    <h2>WhatsApp Messages</h2>
    <!-- Plotting only messages sent per day -->
    <WhatsAppHeatmaps />
  </main>
  
</template>

<style scoped>
main {
  max-width: 1100px;
  margin: 0 auto;
  text-align: left;
}
</style>




