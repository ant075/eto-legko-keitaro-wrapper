<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'
import OfferList from '../components/OfferList.vue'

const route = useRoute(), router = useRouter()
const campaign = ref(null), campaignOffers = ref([]), offerQuery = ref(''), offerSearchResults = ref([]), error = ref(''), addingOffer = ref(false)
let searchTimer
async function load() { try { campaign.value = await api.campaign(route.params.id); campaignOffers.value = (await api.campaignOffers(route.params.id)).offers } catch (err) { error.value = err.message } }
async function offerAction(action, offerId) { try { const result = await action(campaign.value.id, offerId); campaignOffers.value = result.offers; campaign.value.is_dirty = result.is_dirty } catch (err) { error.value = err.message } }
function searchOffers() { clearTimeout(searchTimer); if (offerQuery.value.trim().length < 2) { offerSearchResults.value = []; return }; searchTimer = setTimeout(async () => { try { offerSearchResults.value = await api.searchOffers(campaign.value.id, offerQuery.value) } catch (err) { error.value = err.message } }, 250) }
async function addOffer(offer) { if (addingOffer.value) return; try { addingOffer.value = true; const result = await api.addOffer(campaign.value.id, offer); campaignOffers.value = result.offers; campaign.value.is_dirty = result.is_dirty; offerQuery.value = ''; offerSearchResults.value = [] } catch (err) { error.value = err.message } finally { addingOffer.value = false } }
async function campaignAction(action) { try { const result = await action(campaign.value.id); campaignOffers.value = result.offers; campaign.value.is_dirty = result.is_dirty } catch (err) { error.value = err.message } }
onMounted(load)
</script>

<template>
  <main class="page"><header class="topbar"><button class="link" @click="router.push('/campaigns')">← Кампании</button><h1 v-if="campaign">{{ campaign.name }}</h1><span v-else>Загрузка…</span></header><p v-if="error" class="error">{{ error }} <button class="link" @click="error = ''">закрыть</button></p><section v-if="campaign" class="panel editor"><div class="editor-title"><span class="muted">Поток офферов #{{ campaign.offers_stream_id }}</span><div class="actions"><button :disabled="!campaign.is_dirty" @click="campaignAction(api.publish)">Опубликовать</button><button :disabled="!campaign.is_dirty" @click="campaignAction(api.cancel)">Отмена</button><button :disabled="campaign.is_dirty" @click="campaignAction(api.sync)">Запросить из Keitaro</button></div></div><OfferList :offers="campaignOffers" :dirty="campaign.is_dirty" @pin="(id) => offerAction(api.pin, id)" @unpin="(id) => offerAction(api.unpin, id)" @delete="(id) => offerAction(api.deleteOffer, id)" @restore="(id) => offerAction(api.restoreOffer, id)" /><div class="add-offer"><input v-model="offerQuery" placeholder="Поиск оффера" @input="searchOffers"><button v-for="offer in offerSearchResults" :key="offer.offer_id" :disabled="addingOffer" @click="addOffer(offer)">{{ offer.name }} (#{{ offer.offer_id }})</button></div></section></main>
</template>

