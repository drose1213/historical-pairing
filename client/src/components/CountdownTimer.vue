<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from "vue";

const props = defineProps<{
  initialSeconds: number;
}>();

const emit = defineEmits<{
  timeUp: [];
  timeUpdate: [seconds: number];
}>();

const seconds = ref(props.initialSeconds);
const interval = ref<number | null>(null);

const displaySeconds = computed(() => seconds.value);
const progress = computed(() => seconds.value / props.initialSeconds);

const colorClass = computed(() => {
  if (seconds.value <= 5) return "danger";
  if (seconds.value <= 10) return "warning";
  return "normal";
});

function startTimer() {
  if (interval.value) return;

  interval.value = window.setInterval(() => {
    seconds.value--;
    emit("timeUpdate", props.initialSeconds - seconds.value);

    if (seconds.value <= 0) {
      if (interval.value) {
        clearInterval(interval.value);
        interval.value = null;
      }
      emit("timeUp");
    }
  }, 1000);
}

function stopTimer() {
  if (interval.value) {
    clearInterval(interval.value);
    interval.value = null;
  }
}

watch(
  () => props.initialSeconds,
  () => {
    stopTimer();
    seconds.value = props.initialSeconds;
    startTimer();
  }
);

onMounted(() => {
  startTimer();
});

onUnmounted(() => {
  stopTimer();
});
</script>

<template>
  <div class="countdown-timer" :class="colorClass">
    <div class="timer-ring">
      <svg viewBox="0 0 100 100">
        <circle
          class="timer-bg"
          cx="50"
          cy="50"
          r="45"
        />
        <circle
          class="timer-progress"
          cx="50"
          cy="50"
          r="45"
          :stroke-dasharray="283"
          :stroke-dashoffset="283 * (1 - progress)"
        />
      </svg>
      <div class="timer-text">{{ displaySeconds }}</div>
    </div>
  </div>
</template>

<style scoped>
.countdown-timer {
  display: flex;
  align-items: center;
  justify-content: center;
}

.timer-ring {
  position: relative;
  width: 80px;
  height: 80px;
}

.timer-ring svg {
  transform: rotate(-90deg);
}

.timer-bg {
  fill: none;
  stroke: #e5e7eb;
  stroke-width: 8;
}

.timer-progress {
  fill: none;
  stroke: #22c55e;
  stroke-width: 8;
  stroke-linecap: round;
  transition: stroke-dashoffset 0.3s ease;
}

.normal .timer-progress {
  stroke: #22c55e;
}

.warning .timer-progress {
  stroke: #f59e0b;
}

.danger .timer-progress {
  stroke: #ef4444;
}

.timer-text {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  font-weight: 800;
  color: #1a1a1a;
}

.normal .timer-text {
  color: #22c55e;
}

.warning .timer-text {
  color: #f59e0b;
}

.danger .timer-text {
  color: #ef4444;
}
</style>
