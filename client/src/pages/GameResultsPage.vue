<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { CheckCircle2, CircleAlert, LogIn, RotateCcw, Trophy, User } from "lucide-vue-next";
import {
  getHistoryDetail,
  type HistoryDetailResponse,
} from "../api";
import { useAuthStore } from "../stores/auth";
import { useGameStore } from "../stores/game";

const route = useRoute();
const router = useRouter();
const gameStore = useGameStore();
const authStore = useAuthStore();

const historyDetail = ref<HistoryDetailResponse | null>(null);
const detailLoading = ref(false);
const detailError = ref("");

const gameId = computed(() => route.params.gameId as string);
const storeResults = computed(() => gameStore.results);
const usingStoreResults = computed(() => Boolean(storeResults.value?.results?.length));

const displayKeyword = computed(() => {
  if (usingStoreResults.value) return gameStore.currentGame?.keyword ?? "";
  return historyDetail.value?.keyword ?? "";
});

const displayTimeUsed = computed(() => {
  if (usingStoreResults.value) return gameStore.timeUsed ?? 0;
  return historyDetail.value?.time_used ?? 0;
});

const displayScore = computed(() => {
  if (usingStoreResults.value) return storeResults.value?.final_score ?? 0;
  return historyDetail.value?.score ?? 0;
});

const displayCorrectCount = computed(() => {
  if (usingStoreResults.value) return storeResults.value?.correct_count ?? 0;
  return historyDetail.value?.results.filter((item) => item.is_correct).length ?? 0;
});

const displayTotal = computed(() => {
  if (usingStoreResults.value) return storeResults.value?.total ?? 0;
  return historyDetail.value?.total ?? 0;
});

const displayResults = computed(() => {
  if (usingStoreResults.value) {
    return (storeResults.value?.results ?? []).map((item) => ({
      key: item.leftId,
      left: item.left,
      userRight: item.userRight,
      correctRight: item.correctRight,
      isCorrect: item.isCorrect,
      explanation: item.explanation,
      type: item.type,
    }));
  }

  return (historyDetail.value?.results ?? []).map((item, index) => ({
    key: `${item.left}-${index}`,
    left: item.left,
    userRight: item.right,
    correctRight: item.correct_right,
    isCorrect: item.is_correct,
    explanation: item.explanation,
    type: item.type,
  }));
});

async function loadHistoryDetail() {
  if (usingStoreResults.value) return;
  detailLoading.value = true;
  detailError.value = "";
  try {
    historyDetail.value = await getHistoryDetail(gameId.value);
  } catch (error) {
    detailError.value = error instanceof Error ? error.message : "加载答题详情失败";
  } finally {
    detailLoading.value = false;
  }
}

function formatTime(seconds: number) {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return mins > 0 ? `${mins}分${secs}秒` : `${secs}秒`;
}

function playAgain() {
  router.push({ path: "/", query: { keyword: displayKeyword.value } });
}

// Card modal
const selectedCard = ref<(typeof displayResults.value)[number] | null>(null);

function openCard(item: (typeof displayResults.value)[number]) {
  selectedCard.value = item;
}

function closeCard() {
  selectedCard.value = null;
}

// Generate a unique card ID based on content
function getCardId(item: (typeof displayResults.value)[number], index: number) {
  const str = item.left + item.correctRight + item.type + index;
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash;
  }
  return Math.abs(hash);
}

// Card color themes
const cardThemes = [
  { bg: "linear-gradient(135deg, #246b55 0%, #35c494 100%)", accent: "#35c494", border: "#1a5a45" },
  { bg: "linear-gradient(135deg, #2f7f95 0%, #68d7ed 100%)", accent: "#68d7ed", border: "#1d6075" },
  { bg: "linear-gradient(135deg, #7c3aed 0%, #a78bfa 100%)", accent: "#a78bfa", border: "#5b21b6" },
  { bg: "linear-gradient(135deg, #dc2626 0%, #f87171 100%)", accent: "#f87171", border: "#991b1b" },
  { bg: "linear-gradient(135deg, #d97706 0%, #fbbf24 100%)", accent: "#fbbf24", border: "#92400e" },
  { bg: "linear-gradient(135deg, #059669 0%, #34d399 100%)", accent: "#34d399", border: "#065f46" },
];

