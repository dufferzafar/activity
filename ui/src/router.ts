import { createRouter, createWebHistory } from 'vue-router';

import Home from './pages/Home.vue';
import Trakt from './pages/Trakt.vue';
import YTMusic from './pages/YTMusic.vue';
import Youtube from './pages/Youtube.vue';
import GooglePhotos from './pages/GooglePhotos.vue';
import Calls from './pages/Calls.vue';
import WhatsApp from './pages/WhatsApp.vue';

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/activity', name: 'home', component: Home },
    { path: '/activity/trakt', name: 'trakt', component: Trakt },
    { path: '/activity/ytmusic', name: 'ytmusic', component: YTMusic },
    { path: '/activity/youtube', name: 'youtube', component: Youtube },
    { path: '/activity/photos', name: 'photos', component: GooglePhotos },
    { path: '/activity/calls', name: 'calls', component: Calls },
    { path: '/activity/whatsapp', name: 'whatsapp', component: WhatsApp },
  ],
});

export default router;


