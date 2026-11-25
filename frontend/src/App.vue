<script setup>
import {computed, onMounted, ref} from 'vue'
import {api} from './api'
import OfferList from './components/OfferList.vue'

const campaigns = ref([]), countries = ref([]), domains = ref([]), groups = ref([]), sources = ref([]), offers = ref([])
const selectedCampaign = ref(null), campaignOffers = ref([]), showCreate = ref(false), loading = ref(false), addingOffer = ref(false),
    error = ref('')
const countryQuery = ref(''), offerQuery = ref(''), offerSearchResults = ref([])
let searchTimer
const form = ref({name: '', domain_id: '', group_id: '', traffic_source_id: '', country_code: '', offer_id: ''})

const filteredCountries = computed(() => {
  const needle = countryQuery.value.trim().toLowerCase()
  return countries.value.filter((country) => !needle || `${country.code} ${country.name_ru}`.toLowerCase().includes(needle))
})

function options(items) {
  return (Array.isArray(items) ? items : items?.data || items?.items || []).map((item) => ({
    id: item.id,
    name: item.name || item.title || item.label || String(item.id)
  }))
}

async function loadInitial() {
  try {
    const [campaignData, countryData, domainData, groupData, sourceData, offerData] = await Promise.all([api.campaigns(), api.countries(), api.domains(), api.groups(), api.sources(), api.offers()])
    campaigns.value = campaignData;
    countries.value = countryData;
    domains.value = options(domainData);
    groups.value = options(groupData);
    sources.value = options(sourceData);
    offers.value = options(offerData)
  } catch (err) {
    error.value = err.message
  }
}

