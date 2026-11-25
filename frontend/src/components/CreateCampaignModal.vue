<script setup>
import { computed, ref } from 'vue'
import SearchSelect from './SearchSelect.vue'

const props = defineProps({
  countries: { type: Array, required: true },
  domains: { type: Array, required: true },
  groups: { type: Array, required: true },
  sources: { type: Array, required: true },
  loadOffers: { type: Function, required: true },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'create'])
const form = ref({ name: '', domain_id: '', group_id: '', traffic_source_id: '', country_code: '', offer_id: '' })

const formValid = computed(() => Boolean(
  form.value.name.trim()
  && form.value.domain_id
  && form.value.group_id
  && form.value.traffic_source_id
  && form.value.country_code
  && form.value.offer_id,
))

const countryLabel = (country) => `${country.code} — ${country.name_ru}`

function submit() {
  emit('create', {
    ...form.value,
    domain_id: Number(form.value.domain_id),
    group_id: Number(form.value.group_id),
    traffic_source_id: Number(form.value.traffic_source_id),
    offer_id: Number(form.value.offer_id),
  })
}

function close() {
  if (!props.loading) emit('close')
}
</script>

<template>
  <div class="modal-backdrop" @click.self="close">
    <form class="modal" @submit.prevent="submit">
      <fieldset :disabled="loading" class="modal-fields">
        <h2>Новая кампания</h2>
        <input v-model="form.name" required placeholder="Название">
        <SearchSelect v-model="form.country_code" :options="countries" value-key="code" :get-label="countryLabel" :search-fields="['code', 'name_ru']" placeholder="Страна" />
        <select v-model="form.domain_id" required>
          <option disabled value="">Домен</option>
          <option v-for="item in domains" :key="item.id" :value="item.id">{{ item.name }}</option>
        </select>
        <select v-model="form.group_id" required>
          <option disabled value="">Группа</option>
          <option v-for="item in groups" :key="item.id" :value="item.id">{{ item.name }}</option>
        </select>
        <select v-model="form.traffic_source_id" required>
          <option disabled value="">Источник</option>
          <option v-for="item in sources" :key="item.id" :value="item.id">{{ item.name }}</option>
        </select>
        <SearchSelect v-model="form.offer_id" :load-options="loadOffers" value-key="id" :get-label="(offer) => offer.name" :min-search-length="2" placeholder="Оффер" />
        <div class="modal-actions">
          <button type="button" @click="close">Отмена</button>
          <button type="submit" :disabled="!formValid">Создать</button>
        </div>
      </fieldset>
      <div v-if="loading" class="modal-loading"><span class="spinner"></span><span>Загрузка справочников…</span></div>
    </form>
  </div>
</template>

