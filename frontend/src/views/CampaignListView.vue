<script setup>
import {onMounted, ref} from 'vue'
import {api} from '../api'
import CreateCampaignModal from '../components/CreateCampaignModal.vue'

const campaigns = ref([]), countries = ref([]), domains = ref([]), groups = ref([]), sources = ref([]), offers = ref([])
const showCreate = ref(false), loading = ref(false), campaignsLoading = ref(false), referencesLoading = ref(false), referencesLoaded = ref(false),
    error = ref('')

function options(items) {
  return (Array.isArray(items) ? items : items?.data || items?.items || []).map((item) => ({
    id: item.id,
    name: item.name || item.title || item.label || String(item.id)
  }))
}

async function loadCampaigns() {
  try {
    campaignsLoading.value = true
    const [campaignData, groupData, sourceData] = await Promise.all([api.campaigns(), api.groups(), api.sources()])
    campaigns.value = campaignData
    groups.value = options(groupData)
    sources.value = options(sourceData)
  } catch (err) {
    error.value = err.message
  } finally {
    campaignsLoading.value = false
  }
}

async function loadReferences() {
  if (referencesLoaded.value || referencesLoading.value) return;
  try {
    referencesLoading.value = true;
    const [countryData, domainData, offerData] = await Promise.all([api.countries(), api.domains(), api.offers()]);
    countries.value = countryData;
    domains.value = options(domainData);
    offers.value = options(offerData);
    referencesLoaded.value = true
  } catch (err) {
    error.value = err.message
  } finally {
    referencesLoading.value = false
  }
}

function referenceName(items, id) {
  return items.find((item) => item.id === id)?.name || id
}

function formatDate(value) {
  if (!value) return '—'
  return new Date(value.replace(' ', 'T')).toLocaleString('ru-RU')
}

async function openCreateModal() {
  showCreate.value = true;
  await loadReferences()
}

async function createCampaign(data) {
  try {
    loading.value = true;
    await api.createCampaign(data);
    showCreate.value = false;
    await loadCampaigns()
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function removeCampaign(campaign) {
  if (!confirm(`Удалить кампанию «${campaign.name}»?`)) return;
  try {
    await api.deleteCampaign(campaign.id);
    campaigns.value = campaigns.value.filter((item) => item.id !== campaign.id)
  } catch (err) {
    error.value = err.message
  }
}

onMounted(loadCampaigns)
</script>

<template>
  <main class="page">
    <header class="topbar"><h1>Keitaro API Wrapper</h1>
      <button @click="openCreateModal">Добавить кампанию</button>
    </header>
    <p v-if="error" class="error">{{ error }}
      <button class="link" @click="error = ''">закрыть</button>
    </p>
    <section class="panel campaign-panel"><h2>Кампании</h2>
      <div v-if="campaignsLoading" class="loading-state"><span class="spinner" aria-label="Загрузка"></span><span class="muted">Загрузка кампаний…</span></div>
      <p v-else-if="!campaigns.length" class="muted">Кампаний пока нет.</p>
      <div v-else class="table-wrapper"><table class="campaign-table"><thead><tr><th>ID</th><th>Имя</th><th>Источник</th><th>Группа</th><th>Дата последнего изменения</th><th></th></tr></thead><tbody><tr v-for="campaign in campaigns" :key="campaign.id"><td>{{ campaign.id }}</td><td><RouterLink class="campaign-link" :to="`/campaigns/${campaign.id}`">{{ campaign.name }}</RouterLink></td><td>{{ referenceName(sources, campaign.traffic_source_id) }}</td><td>{{ referenceName(groups, campaign.group_id) }}</td><td>{{ formatDate(campaign.updated_at) }}</td><td><button class="danger link" @click="removeCampaign(campaign)">Удалить</button></td></tr></tbody></table></div>
    </section>
    <CreateCampaignModal v-if="showCreate" :countries="countries" :domains="domains" :groups="groups" :sources="sources"
                         :offers="offers" :loading="loading || referencesLoading" @close="showCreate = false"
                         @create="createCampaign"/>
  </main>
</template>

