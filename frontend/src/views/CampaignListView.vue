<script setup>
import {onMounted, ref} from 'vue'
import {useRouter} from 'vue-router'
import {api} from '../api'
import CreateCampaignModal from '../components/CreateCampaignModal.vue'

const router = useRouter()
const campaigns = ref([]), countries = ref([]), domains = ref([]), groups = ref([]), sources = ref([]), offers = ref([])
const showCreate = ref(false), loading = ref(false), referencesLoading = ref(false), referencesLoaded = ref(false),
    error = ref('')

function options(items) {
  return (Array.isArray(items) ? items : items?.data || items?.items || []).map((item) => ({
    id: item.id,
    name: item.name || item.title || item.label || String(item.id)
  }))
}

async function loadCampaigns() {
  try {
    campaigns.value = await api.campaigns()
  } catch (err) {
    error.value = err.message
  }
}

async function loadReferences() {
  if (referencesLoaded.value || referencesLoading.value) return;
  try {
    referencesLoading.value = true;
    const [countryData, domainData, groupData, sourceData, offerData] = await Promise.all([api.countries(), api.domains(), api.groups(), api.sources(), api.offers()]);
    countries.value = countryData;
    domains.value = options(domainData);
    groups.value = options(groupData);
    sources.value = options(sourceData);
    offers.value = options(offerData);
    referencesLoaded.value = true
  } catch (err) {
    error.value = err.message
  } finally {
    referencesLoading.value = false
  }
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
    <header class="topbar"><h1>Keitaro Wrapper</h1>
      <button @click="openCreateModal">Добавить кампанию</button>
    </header>
    <p v-if="error" class="error">{{ error }}
      <button class="link" @click="error = ''">закрыть</button>
    </p>
    <section class="panel campaign-panel"><h2>Кампании</h2>
      <p v-if="!campaigns.length" class="muted">Кампаний пока нет.</p>
      <div v-for="campaign in campaigns" :key="campaign.id" class="campaign-row">
        <button class="campaign-name" @click="router.push(`/campaigns/${campaign.id}`)">{{ campaign.name }}</button>
        <span class="muted">#{{ campaign.id }}</span>
        <button class="danger link" @click="removeCampaign(campaign)">Удалить</button>
      </div>
    </section>
    <CreateCampaignModal v-if="showCreate" :countries="countries" :domains="domains" :groups="groups" :sources="sources"
                         :offers="offers" :loading="loading || referencesLoading" @close="showCreate = false"
                         @create="createCampaign"/>
  </main>
</template>

