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
    <div class="timer-glow"></div>
    <div class="timer-ring">
      <svg viewBox="0 0 100 100">
        <circle class="timer-bg" cx="50" cy="50" r="45" />
        <circle
          class="timer-progress"
          cx="50"
          cy="50"
          r="45"
          :stroke-dasharray="283"
          :stroke-dashoffset="283 * (1 - progress)"
        />
      </svg>
      <div class="timer-text">
        <span class="timer-number">{{ displaySeconds }}</span>
        <span class="timer-label">秒</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.countdown-timer {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.timer-glow {
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  pointer-events: none;
  transition: background 0.3s;
}

.normal .timer-glow {
  background: rgba(34, 197, 94, 0.12);
  box-shadow: 0 0 20px rgba(34, 197, 94, 0.2);
}

.warning .timer-glow {
  background: rgba(245, 158, 11, 0.15);
  box-shadow: 0 0 24px rgba(245, 158, 11, 0.3);
}

.danger .timer-glow {
  background: rgba(239, 68, 68, 0.2);
  box-shadow: 0 0 28px rgba(239, 68, 68, 0.4);
  animation: pulse-danger 0.5s ease-in-out infinite alternate;
}

@keyframes pulse-danger {
  from { transform: scale(1); }
  to   { transform: scale(1.08); }
}

.timer-ring {
  position: relative;
  width: 96px;
  height: 96px;
}

.timer-ring svg {
  transform: rotate(-90deg);
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
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
  transition: stroke-dashoffset 0.3s ease, stroke 0.5s ease;
  filter: drop-shadow(0 0 3px currentColor);
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
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1px;
}

.timer-number {
  font-size: 36px;
  font-weight: 900;
  line-height: 1;
  transition: color 0.5s ease;
}

.timer-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 2px;
  opacity: 0.7;
}

.normal .timer-number { color: #16a34a; }
.warning .timer-number { color: #d97706; }
.danger  .timer-number { color: #dc2626; animation: shake 0.4s ease-in-out infinite alternate; }

@keyframes shake {
  from { transform: translateX(0); }
  to   { transform: translateX(2px); }
}

.normal .timer-label { color: #16a34a; }
.warning .timer-label { color: #d97706; }
.danger  .timer-label { color: #dc2626; }
</style>
