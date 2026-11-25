<script setup>
import {onMounted, ref} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {api} from '../api'
import OfferList from '../components/OfferList.vue'
import SearchSelect from '../components/SearchSelect.vue'

const route = useRoute(), router = useRouter()
const campaign = ref(null), campaignOffers = ref([]), selectedOffer = ref(null),
    error = ref(''), addingOffer = ref(false)

async function load() {
  try {
    campaign.value = await api.campaign(route.params.id);
    campaignOffers.value = (await api.campaignOffers(route.params.id)).offers
  } catch (err) {
    error.value = err.message
  }
}

async function offerAction(action, offerId) {
  try {
    const result = await action(campaign.value.id, offerId);
    campaignOffers.value = result.offers;
    campaign.value.is_dirty = result.is_dirty
  } catch (err) {
    error.value = err.message
  }
}

async function loadOfferOptions(query) {
  try { return await api.searchOffers(campaign.value.id, query) } catch (err) { error.value = err.message; return [] }
}

async function addOffer() {
  if (!selectedOffer.value) return;
  if (addingOffer.value) return;
  try {
    addingOffer.value = true;
    const result = await api.addOffer(campaign.value.id, selectedOffer.value);
    campaignOffers.value = result.offers;
    campaign.value.is_dirty = result.is_dirty;
    selectedOffer.value = null
  } catch (err) {
    error.value = err.message
  } finally {
    addingOffer.value = false
  }
}

async function campaignAction(action) {
  try {
    const result = await action(campaign.value.id);
    campaignOffers.value = result.offers;
    campaign.value.is_dirty = result.is_dirty
  } catch (err) {
    error.value = err.message
  }
}

onMounted(load)
</script>

<template>
  <main class="page">
    <header class="topbar">
      <button class="link" @click="router.push('/campaigns')">← Кампании</button>
      <h1 v-if="campaign">{{ campaign.name }}</h1><span v-else>Загрузка…</span></header>
    <p v-if="error" class="error">{{ error }}
      <button class="link" @click="error = ''">закрыть</button>
    </p>
    <section v-if="campaign" class="streams">
      <section class="panel stream-card">
        <div class="editor-title">
          <span class="muted">Поток редиректа по стране #{{ campaign.redirect_stream_id }}</span>
        </div>
        <p>
          Пользователей из <strong>{{ campaign.country_name }} ({{ campaign.country_code }})</strong>
          перенаправлять на <strong>{{ campaign.redirect_target_url }}</strong>
        </p>
      </section>
      <section class="panel editor">
      <div class="editor-title">
        <span class="muted">Поток офферов #{{ campaign.offers_stream_id }}</span>
        <div class="actions">
          <button :disabled="!campaign.is_dirty" @click="campaignAction(api.publish)">Опубликовать</button>
          <button :disabled="!campaign.is_dirty" @click="campaignAction(api.cancel)">Отмена</button>
          <button :disabled="campaign.is_dirty" @click="campaignAction(api.sync)">Запросить из Keitaro</button>
        </div>
      </div>
      <OfferList
          :offers="campaignOffers"
          :dirty="campaign.is_dirty"
          @pin="(id) => offerAction(api.pin, id)"
          @unpin="(id) => offerAction(api.unpin, id)" @delete="(id) => offerAction(api.deleteOffer, id)"
          @restore="(id) => offerAction(api.restoreOffer, id)"
      />
      <div class="add-offer">
        <SearchSelect v-model="selectedOffer" :load-options="loadOfferOptions" :get-label="(offer) => `${offer.name} (#${offer.offer_id})`" :min-search-length="2" placeholder="Поиск оффера" :disabled="addingOffer" />
        <button :disabled="!selectedOffer || addingOffer" @click="addOffer">Добавить</button>
      </div>
      </section>
    </section>
  </main>
</template>

