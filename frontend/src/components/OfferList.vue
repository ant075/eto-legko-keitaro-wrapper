<script setup>
defineProps({
  offers: { type: Array, required: true },
  dirty: { type: Boolean, default: false },
})

const emit = defineEmits(['pin', 'unpin', 'delete', 'restore'])

const pinTitle = 'Закрепить оффер: его вес НЕ будет пересчитываться при изменении состава офферов'
const unpinTitle = 'Открепить оффер: его вес будет пересчитываться при изменении состава офферов'
</script>

<template>
  <div class="offer-list" :class="{ dirty }">
    <div v-for="offer in offers" :key="offer.offer_id" class="offer-row" :class="{ deleted: offer.is_deleted }">
      <span>{{ offer.name }} <small>#{{ offer.offer_id }}</small></span>
      <span>{{ offer.weight }}%</span>
      <button
        class="pin-button"
        :class="{ pinned: offer.is_pinned }"
        :disabled="offer.is_deleted"
        :title="offer.is_pinned ? unpinTitle : pinTitle"
        :aria-label="offer.is_pinned ? unpinTitle : pinTitle"
        @click="emit(offer.is_pinned ? 'unpin' : 'pin', offer.offer_id)"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14.7 3.3a1 1 0 0 1 1.4 0l4.6 4.6a1 1 0 0 1 0 1.4l-1.8 1.8-.2 4.2a1 1 0 0 1-.3.7l-2 2-3.8-3.8-5.8 5.8a1 1 0 1 1-1.4-1.4l5.8-5.8-3.8-3.8 2-2a1 1 0 0 1 .7-.3l4.2-.2 1.8-1.8a1 1 0 0 1 1.4 0Z"/></svg>
      </button>
      <button @click="emit(offer.is_deleted ? 'restore' : 'delete', offer.offer_id)">
        {{ offer.is_deleted ? 'Восстановить' : 'Удалить' }}
      </button>
    </div>
    <p v-if="!offers.length" class="muted">Офферов нет.</p>
  </div>
</template>

