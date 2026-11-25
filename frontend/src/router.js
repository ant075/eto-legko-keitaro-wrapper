import { createRouter, createWebHistory } from 'vue-router'
import CampaignListView from './views/CampaignListView.vue'
import CampaignEditView from './views/CampaignEditView.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/campaigns' },
    { path: '/campaigns', component: CampaignListView },
    { path: '/campaigns/:id', component: CampaignEditView },
  ],
})

