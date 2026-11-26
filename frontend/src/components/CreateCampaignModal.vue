<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import SearchSelect from './SearchSelect.vue'

const props = defineProps({
  countries: { type: Array, required: true },
  domains: { type: Array, required: true },
  groups: { type: Array, required: true },
  sources: { type: Array, required: true },
  loadOffers: { type: Function, required: true },
  loading: { type: Boolean, default: false },
  creating: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'create'])
const form = ref({ name: '', domain_id: '', group_id: '', traffic_source_id: '', country_code: '', offer_id: '' })
const nameInput = ref(null)

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
  if (!props.loading && !props.creating) emit('close')
}

function focusNameInput() {
  if (!props.loading && !props.creating) {
    nextTick(() => nameInput.value?.focus())
  }
}

onMounted(focusNameInput)
watch(() => [props.loading, props.creating], focusNameInput)
</script>

<template>
  <div class="modal-backdrop" @click.self="close">
    <form class="modal" @submit.prevent="submit">
      <fieldset :disabled="loading || creating" class="modal-fields">
        <h2>Новая кампания</h2>
        <input ref="nameInput" v-model="form.name" required autofocus placeholder="Название">
        <SearchSelect
            v-model="form.country_code"
            :options="countries"
            value-key="code"
            :get-label="countryLabel"
            :search-fields="['code', 'name_ru']"
            placeholder="Страна"
        />
        <SearchSelect
            v-model="form.domain_id"
            :options="domains"
            value-key="id"
            :search-fields="['name']"
            placeholder="Домен"
        />
        <SearchSelect
            v-model="form.group_id"
            :options="groups"
            value-key="id"
            :search-fields="['name']"
            placeholder="Группа"
        />
        <SearchSelect
            v-model="form.traffic_source_id"
            :options="sources"
            value-key="id"
            :search-fields="['name']"
            placeholder="Источник"
        />
        <SearchSelect
            v-model="form.offer_id"
            :load-options="loadOffers"
            value-key="id"
            :get-label="(offer) => offer.name"
            :min-search-length="2"
            placeholder="Оффер"
        />
        <div class="modal-actions">
          <button type="button" @click="close">Отмена</button>
          <button type="submit" :disabled="!formValid || creating">Создать</button>
        </div>
      </fieldset>
      <div v-if="loading || creating" class="modal-loading">
        <span class="spinner"></span>
        <span>{{ creating ? 'Создание кампании…' : 'Загрузка справочников…' }}</span>
      </div>
    </form>
  </div>
</template>

