<script setup lang="ts">
import { RouterLink } from 'vue-router';
</script>

<template>
  <main class="home">
    <h1>Activity Analytics</h1>
    <p>Choose a page:</p>
    <ul>
      <li><RouterLink to="/activity/trakt">Trakt.tv</RouterLink></li>
      <li><RouterLink to="/activity/ytmusic">YouTube Music</RouterLink></li>
      <li><RouterLink to="/activity/youtube">YouTube</RouterLink></li>
      <li><RouterLink to="/activity/photos">Google Photos</RouterLink></li>
      <li><RouterLink to="/activity/calls">Calls</RouterLink></li>
      <li><RouterLink to="/activity/whatsapp">WhatsApp</RouterLink></li>
    </ul>
  </main>
</template>

<style scoped>
.home {
  max-width: 700px;
  margin: 2rem auto;
  text-align: left;
}
ul { padding-left: 1.25rem; }
li { margin: 0.25rem 0; }
a { color: #2563eb; text-decoration: none; }
a:hover { text-decoration: underline; }
</style>


