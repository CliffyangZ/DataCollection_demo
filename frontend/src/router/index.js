import { createRouter, createWebHistory } from 'vue-router'
import DataCollectionView from '../views/DataCollectionView.vue'
import KlineChartView from '../views/KlineChartView.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: DataCollectionView
  },
  {
    path: '/data-collection',
    name: 'data-collection',
    component: DataCollectionView
  },
  {
    path: '/data',
    name: 'data',
    component: KlineChartView
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

export default router