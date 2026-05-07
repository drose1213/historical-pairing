<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { CheckCircle2, CircleAlert, RotateCcw, User, LogIn, Trophy, TrendingUp } from "lucide-vue-next";
import { useGameStore } from "../stores/game";
import { useAuthStore } from "../stores/auth";
import { getUserStats, type UserStatsResponse } from "../api";

const router = useRouter();
const gameStore = useGameStore();
const authStore = useAuthStore();

const results = computed(() => gameStore.results);
const timeUsed = computed(() => gameStore.timeUsed);
const keyword = computed(() => gameStore.currentGame?.keyword ?? "");

const userStats = ref<UserStatsResponse | null>(null);

async function loadStats() {
  if (!authStore.isLoggedIn) return;
  try {
    userStats.value = await getUserStats();
  } catch {
    userStats.value = null;
  }
}

onMounted(loadStats);

function formatTime(seconds: number) {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return mins > 0 ? `${mins}分${secs}秒` : `${secs}秒`;
}

function playAgain() {
  router.push({ path: "/", query: { keyword: keyword.value } });
}

// 题型正确率统计
const typeStats = computed(() => {
  if (!results.value?.results) return [];
  const map: Record<string, { total: number; correct: number }> = {};
  for (const r of results.value.results) {
    if (!map[r.type]) map[r.type] = { total: 0, correct: 0 };
    map[r.type].total++;
    if (r.isCorrect) map[r.type].correct++;
  }
  return Object.entries(map).map(([type, v]) => ({
    type,
    total: v.total,
    correct: v.correct,
    rate: v.total > 0 ? v.correct / v.total : 0,
  }));
});

// 题目分析（关键词分布）
const keywordStats = computed(() => {
  if (!results.value?.results) return [];
  const kw = keyword.value;
  const total = results.value.results.length;
  const correct = results.value.results.filter((r) => r.isCorrect).length;
  return [{
    keyword: kw,
    total,
    correct,
    rate: total > 0 ? correct / total : 0,
  }];
});

const tendency = computed(() => userStats.value?.tendency ?? null);
</script>

<template>
  <main class="results-page">
    <header class="topbar">
      <div>
        <p class="eyebrow">历史配对</p>
        <h1>游戏结果</h1>
      </div>
    </header>

    <!-- 得分摘要 -->
    <section class="results-summary">
      <div class="score-card primary">
        <div class="score">{{ results?.final_score ?? 0 }}</div>
        <div class="score-label">综合得分</div>
      </div>
      <div class="score-card">
        <div class="score small">{{ results?.correct_count ?? 0 }}/{{ results?.total }}</div>
        <div class="score-label">答对题数</div>
      </div>
      <div class="time-card">
        <div class="time">{{ formatTime(timeUsed || 0) }}</div>
        <div class="time-label">用时</div>
      </div>
    </section>

    <!-- 数据分析卡片（用户倾向） -->
    <section v-if="tendency" class="data-analysis-card">
      <div class="card-icon green">
        <TrendingUp :size="20" />
      </div>
      <div class="card-body">
        <p class="card-title">数据分析</p>
        <p class="card-desc">{{ tendency }}</p>
      </div>
    </section>

    <!-- 两张分析卡片 -->
    <section class="analysis-cards">
      <!-- 题目分析卡片 -->
      <div class="analysis-card kw-card">
        <div class="card-header-bar green-bar">
          <span class="card-type-label">题目分析</span>
        </div>
        <div class="card-content">
          <div v-for="stat in keywordStats" :key="stat.keyword" class="stat-row">
            <div class="stat-label-col">
              <span class="stat-kw">{{ stat.keyword }}</span>
              <span class="stat-count">{{ stat.correct }}/{{ stat.total }}</span>
            </div>
            <div class="stat-track">
              <div
                class="stat-fill green-fill"
                :style="{ width: `${stat.rate * 100}%` }"
              ></div>
            </div>
            <span class="stat-pct green-pct">{{ (stat.rate * 100).toFixed(0) }}%</span>
          </div>
        </div>
      </div>

      <!-- 题型准确率卡片 -->
      <div class="analysis-card type-card">
        <div class="card-header-bar purple-bar">
          <span class="card-type-label">题型准确率</span>
        </div>
        <div class="card-content">
          <div v-for="stat in typeStats" :key="stat.type" class="stat-row">
            <div class="stat-label-col">
              <span class="stat-kw">{{ stat.type }}</span>
              <span class="stat-count">{{ stat.correct }}/{{ stat.total }}</span>
            </div>
            <div class="stat-track">
              <div
                class="stat-fill purple-fill"
                :style="{
                  width: `${stat.rate * 100}%`,
                  background: stat.rate >= 0.75 ? '#8b5cf6' : stat.rate >= 0.4 ? '#a78bfa' : '#c4b5fd',
                }"
              ></div>
            </div>
            <span
              class="stat-pct"
              :style="{ color: stat.rate >= 0.75 ? '#7c3aed' : stat.rate >= 0.4 ? '#8b5cf6' : '#a78bfa' }"
            >{{ (stat.rate * 100).toFixed(0) }}%</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 答案对照 -->
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
              <span v-if="item.isCorrect" class="right-text is-correct">{{ item.correctRight }}</span>
              <template v-else>
                <span class="right-text is-wrong">{{ item.userRight || "未作答" }}</span>
                <span class="correct-label">正确：</span>
                <span class="right-text is-correct">{{ item.correctRight }}</span>
              </template>
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
      <button class="action-btn" @click="router.push('/leaderboard')">
        <Trophy :size="18" />
        <span>排行榜</span>
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

