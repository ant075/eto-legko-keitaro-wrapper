<script setup>
import { ref } from 'vue'
const status = ref('проверка backend…')
fetch('/api/health').then((r) => r.json()).then((data) => { status.value = data.status }).catch(() => { status.value = 'backend недоступен' })
</script>
<template><main><h1>Keitaro Wrapper</h1><p>Статус backend: {{ status }}</p></main></template>

