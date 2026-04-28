<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";
import { CheckCircle2, CircleAlert, RotateCcw, User, LogIn } from "lucide-vue-next";
import { useGameStore } from "../stores/game";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const gameStore = useGameStore();
const authStore = useAuthStore();

const results = computed(() => gameStore.results);
const timeUsed = computed(() => gameStore.timeUsed);
const keyword = computed(() => gameStore.currentGame?.keyword ?? "");

function formatTime(seconds: number) {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return mins > 0 ? `${mins}分${secs}秒` : `${secs}秒`;
}

function playAgain() {
  router.push("/");
}
</script>

<template>
  <main class="results-page">
    <header class="topbar">
      <div>
        <p class="eyebrow">历史配对</p>
        <h1>游戏结果</h1>
      </div>
    </header>

    <section class="results-summary">
      <div class="score-card">
        <div class="score">{{ results?.score }}/{{ results?.total }}</div>
        <div class="score-label">正确匹配</div>
      </div>
      <div class="time-card">
        <div class="time">{{ formatTime(timeUsed || 0) }}</div>
        <div class="time-label">用时</div>
      </div>
    </section>

    <section class="results-table">
      <h2>答案对照</h2>
      <div class="table">
        <div
          v-for="item in results?.results"
          :key="item.leftId"
          class="result-row"
          :class="item.isCorrect ? 'is-correct' : 'is-wrong'"
        >
          <div class="result-icon">
            <CheckCircle2 v-if="item.isCorrect" :size="24" />
            <CircleAlert v-else :size="24" />
          </div>
          <div class="result-content">
            <div class="pair-info">
              <span class="left-text">{{ item.left }}</span>
              <span class="arrow">→</span>
              <span class="right-text" :class="{ 'is-correct': item.isCorrect, 'is-wrong': !item.isCorrect }">
                {{ item.isCorrect ? item.correctRight : (item.userRight || "未作答") }}
              </span>
            </div>
            <p class="explanation">{{ item.explanation }}</p>
            <p class="type">{{ item.type }}</p>
          </div>
        </div>
      </div>
    </section>

    <section class="actions">
      <button class="action-btn primary" @click="playAgain">
        <RotateCcw :size="18" />
        <span>再来一局</span>
      </button>
      <button v-if="authStore.isLoggedIn" class="action-btn" @click="router.push('/profile')">
        <User :size="18" />
        <span>查看战绩</span>
      </button>
      <button v-else class="action-btn" @click="router.push('/')">
        <LogIn :size="18" />
        <span>登录后查看战绩</span>
      </button>
    </section>
  </main>
</template>

<style scoped>
.results-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f0e6 0%, #e8dcc8 100%);
  padding: 0 16px;
}

.topbar {
  padding: 20px 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

.eyebrow {
  font-size: 12px;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin: 0;
}

h1 {
  font-size: 24px;
  font-weight: 800;
  color: #1a1a1a;
  margin: 4px 0 0;
}

.results-summary {
  display: flex;
  gap: 20px;
  max-width: 500px;
  margin: 40px auto;
  justify-content: center;
}

.score-card,
.time-card {
  flex: 1;
  background: white;
  border-radius: 16px;
  padding: 24px;
  text-align: center;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.score {
  font-size: 48px;
  font-weight: 800;
  color: #246b55;
}

.score-label,
.time-label {
  font-size: 14px;
  color: #6b7280;
  margin-top: 8px;
}

.time {
  font-size: 36px;
  font-weight: 800;
  color: #1a1a1a;
}

.results-table {
  max-width: 600px;
  margin: 0 auto;
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.results-table h2 {
  font-size: 18px;
  font-weight: 700;
  color: #1a1a1a;
  margin: 0 0 20px;
}

.table {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.result-row {
  display: flex;
  gap: 12px;
  padding: 16px;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
}

.result-row.is-correct {
  background: #f0fdf4;
  border-color: #86efac;
}

.result-row.is-wrong {
  background: #fef2f2;
  border-color: #fca5a5;
}

.result-icon {
  flex-shrink: 0;
}

.is-correct .result-icon {
  color: #22c55e;
}

.is-wrong .result-icon {
  color: #ef4444;
}

.result-content {
  flex: 1;
}

.pair-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.left-text {
  font-weight: 700;
  color: #1a1a1a;
}

.arrow {
  color: #9ca3af;
}

.right-text.is-correct {
  color: #22c55e;
}

.right-text.is-wrong {
  color: #ef4444;
}

.explanation {
  font-size: 14px;
  color: #4b5563;
  margin: 8px 0 4px;
  line-height: 1.5;
}

.type {
  font-size: 12px;
  color: #9ca3af;
  margin: 0;
}

.actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  padding: 40px 0;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 24px;
  background: white;
  border: 2px solid #d4c9b0;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn.primary {
  background: #246b55;
  color: white;
  border-color: #246b55;
}

.action-btn:hover {
  border-color: #246b55;
  color: #246b55;
}

.action-btn.primary:hover {
  background: #1d5243;
  color: white;
}
</style>
