<script setup>
import {onMounted, ref} from 'vue'
import {api} from '../api'
import CreateCampaignModal from '../components/CreateCampaignModal.vue'

const campaigns = ref([]), countries = ref([]), domains = ref([]), groups = ref([]), sources = ref([])
const showCreate = ref(false), loading = ref(false), campaignsLoading = ref(false), referencesLoading = ref(false),
    referencesLoaded = ref(false), deletingCampaignId = ref(null),
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
    campaigns.value = await api.campaigns()
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
    const [countryData, domainData, groupData, sourceData] = await Promise.all([api.countries(), api.domains(), api.groups(), api.sources()]);
    countries.value = countryData;
    domains.value = options(domainData);
    groups.value = options(groupData);
    sources.value = options(sourceData);
    referencesLoaded.value = true
  } catch (err) {
    error.value = err.message
  } finally {
    referencesLoading.value = false
  }
}

async function searchOffers(query) {
  try {
    return await api.searchReferenceOffers(query)
  } catch (err) {
    error.value = err.message;
    return []
  }
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
  if (deletingCampaignId.value !== null) return;
  try {
    deletingCampaignId.value = campaign.id
    await api.deleteCampaign(campaign.id);
    campaigns.value = campaigns.value.filter((item) => item.id !== campaign.id)
  } catch (err) {
    error.value = err.message
  } finally {
    deletingCampaignId.value = null
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
    <section class="panel campaign-panel" :aria-busy="deletingCampaignId !== null">
      <div v-if="deletingCampaignId !== null" class="campaign-list-loading" aria-label="Удаление кампании">
        <span class="spinner"></span>
        <span>Удаление кампании…</span>
      </div>
      <h2>Кампании</h2>
      <div v-if="campaignsLoading" class="loading-state"><span class="spinner" aria-label="Загрузка"></span><span
          class="muted">Загрузка кампаний…</span></div>
      <p v-else-if="!campaigns.length" class="muted">Кампаний пока нет.</p>
      <div v-else class="table-wrapper">
        <table class="campaign-table">
          <thead>
          <tr>
            <th>ID</th>
            <th>Имя</th>
            <th>Дата последнего изменения</th>
            <th></th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="campaign in campaigns" :key="campaign.id">
            <td>{{ campaign.id }}</td>
            <td>
              <RouterLink class="campaign-link" :to="`/campaigns/${campaign.id}`">{{ campaign.name }}</RouterLink>
            </td>
            <td>{{ formatDate(campaign.updated_at) }}</td>
            <td>
              <button class="danger link" :disabled="deletingCampaignId !== null" @click="removeCampaign(campaign)">Удалить</button>
            </td>
          </tr>
          </tbody>
        </table>
      </div>
    </section>
    <CreateCampaignModal v-if="showCreate" :countries="countries" :domains="domains" :groups="groups" :sources="sources"
                         :load-offers="searchOffers" :loading="referencesLoading" :creating="loading"
                         @close="showCreate = false"
                         @create="createCampaign"/>
  </main>
</template>

