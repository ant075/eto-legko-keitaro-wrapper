<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  countries: { type: Array, required: true },
  domains: { type: Array, required: true },
  groups: { type: Array, required: true },
  sources: { type: Array, required: true },
  offers: { type: Array, required: true },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'create'])
const countryQuery = ref('')
const form = ref({ name: '', domain_id: '', group_id: '', traffic_source_id: '', country_code: '', offer_id: '' })

const filteredCountries = computed(() => {
  const needle = countryQuery.value.trim().toLowerCase()
  return props.countries.filter((country) => !needle || `${country.code} ${country.name_ru}`.toLowerCase().includes(needle))
})

function submit() {
  emit('create', {
    ...form.value,
    domain_id: Number(form.value.domain_id),
    group_id: Number(form.value.group_id),
    traffic_source_id: Number(form.value.traffic_source_id),
    offer_id: Number(form.value.offer_id),
  })
}
</script>

<template>
  <div class="modal-backdrop" @click.self="emit('close')">
    <form class="modal" @submit.prevent="submit">
      <h2>Новая кампания</h2>
      <input v-model="form.name" required placeholder="Название">
      <input v-model="countryQuery" placeholder="Поиск страны">
      <select v-model="form.country_code" required>
        <option disabled value="">Страна</option>
        <option v-for="country in filteredCountries" :key="country.code" :value="country.code">
          {{ country.code }} — {{ country.name_ru }}
        </option>
      </select>
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
      <select v-model="form.offer_id" required>
        <option disabled value="">Оффер</option>
        <option v-for="item in offers" :key="item.id" :value="item.id">{{ item.name }}</option>
      </select>
      <div class="modal-actions">
        <button type="button" @click="emit('close')">Отмена</button>
        <button type="submit" :disabled="loading">Создать</button>
      </div>
    </form>
  </div>
</template>

