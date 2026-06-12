import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/splitter', name: 'splitter', component: () => import('@/views/SplitterView.vue') },
    { path: '/result/:taskId', name: 'result', component: () => import('@/views/ResultView.vue') },
    { path: '/cutter', name: 'cutter', component: () => import('@/views/CutterView.vue') },
    { path: '/merger', name: 'merger', component: () => import('@/views/MergerView.vue') },
    { path: '/bpm-key', name: 'bpm-key', component: () => import('@/views/BpmKeyView.vue') },
  ],
})

export default router