function getCardTheme(index: number) {
  return cardThemes[index % cardThemes.length];
}

onMounted(async () => {
  await loadHistoryDetail();
});
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
      <div class="score-card primary">
        <div class="score">{{ displayScore }}</div>
        <div class="score-label">综合得分</div>
      </div>
      <div class="score-card">
        <div class="score small">{{ displayCorrectCount }}/{{ displayTotal }}</div>
        <div class="score-label">答对题数</div>
      </div>
      <div class="time-card">
        <div class="time">{{ formatTime(displayTimeUsed) }}</div>
        <div class="time-label">用时</div>
      </div>
    </section>

    <section class="results-table">
      <h2>答案对照</h2>
      <p class="table-hint">点击答案查看详情</p>

      <div v-if="detailLoading" class="status-text">加载中...</div>
      <div v-else-if="detailError" class="status-text error-text">{{ detailError }}</div>
      <div v-else-if="displayResults.length === 0" class="status-text">暂无答题详情</div>

      <div v-else class="table">
        <div
          v-for="(item, index) in displayResults"
          :key="item.key"
          class="result-row"
          :class="item.isCorrect ? 'is-correct' : 'is-wrong'"
          @click="openCard(item)"
        >
          <div class="result-icon">
            <CheckCircle2 v-if="item.isCorrect" :size="22" />
            <CircleAlert v-else :size="22" />
          </div>
          <div class="result-content">
            <div class="pair-info">
              <span class="left-text">{{ item.left }}</span>
              <span class="arrow">→</span>
              <span v-if="item.isCorrect" class="right-text is-correct clickable">{{ item.correctRight }}</span>
              <template v-else>
                <span class="right-text is-wrong clickable">{{ item.userRight || "未作答" }}</span>
                <span class="correct-label">→</span>
                <span class="right-text is-correct">{{ item.correctRight }}</span>
              </template>
            </div>
            <p class="type">{{ item.type }}</p>
          </div>
        </div>
      </div>
    </section>

    <section class="actions">
      <button class="action-btn primary" type="button" @click="playAgain">
        <RotateCcw :size="18" />
        <span>再来一局</span>
      </button>
      <button class="action-btn" type="button" @click="router.push('/leaderboard')">
        <Trophy :size="18" />
        <span>排行榜</span>
      </button>
      <button v-if="authStore.isLoggedIn" class="action-btn" type="button" @click="router.push('/profile')">
        <User :size="18" />
        <span>查看战绩</span>
      </button>
      <button v-else class="action-btn" type="button" @click="router.push('/')">
        <LogIn :size="18" />
        <span>登录后查看战绩</span>
      </button>
    </section>

    <!-- Card Modal -->
    <Teleport to="body">
      <div v-if="selectedCard" class="card-modal-overlay" @click="closeCard">
        <div
          class="collectible-card"
          :class="selectedCard.isCorrect ? 'card-correct' : 'card-wrong'"
          @click.stop
        >
          <button class="card-close" @click="closeCard">×</button>

          <div class="card-ornament-top">
            <div class="ornament-line"></div>
            <div class="ornament-dots">
              <span v-for="n in 5" :key="n" class="ornament-dot"></span>
            </div>
            <div class="ornament-line"></div>
          </div>

          <div class="card-badge" :class="selectedCard.isCorrect ? 'badge-correct' : 'badge-wrong'">
            <CheckCircle2 v-if="selectedCard.isCorrect" :size="14" />
            <CircleAlert v-else :size="14" />
            {{ selectedCard.isCorrect ? "回答正确" : "回答错误" }}
          </div>

          <div class="card-corner-lu"></div>
          <div class="card-corner-ru"></div>
          <div class="card-corner-ld"></div>
          <div class="card-corner-rd"></div>

          <div class="card-id">NO.{{ getCardId(selectedCard, displayResults.indexOf(selectedCard)) }}</div>

          <div class="card-type">{{ selectedCard.type }}</div>

          <div class="card-pair">
            <div class="card-side left-side">
              <div class="side-label">题目</div>
              <div class="side-value">{{ selectedCard.left }}</div>
            </div>
            <div class="card-divider">
              <div class="divider-line"></div>
              <div class="divider-icon">↔</div>
              <div class="divider-line"></div>
            </div>
            <div class="card-side right-side">
              <div class="side-label">正确答案</div>
              <div class="side-value correct">{{ selectedCard.correctRight }}</div>
            </div>
          </div>

          <div v-if="!selectedCard.isCorrect && selectedCard.userRight" class="card-user-answer">
            <div class="side-label">你的答案</div>
            <div class="side-value wrong">{{ selectedCard.userRight }}</div>
          </div>

          <div class="card-explanation">
            <div class="explanation-label">解析</div>
            <div class="explanation-text">{{ selectedCard.explanation }}</div>
          </div>

          <div class="card-ornament-bottom">
            <div class="ornament-line"></div>
            <div class="ornament-dots">
              <span v-for="n in 5" :key="n" class="ornament-dot"></span>
            </div>
            <div class="ornament-line"></div>
          </div>
        </div>
      </div>
    </Teleport>
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

