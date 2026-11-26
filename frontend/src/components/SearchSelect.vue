<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

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
const root = ref(null), input = ref(null), query = ref(''), opened = ref(false), loading = ref(false), remoteOptions = ref([]), activeIndex = ref(-1), optionRefs = ref([]), suppressOpen = ref(false)
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
  activeIndex.value = -1
  emit('update:modelValue', valueFor(option))
  emit('select', option)
}

function clear() {
  searchVersion += 1
  query.value = ''
  remoteOptions.value = []
  activeIndex.value = -1
  emit('update:modelValue', null)
  input.value?.focus()
}

function open() {
  if (!props.disabled && !suppressOpen.value) opened.value = true
}

function focusInputAfterSelection() {
  suppressOpen.value = true
  nextTick(() => {
    input.value?.focus()
    suppressOpen.value = false
  })
}

function setOptionRef(element, index) {
  if (element) optionRefs.value[index] = element
}

function focusOption(index) {
  activeIndex.value = index
  nextTick(() => optionRefs.value[index]?.focus())
}

function onKeydown(event) {
  if (event.key === 'Escape') {
    opened.value = false
    return
  }
  if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
    if (!opened.value) opened.value = true
    if (!visibleOptions.value.length) return
    event.preventDefault()
    const inputHasFocus = document.activeElement === input.value
    if (event.key === 'ArrowDown' && inputHasFocus) {
      focusOption(activeIndex.value >= 0 ? activeIndex.value : 0)
      return
    }
    const direction = event.key === 'ArrowDown' ? 1 : -1
    const nextIndex = activeIndex.value + direction
    focusOption((nextIndex + visibleOptions.value.length) % visibleOptions.value.length)
    return
  }
  if (event.key === 'Enter' && opened.value && visibleOptions.value.length) {
    event.preventDefault()
    selectOption(visibleOptions.value[activeIndex.value >= 0 ? activeIndex.value : 0])
  }
}

function onOptionKeydown(event, index) {
  if (event.key === 'Enter') {
    event.preventDefault()
    selectOption(visibleOptions.value[index])
    focusInputAfterSelection()
    return
  }
  if (event.key === 'Escape') {
    event.preventDefault()
    opened.value = false
    input.value?.focus()
    return
  }
  if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
    event.preventDefault()
    const direction = event.key === 'ArrowDown' ? 1 : -1
    const nextIndex = index + direction
    focusOption((nextIndex + visibleOptions.value.length) % visibleOptions.value.length)
  }
}

function onOutside(event) {
  if (!root.value?.contains(event.target)) opened.value = false
}

watch(query, (value) => {
  activeIndex.value = -1
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

watch(visibleOptions, (options) => {
  activeIndex.value = options.length ? 0 : -1
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
      <button v-for="(option, index) in visibleOptions" v-else :key="String(valueFor(option))" :ref="(element) => setOptionRef(element, index)" type="button" class="search-select-option" :class="{ active: index === activeIndex }" @focus="activeIndex = index" @mouseenter="activeIndex = index" @keydown="onOptionKeydown($event, index)" @mousedown.prevent="selectOption(option)">{{ labelFor(option) }}</button>
    </div>
  </div>
</template>

