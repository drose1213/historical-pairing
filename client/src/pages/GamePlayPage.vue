<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from "vue";
import { useRouter, useRoute } from "vue-router";
import { Send, X } from "lucide-vue-next";
import { useGameStore } from "../stores/game";
import { useAuthStore } from "../stores/auth";
import { trackEvent } from "../api";
import CountdownTimer from "../components/CountdownTimer.vue";

const router = useRouter();
const route = useRoute();
const gameStore = useGameStore();
const authStore = useAuthStore();

const selectedLeftId = ref<string | null>(null);
const matches = ref<Record<string, string>>({});
const timeUsed = ref(0);
const timerKey = ref(0);

const gameId = computed(() => route.params.gameId as string);
const game = computed(() => gameStore.currentGame);

const matchedCount = computed(() => Object.keys(matches.value).length);
const canSubmit = computed(() => matchedCount.value === 4);

const selectedRightIds = computed(() => new Set(Object.values(matches.value)));

function rightText(rightId: string) {
  return game.value?.rightItems.find((item) => item.id === rightId)?.text ?? "";
}

function chooseLeft(item: { id: string; text: string }) {
  if (selectedLeftId.value === item.id) {
    selectedLeftId.value = null;
  } else {
    selectedLeftId.value = item.id;
  }
}

function chooseRight(item: { id: string; text: string }) {
  // If this right item is already used, do nothing
  if (selectedRightIds.value.has(item.id)) return;

  if (!selectedLeftId.value) return;

  // If clicking the same left item, deselect it
  if (matches.value[selectedLeftId.value] === item.id) {
    const next = { ...matches.value };
    delete next[selectedLeftId.value];
    matches.value = next;
    selectedLeftId.value = null;
    return;
  }

  const next = { ...matches.value };
  // Remove any existing match for this right item
  for (const [leftId, rightId] of Object.entries(next)) {
    if (rightId === item.id) {
      delete next[leftId];
    }
  }
  next[selectedLeftId.value] = item.id;
  matches.value = next;
  selectedLeftId.value = null;
}

function removeMatch(leftId: string) {
  const next = { ...matches.value };
  delete next[leftId];
  matches.value = next;
}

async function submit() {
  if (!canSubmit.value) return;

  const matchList = Object.entries(matches.value).map(([leftId, rightId]) => ({ leftId, rightId }));
  const result = await gameStore.submitGame(matchList, timeUsed.value);

  await trackEvent("game_session_end", gameId.value, {
    trigger: "user_submit",
    time_used: timeUsed.value,
    correct_count: result.score,
    total_count: result.total,
  });

  router.push(`/results/${gameId.value}`);
}

function onTimeUp() {
  submit();
}

function onTimeUpdate(seconds: number) {
  timeUsed.value = seconds;
}

onMounted(async () => {
  if (!game.value || game.value.gameId !== gameId.value) {
    router.replace("/");
    return;
  }
  timerKey.value++;
});
</script>

<template>
  <main class="play-page">
    <header class="topbar">
      <div>
        <p class="keyword">{{ game?.keyword }}</p>
        <p class="progress">{{ matchedCount }}/4 已配对</p>
      </div>
      <CountdownTimer
        :key="timerKey"
        :initial-seconds="30"
        @time-up="onTimeUp"
        @time-update="onTimeUpdate"
      />
    </header>

    <section class="game-layout">
      <div class="column">
        <div class="column-head">
          <span>人物</span>
        </div>
        <button
          v-for="item in game?.leftItems"
          :key="item.id"
          class="pair-button left-button"
          :class="{
            'is-selected': selectedLeftId === item.id,
            'is-matched': matches[item.id],
          }"
          @click="chooseLeft(item)"
        >
          <span class="item-text">{{ item.text }}</span>
          <div v-if="matches[item.id]" class="match-badge" @click.stop="removeMatch(item.id)">
            <span>{{ rightText(matches[item.id]) }}</span>
            <X :size="14" />
          </div>
        </button>
      </div>

      <div class="column">
        <div class="column-head">
          <span>事件</span>
        </div>
        <button
          v-for="item in game?.rightItems"
          :key="item.id"
          class="pair-button right-button"
          :class="{ 'is-used': selectedRightIds.has(item.id) }"
          @click="chooseRight(item)"
        >
          {{ item.text }}
        </button>
      </div>
    </section>

    <section class="action-band">
      <button class="submit-button" :disabled="!canSubmit" @click="submit">
        <Send :size="18" />
        <span>提交答案</span>
      </button>
    </section>
  </main>
</template>

<style scoped>
.play-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f0e6 0%, #e8dcc8 100%);
  padding: 0 16px;
}

.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

.keyword {
  font-size: 18px;
  font-weight: 700;
  color: #1a1a1a;
  margin: 0;
}

.progress {
  font-size: 14px;
  color: #6b7280;
  margin: 4px 0 0;
}

.game-layout {
  display: flex;
  gap: 40px;
  max-width: 900px;
  margin: 40px auto;
  justify-content: center;
}

.column {
  flex: 1;
  max-width: 360px;
}

.column-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 0 8px;
}

.column-head span {
  font-size: 14px;
  font-weight: 700;
  color: #6b7280;
  text-transform: uppercase;
}

.pair-button {
  width: 100%;
  padding: 16px;
  margin-bottom: 12px;
  border: 2px solid #d4c9b0;
  border-radius: 12px;
  background: white;
  font-size: 16px;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s;
}

.left-button.is-selected {
  border-color: #246b55;
  background: #f0f9f6;
}

.left-button.is-matched {
  border-color: #246b55;
  background: #e8f5f0;
}

.right-button.is-used {
  opacity: 0.5;
  border-color: #9ca3af;
  background: #f3f4f6;
}

.item-text {
  display: block;
  margin-bottom: 8px;
}

.match-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: #246b55;
  color: white;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
}

.match-badge:hover {
  background: #1d5243;
}

.action-band {
  display: flex;
  justify-content: center;
  padding: 20px 0 40px;
}

.submit-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px 32px;
  background: #246b55;
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.2s;
}

.submit-button:hover:not(:disabled) {
  background: #1d5243;
}

.submit-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