/* 得分摘要 */
.results-summary {
  display: flex;
  gap: 16px;
  max-width: 560px;
  margin: 24px auto;
  justify-content: center;
}

.score-card,
.time-card {
  flex: 1;
  background: white;
  border-radius: 16px;
  padding: 20px 16px;
  text-align: center;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.score-card.primary {
  background: linear-gradient(135deg, #f0f9f6, #e0f2ec);
  border: 2px solid #246b55;
}

.score {
  font-size: 42px;
  font-weight: 800;
  color: #246b55;
  line-height: 1;
}

.score.small {
  font-size: 32px;
}

.score-label,
.time-label {
  font-size: 13px;
  color: #6b7280;
  margin-top: 8px;
}

.time {
  font-size: 32px;
  font-weight: 800;
  color: #1a1a1a;
}

/* 数据分析卡片 */
.data-analysis-card {
  display: flex;
  gap: 14px;
  align-items: flex-start;
  max-width: 560px;
  margin: 0 auto 16px;
  background: linear-gradient(135deg, #f0fdf4, #e8f5ee);
  border: 1px solid #86efac;
  border-radius: 14px;
  padding: 14px 18px;
}

.card-icon {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-icon.green {
  background: #22c55e;
  color: white;
}

.card-body {
  flex: 1;
}

.card-title {
  font-size: 11px;
  font-weight: 700;
  color: #6b7280;
  margin: 0 0 3px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.card-desc {
  font-size: 14px;
  color: #1a1a1a;
  line-height: 1.6;
  margin: 0;
  font-weight: 500;
}

/* 两张分析卡片 */
.analysis-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-width: 560px;
  margin: 0 auto 20px;
}

.analysis-card {
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.kw-card {
  background: linear-gradient(135deg, #ecfdf5, #d1fae5);
}

.type-card {
  background: linear-gradient(135deg, #f5f3ff, #ede9fe);
}

.card-header-bar {
  padding: 10px 18px;
}

.green-bar {
  background: rgba(34, 197, 94, 0.15);
  border-bottom: 1px solid rgba(34, 197, 94, 0.25);
}

.purple-bar {
  background: rgba(139, 92, 246, 0.12);
  border-bottom: 1px solid rgba(139, 92, 246, 0.2);
}

.card-type-label {
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.green-bar .card-type-label {
  color: #15803d;
}

.purple-bar .card-type-label {
  color: #7c3aed;
}

.card-content {
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stat-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.stat-label-col {
  width: 100px;
  flex-shrink: 0;
}

.stat-kw {
  display: block;
  font-size: 14px;
  font-weight: 700;
  color: #1a1a1a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.stat-count {
  font-size: 11px;
  color: #6b7280;
  font-weight: 600;
}

.stat-track {
  flex: 1;
  height: 10px;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 5px;
  overflow: hidden;
}

.stat-fill {
  height: 100%;
  border-radius: 5px;
  transition: width 0.5s ease;
}

.green-fill {
  background: linear-gradient(90deg, #22c55e, #4ade80);
}

.purple-fill {
  background: linear-gradient(90deg, #8b5cf6, #a78bfa);
}

.stat-pct {
  width: 42px;
  text-align: right;
  font-size: 14px;
  font-weight: 800;
  flex-shrink: 0;
}

.green-pct {
  color: #15803d;
}

/* 答案对照 */
.results-table {
  max-width: 560px;
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
  text-decoration: line-through;
}

.correct-label {
  font-size: 12px;
  color: #6b7280;
  margin-left: 4px;
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
  flex-wrap: wrap;
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
