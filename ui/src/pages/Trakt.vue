<script setup lang="ts">
import TraktHeatmaps from '../components/TraktHeatmaps.vue'
// import GenresWordclouds from '../components/GenresWordclouds.vue'
</script>

<template>
  <main>
    <h2>Trakt.tv</h2>
    <p>
      I've been using Trakt.tv to track my TV and movie watching.
      This is a heatmap of my <a href="https://trakt.tv/users/dufferzafar/history">viewing activity</a>.
    </p>
    <TraktHeatmaps />

    <!-- <h2 style="margin-top: 2rem;">Genres by Month</h2>
    <GenresWordclouds /> -->
  </main>
</template>

<style scoped>
main {
  max-width: 1100px;
  margin: 0 auto;
  text-align: left;
}
</style>