.score.small,
.time {
  font-size: 32px;
}

.score-label,
.time-label {
  font-size: 13px;
  color: #6b7280;
  margin-top: 8px;
}

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
  margin: 0 0 4px;
}

.table-hint {
  font-size: 12px;
  color: #9ca3af;
  margin: 0 0 16px;
}

.status-text {
  color: #6b7280;
  padding: 8px 0;
}

.error-text {
  color: #dc2626;
}

.table {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.result-row {
  display: flex;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  cursor: pointer;
  transition: all 0.2s;
}

.result-row.is-correct {
  background: #f0fdf4;
  border-color: #86efac;
}

.result-row.is-wrong {
  background: #fef2f2;
  border-color: #fca5a5;
}

.result-row:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.result-icon {
  flex-shrink: 0;
  margin-top: 2px;
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

.right-text.clickable {
  cursor: pointer;
}

.right-text.clickable:hover {
  text-decoration: underline;
  text-decoration-style: dotted;
}

.correct-label {
  font-size: 12px;
  color: #6b7280;
  margin-left: 4px;
}

.type {
  font-size: 12px;
  color: #9ca3af;
  margin: 4px 0 0;
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

/* Collectible Card Modal */
.card-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.collectible-card {
  position: relative;
  background: linear-gradient(145deg, #faf6ee 0%, #f0e8d6 60%, #e8dcc8 100%);
  border: 3px solid #c9b98a;
  border-radius: 20px;
  padding: 28px 24px 24px;
  max-width: 380px;
  width: 100%;
  box-shadow:
    0 20px 60px rgba(0, 0, 0, 0.3),
    0 0 0 1px rgba(255, 255, 255, 0.1) inset,
    0 0 40px rgba(201, 185, 138, 0.3);
  animation: cardAppear 0.3s ease-out;
}

.collectible-card.card-correct {
  border-color: #22c55e;
  box-shadow:
    0 20px 60px rgba(0, 0, 0, 0.3),
    0 0 0 1px rgba(255, 255, 255, 0.1) inset,
    0 0 30px rgba(34, 197, 94, 0.2);
}

.collectible-card.card-wrong {
  border-color: #ef4444;
  box-shadow:
    0 20px 60px rgba(0, 0, 0, 0.3),
    0 0 0 1px rgba(255, 255, 255, 0.1) inset,
    0 0 30px rgba(239, 68, 68, 0.2);
}

@keyframes cardAppear {
  from {
    opacity: 0;
    transform: scale(0.9) rotateX(10deg);
  }
  to {
    opacity: 1;
    transform: scale(1) rotateX(0);
  }
}

.card-close {
  position: absolute;
  top: 12px;
  right: 12px;
  background: rgba(0, 0, 0, 0.1);
  border: none;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #6b7280;
  transition: all 0.2s;
  font-size: 20px;
  line-height: 1;
  font-weight: 300;
}

.card-close:hover {
  background: rgba(0, 0, 0, 0.2);
  color: #1a1a1a;
}

.card-corner-lu,
.card-corner-ru,
.card-corner-ld,
.card-corner-rd {
  position: absolute;
  width: 20px;
  height: 20px;
  border-color: #c9b98a;
  border-style: solid;
}

.card-correct .card-corner-lu,
.card-correct .card-corner-ru,
.card-correct .card-corner-ld,
.card-correct .card-corner-rd {
  border-color: #22c55e;
}

.card-wrong .card-corner-lu,
.card-wrong .card-corner-ru,
.card-wrong .card-corner-ld,
.card-wrong .card-corner-rd {
  border-color: #ef4444;
}

.card-corner-lu {
  top: 8px;
  left: 8px;
  border-width: 3px 0 0 3px;
  border-radius: 6px 0 0 0;
}

.card-corner-ru {
  top: 8px;
  right: 8px;
  border-width: 3px 3px 0 0;
  border-radius: 0 6px 0 0;
}

.card-corner-ld {
  bottom: 8px;
  left: 8px;
  border-width: 0 0 3px 3px;
  border-radius: 0 0 0 6px;
}

.card-corner-rd {
  bottom: 8px;
  right: 8px;
  border-width: 0 3px 3px 0;
  border-radius: 0 0 6px 0;
}

.card-id {
  position: absolute;
  top: 14px;
  left: 20px;
  font-size: 10px;
  color: #9ca3af;
  font-weight: 600;
  letter-spacing: 1px;
  font-family: monospace;
}

.card-type {
  text-align: center;
  font-size: 11px;
  font-weight: 700;
  color: #8b7355;
  letter-spacing: 3px;
  text-transform: uppercase;
  margin-bottom: 16px;
}

.card-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 700;
  margin: 0 auto 20px;
  width: fit-content;
}

.card-badge.badge-correct {
  background: linear-gradient(135deg, #22c55e, #4ade80);
  color: white;
}

.card-badge.badge-wrong {
  background: linear-gradient(135deg, #ef4444, #f87171);
  color: white;
}

.card-pair {
  display: flex;
  align-items: stretch;
  gap: 12px;
  margin-bottom: 16px;
}

.card-side {
  flex: 1;
  background: rgba(255, 255, 255, 0.7);
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  padding: 12px;
  text-align: center;
}

.side-label {
  font-size: 10px;
  font-weight: 700;
  color: #9ca3af;
  letter-spacing: 2px;
  text-transform: uppercase;
  margin-bottom: 6px;
}

.side-value {
  font-size: 15px;
  font-weight: 700;
  color: #1a1a1a;
  line-height: 1.3;
}

.side-value.correct {
  color: #22c55e;
}

.side-value.wrong {
  color: #ef4444;
  text-decoration: line-through;
}

.card-divider {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  width: 30px;
}

.divider-line {
  flex: 1;
  width: 2px;
  background: linear-gradient(to bottom, transparent, #c9b98a, transparent);
}

.divider-icon {
  font-size: 12px;
  color: #c9b98a;
}

.card-user-answer {
  background: rgba(254, 226, 226, 0.5);
  border: 1px solid #fca5a5;
  border-radius: 10px;
  padding: 10px 12px;
  margin-bottom: 16px;
  text-align: center;
}

.card-user-answer .side-value {
  color: #dc2626;
  text-decoration: line-through;
}

.card-explanation {
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 14px;
}

.explanation-label {
  font-size: 10px;
  font-weight: 700;
  color: #9ca3af;
  letter-spacing: 2px;
  text-transform: uppercase;
  margin-bottom: 6px;
}

.explanation-text {
  font-size: 14px;
  color: #4b5563;
  line-height: 1.6;
}

.card-ornament-top,
.card-ornament-bottom {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 16px 0;
}

.ornament-line {
  flex: 1;
  height: 2px;
  background: linear-gradient(to right, transparent, #c9b98a, transparent);
}

.ornament-dots {
  display: flex;
  gap: 4px;
}

.ornament-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #c9b98a;
}

@media (max-width: 640px) {
  .results-summary {
    flex-direction: column;
  }

  .results-table,
  .results-summary {
    max-width: 100%;
  }
}
</style>
