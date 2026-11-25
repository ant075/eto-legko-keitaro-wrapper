<script setup>
defineProps({
  offers: { type: Array, required: true },
  dirty: { type: Boolean, default: false },
})

const emit = defineEmits(['pin', 'unpin', 'delete', 'restore'])
</script>

<template>
  <div class="offer-list" :class="{ dirty }">
    <div v-for="offer in offers" :key="offer.offer_id" class="offer-row" :class="{ deleted: offer.is_deleted }">
      <span>{{ offer.name }} <small>#{{ offer.offer_id }}</small></span>
      <span>{{ offer.weight }}%</span>
      <button :disabled="offer.is_deleted" :class="{ pinned: offer.is_pinned }" @click="emit(offer.is_pinned ? 'unpin' : 'pin', offer.offer_id)">
        {{ offer.is_pinned ? 'Открепить' : 'Закрепить' }}
      </button>
      <button @click="emit(offer.is_deleted ? 'restore' : 'delete', offer.offer_id)">
        {{ offer.is_deleted ? 'Восстановить' : 'Удалить' }}
      </button>
    </div>
    <p v-if="!offers.length" class="muted">Офферов нет.</p>
  </div>
</template>