async function createCampaign() {
  try {
    loading.value = true
    await api.createCampaign({
      ...form.value,
      domain_id: Number(form.value.domain_id),
      group_id: Number(form.value.group_id),
      traffic_source_id: Number(form.value.traffic_source_id),
      offer_id: Number(form.value.offer_id)
    })
    showCreate.value = false;
    form.value = {name: '', domain_id: '', group_id: '', traffic_source_id: '', country_code: '', offer_id: ''};
    await loadInitial()
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function openCampaign(campaign) {
  try {
    selectedCampaign.value = campaign;
    campaignOffers.value = (await api.campaignOffers(campaign.id)).offers
  } catch (err) {
    error.value = err.message
  }
}

async function offerAction(action, offerId) {
  try {
    const result = await action(selectedCampaign.value.id, offerId);
    campaignOffers.value = result.offers;
    selectedCampaign.value.is_dirty = result.is_dirty
  } catch (err) {
    error.value = err.message
  }
}

function searchOffers() {
  clearTimeout(searchTimer)
  if (offerQuery.value.trim().length < 2) {
    offerSearchResults.value = [];
    return
  }
  searchTimer = setTimeout(async () => {
    try {
      offerSearchResults.value = await api.searchOffers(selectedCampaign.value.id, offerQuery.value)
    } catch (err) {
      error.value = err.message
    }
  }, 250)
}

async function addOffer(offer) {
  if (addingOffer.value) return
  try {
    addingOffer.value = true
    campaignOffers.value = (await api.addOffer(selectedCampaign.value.id, offer)).offers;
    offerQuery.value = '';
    offerSearchResults.value = []
  } catch (err) {
    error.value = err.message
  } finally {
    addingOffer.value = false
  }
}

async function campaignAction(action) {
  try {
    const result = await action(selectedCampaign.value.id);
    campaignOffers.value = result.offers;
    selectedCampaign.value.is_dirty = result.is_dirty
    if (action === api.publish || action === api.cancel) await loadInitial()
  } catch (err) {
    error.value = err.message
  }
}

async function removeCampaign(campaign) {
  if (!confirm(`Удалить кампанию «${campaign.name}»?`)) return
  try {
    await api.deleteCampaign(campaign.id);
    campaigns.value = campaigns.value.filter((item) => item.id !== campaign.id);
    if (selectedCampaign.value?.id === campaign.id) selectedCampaign.value = null
  } catch (err) {
    error.value = err.message
  }
}

onMounted(loadInitial)
</script>

<template>
  <main class="page">
    <header class="topbar"><h1>Keitaro Wrapper</h1>
      <button @click="showCreate = true">Добавить кампанию</button>
    </header>
    <p v-if="error" class="error">{{ error }}
      <button class="link" @click="error = ''">закрыть</button>
    </p>
    <section class="layout">
      <div class="panel"><h2>Кампании</h2>
        <p v-if="!campaigns.length" class="muted">Кампаний пока нет.</p>
        <div v-for="campaign in campaigns" :key="campaign.id" class="campaign-row"
             :class="{ selected: selectedCampaign?.id === campaign.id }">
          <button class="campaign-name" @click="openCampaign(campaign)">{{ campaign.name }}</button>
          <span class="muted">#{{ campaign.id }}</span>
          <button class="danger link" @click="removeCampaign(campaign)">Удалить</button>
        </div>
      </div>
      <div v-if="selectedCampaign" class="panel editor">
        <div class="editor-title">
          <div><h2>{{ selectedCampaign.name }}</h2><span
              class="muted">Поток офферов #{{ selectedCampaign.offers_stream_id }}</span></div>
          <button class="link" @click="selectedCampaign = null">закрыть</button>
        </div>
        <div class="actions">
          <button :disabled="!selectedCampaign.is_dirty" @click="campaignAction(api.publish)">Опубликовать</button>
          <button :disabled="!selectedCampaign.is_dirty" @click="campaignAction(api.cancel)">Отмена</button>
          <button :disabled="selectedCampaign.is_dirty" @click="campaignAction(api.sync)">Запросить из Keitaro</button>
        </div>
        <OfferList
          :offers="campaignOffers"
          :dirty="selectedCampaign.is_dirty"
          @pin="(offerId) => offerAction(api.pin, offerId)"
          @unpin="(offerId) => offerAction(api.unpin, offerId)"
          @delete="(offerId) => offerAction(api.deleteOffer, offerId)"
          @restore="(offerId) => offerAction(api.restoreOffer, offerId)"
        />
        <div class="add-offer"><input v-model="offerQuery" placeholder="Поиск оффера" @input="searchOffers">
          <button v-for="offer in offerSearchResults" :key="offer.offer_id" :disabled="addingOffer" @click="addOffer(offer)">{{ offer.name }}
            (#{{ offer.offer_id }})
          </button>
        </div>
      </div>
    </section>
    <div v-if="showCreate" class="modal-backdrop" @click.self="showCreate = false">
      <form class="modal" @submit.prevent="createCampaign"><h2>Новая кампания</h2><input v-model="form.name" required
                                                                                         placeholder="Название"><input
          v-model="countryQuery" placeholder="Поиск страны"><select v-model="form.country_code" required>
        <option disabled value="">Страна</option>
        <option v-for="country in filteredCountries" :key="country.code" :value="country.code">{{ country.code }} —
          {{ country.name_ru }}
        </option>
      </select><select v-model="form.domain_id" required>
        <option disabled value="">Домен</option>
        <option v-for="item in domains" :key="item.id" :value="item.id">{{ item.name }}</option>
      </select><select v-model="form.group_id" required>
        <option disabled value="">Группа</option>
        <option v-for="item in groups" :key="item.id" :value="item.id">{{ item.name }}</option>
      </select><select v-model="form.traffic_source_id" required>
        <option disabled value="">Источник</option>
        <option v-for="item in sources" :key="item.id" :value="item.id">{{ item.name }}</option>
      </select><select v-model="form.offer_id" required>
        <option disabled value="">Оффер</option>
        <option v-for="item in offers" :key="item.id" :value="item.id">{{ item.name }}</option>
      </select>
        <div class="modal-actions">
          <button type="button" @click="showCreate = false">Отмена</button>
          <button type="submit" :disabled="loading">Создать</button>
        </div>
      </form>
    </div>
  </main>
</template>

<style>
:root {
  font-family: Inter, system-ui, sans-serif;
  color: #202124;
  background: #f5f6f8;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
}

button, input, select {
  font: inherit;
  padding: .55rem .7rem;
  border: 1px solid #c7cad1;
  border-radius: 6px;
  background: white;
}

button {
  cursor: pointer;
}

button:disabled {
  cursor: not-allowed;
  opacity: .5;
}

.page {
  max-width: 1200px;
  margin: auto;
  padding: 24px;
}

.topbar, .editor-title, .campaign-row, .offer-row, .actions, .modal-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.topbar, .editor-title {
  justify-content: space-between;
}

h1, h2 {
  margin-top: 0;
}

.layout {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 18px;
}

.panel {
  background: white;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 10px #0000000d;
}

.campaign-row {
  padding: 10px 0;
  border-bottom: 1px solid #eee;
}

.campaign-name {
  border: 0;
  padding: 0;
  text-align: left;
  flex: 1;
}

.selected {
  background: #eef4ff;
}

.muted {
  color: #68707d;
  font-size: .9rem;
}

.link {
  border: 0;
  background: transparent;
  padding: 2px;
}

.danger {
  color: #b42318;
}

.error {
  padding: 12px;
  color: #b42318;
  background: #fee4e2;
  border-radius: 6px;
}

.actions {
  margin: 16px 0;
  flex-wrap: wrap;
}

.offer-list {
  padding: 8px;
  border-radius: 8px;
}

.offer-list.dirty {
  background: #fff8d8;
}

.offer-row {
  padding: 10px 0;
  border-bottom: 1px solid #eee;
}

.offer-row span:first-child {
  flex: 1;
}

.offer-row.deleted {
  color: #9ca3af;
  font-style: italic;
}

.pinned {
  background: #dbeafe;
  border-color: #2563eb;
}

.add-offer {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
}

.add-offer input {
  flex: 1;
  min-width: 220px;
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  display: grid;
  place-items: center;
  background: #0006;
}

.modal {
  width: min(480px, calc(100vw - 32px));
  display: grid;
  gap: 12px;
  padding: 24px;
  background: white;
  border-radius: 10px;
}

.modal-actions {
  justify-content: flex-end;
  margin-top: 8px;
}

@media (max-width: 760px) {
  .layout {
    grid-template-columns: 1fr;
  }

  .offer-row {
    flex-wrap: wrap;
  }
}
</style>
