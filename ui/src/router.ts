import { createRouter, createWebHistory } from 'vue-router';

import Home from './pages/Home.vue';

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/activity', name: 'home', component: Home },
    // Redirect legacy subroutes to the unified page
    { path: '/activity/:rest(.*)*', redirect: { name: 'home' } },
  ],
});

export default router;


