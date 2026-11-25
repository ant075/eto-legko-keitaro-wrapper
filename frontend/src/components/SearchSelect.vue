<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  modelValue: { default: null },
  options: { type: Array, default: () => [] },
  valueKey: { type: String, default: '' },
  getLabel: { type: Function, default: (option) => option?.name || '' },
  searchFields: { type: Array, default: () => [] },
  loadOptions: { type: Function, default: null },
  minSearchLength: { type: Number, default: 0 },
  placeholder: { type: String, default: 'Выберите значение' },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue', 'select'])
const root = ref(null), input = ref(null), query = ref(''), opened = ref(false), loading = ref(false), remoteOptions = ref([])
let timer, searchVersion = 0

const labelFor = (option) => props.getLabel(option)
const selectedOption = computed(() => props.options.find((option) => valueFor(option) === props.modelValue) || remoteOptions.value.find((option) => valueFor(option) === props.modelValue))
const valueFor = (option) => props.valueKey ? option?.[props.valueKey] : option
const availableOptions = computed(() => props.loadOptions ? remoteOptions.value : props.options)
const visibleOptions = computed(() => {
  if (props.loadOptions || !query.value.trim()) return availableOptions.value
  const needle = query.value.trim().toLowerCase()
  return availableOptions.value.filter((option) => props.searchFields.some((field) => String(option[field] ?? '').toLowerCase().includes(needle)))
})

function selectOption(option) {
  query.value = labelFor(option)
  opened.value = false
  emit('update:modelValue', valueFor(option))
  emit('select', option)
}

function clear() {
  searchVersion += 1
  query.value = ''
  remoteOptions.value = []
  emit('update:modelValue', null)
  input.value?.focus()
}

function open() {
  if (!props.disabled) opened.value = true
}

function onKeydown(event) {
  if (event.key === 'Escape') opened.value = false
  if (event.key === 'Enter' && visibleOptions.value.length) { event.preventDefault(); selectOption(visibleOptions.value[0]) }
}

function onOutside(event) {
  if (!root.value?.contains(event.target)) opened.value = false
}

watch(query, (value) => {
  if (!props.loadOptions) return
  const version = ++searchVersion
  clearTimeout(timer)
  remoteOptions.value = []
  if (value.trim().length < props.minSearchLength) return
  timer = setTimeout(async () => {
    try {
      loading.value = true
      const result = await props.loadOptions(value.trim())
      if (version === searchVersion) remoteOptions.value = result
    } finally {
      if (version === searchVersion) loading.value = false
    }
  }, 250)
})

watch(() => props.modelValue, (value) => {
  if (value == null) query.value = ''
})

onMounted(() => document.addEventListener('mousedown', onOutside))
onBeforeUnmount(() => { clearTimeout(timer); document.removeEventListener('mousedown', onOutside) })
</script>

<template>
  <div ref="root" class="search-select" :class="{ opened, disabled }">
    <input ref="input" v-model="query" :placeholder="placeholder" :disabled="disabled" @focus="open" @keydown="onKeydown">
    <button v-if="modelValue != null" type="button" class="search-select-clear" :disabled="disabled" @click="clear">×</button>
    <div v-if="opened" class="search-select-menu">
      <div v-if="loading" class="search-select-state"><span class="spinner"></span>Загрузка…</div>
      <div v-else-if="loadOptions && query.trim().length < minSearchLength" class="search-select-state">Введите минимум {{ minSearchLength }} символа</div>
      <div v-else-if="!visibleOptions.length" class="search-select-state">Ничего не найдено</div>
      <button v-for="option in visibleOptions" v-else :key="String(valueFor(option))" type="button" class="search-select-option" @mousedown.prevent="selectOption(option)">{{ labelFor(option) }}</button>
    </div>
  </div>
</template>

