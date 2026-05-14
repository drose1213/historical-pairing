<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ArrowLeft, ChevronLeft, ChevronRight, LogOut } from "lucide-vue-next";
import { getHistory, getUserStats, type HistoryItem, type UserStatsResponse } from "../api";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

const history = ref<HistoryItem[]>([]);
const total = ref(0);
const page = ref(1);
const pageSize = 5;
const loading = ref(false);
const stats = ref<UserStatsResponse | null>(null);
const statsLoading = ref(false);
const showStats = ref(true);
const activeChart = ref<"periods" | "types">("periods");

const totalPages = computed(() => Math.ceil(total.value / pageSize));
const maxPeriodCount = computed(() => {
  if (!stats.value?.periods.length) return 0;
  return Math.max(...stats.value.periods.map((item) => item.count));
});

function formatDate(dateStr: string) {
  const date = new Date(dateStr);
  return date.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatTime(seconds: number | null) {
  if (!seconds) return "-";
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return mins > 0 ? `${mins}分${secs}秒` : `${secs}秒`;
}

function accuracy(item: HistoryItem) {
  if (item.score === null || item.total === 0) return "-";
  return `${Math.round((item.score / item.total) * 100)}%`;
}

function barWidth(value: number, max: number) {
  if (max === 0) return "0%";
  return `${Math.max(4, Math.round((value / max) * 100))}%`;
}

function pageFromQuery() {
  const rawPage = Number(route.query.page);
  return Number.isInteger(rawPage) && rawPage > 0 ? rawPage : 1;
}

function syncPageQuery() {
  router.replace({
    path: "/profile",
    query: page.value > 1 ? { page: String(page.value) } : {},
  });
}

async function fetchHistory() {
  loading.value = true;
  try {
    const response = await getHistory(page.value, pageSize);
    history.value = response.items;
    total.value = response.total;
  } catch (err) {
    console.error("Failed to fetch history:", err);
  } finally {
    loading.value = false;
  }
}

async function fetchStats() {
  statsLoading.value = true;
  try {
    stats.value = await getUserStats();
  } catch (err) {
    console.error("Failed to fetch stats:", err);
  } finally {
    statsLoading.value = false;
  }
}

function prevPage() {
  if (page.value > 1) {
    page.value--;
    syncPageQuery();
    fetchHistory();
  }
}

function nextPage() {
  if (page.value < totalPages.value) {
    page.value++;
    syncPageQuery();
    fetchHistory();
  }
}

function viewDetail(item: HistoryItem) {
  router.push({
    path: `/results/${item.id}`,
    query: { from: "profile", historyPage: String(page.value) },
  });
}

function logout() {
  authStore.logout();
  router.push("/");
}

onMounted(() => {
  page.value = pageFromQuery();
  fetchHistory();
  fetchStats();
});
</script>

<template>
  <main class="profile-page">
    <header class="topbar">
      <button class="icon-btn" type="button" @click="router.push('/')">
        <ArrowLeft :size="20" />
      </button>
      <div>
        <p class="eyebrow">个人中心</p>
        <h1>我的战绩</h1>
      </div>
      <button class="logout-btn" type="button" @click="logout">
        <LogOut :size="18" />
        <span>退出</span>
      </button>
    </header>

    <section class="user-info">
      <div class="email">{{ authStore.user?.email }}</div>
      <div class="stats-summary">
        <div class="stat">
          <span class="stat-value">{{ stats?.total_games ?? total }}</span>
          <span class="stat-label">总场次</span>
        </div>
        <div v-if="stats && stats.total_games > 0" class="stat">
          <span class="stat-value">{{ stats.avg_score.toFixed(1) }}</span>
          <span class="stat-label">平均分</span>
        </div>
        <div v-if="stats && stats.total_games > 0" class="stat">
          <span class="stat-value">{{ stats.max_score }}</span>
          <span class="stat-label">最高分</span>
        </div>
      </div>
    </section>

    <section v-if="stats && stats.total_games > 0" class="stats-section">
      <button class="section-toggle" type="button" @click="showStats = !showStats">
        <span>数据分析</span>
        <span>{{ showStats ? "收起" : "展开" }}</span>
      </button>

      <div v-if="showStats" class="stats-content">
        <div class="stats-cards">
          <div class="stat-card">
            <div class="card-label">分数区间</div>
            <div class="card-value">{{ stats.min_score }} - {{ stats.max_score }}</div>
          </div>
          <div class="stat-card">
            <div class="card-label">平均用时</div>
            <div class="card-value">{{ stats.avg_time ? `${stats.avg_time.toFixed(0)}秒` : "-" }}</div>
          </div>
          <div class="stat-card">
            <div class="card-label">最快用时</div>
            <div class="card-value">{{ stats.min_time ? `${stats.min_time}秒` : "-" }}</div>
          </div>
          <div class="stat-card">
            <div class="card-label">最慢用时</div>
            <div class="card-value">{{ stats.max_time ? `${stats.max_time}秒` : "-" }}</div>
          </div>
        </div>

        <div class="tendency-block">
          <h3>用户倾向</h3>
          <p class="tendency-text">{{ stats.tendency }}</p>
        </div>

        <div
          v-if="stats.periods.length > 0 || stats.pair_types.length > 0"
          class="chart-stack"
          :class="`is-${activeChart}`"
        >
          <button
            v-if="stats.periods.length > 0"
            class="chart-block stacked-chart period-chart"
            :class="{ active: activeChart === 'periods' }"
            type="button"
            @click="activeChart = 'periods'"
          >
            <h3>题目时期分布</h3>
            <div class="bar-chart">
              <div v-for="p in stats.periods" :key="p.keyword" class="bar-row">
                <span class="bar-label">{{ p.keyword }}</span>
                <div class="bar-track">
                  <div class="bar-fill" :style="{ width: barWidth(p.count, maxPeriodCount) }"></div>
                </div>
                <span class="bar-value">{{ p.count }}次 均分{{ p.avg_score.toFixed(1) }}</span>
              </div>
            </div>
          </button>

          <button
            v-if="stats.pair_types.length > 0"
            class="chart-block stacked-chart type-chart"
            :class="{ active: activeChart === 'types' }"
            type="button"
            @click="activeChart = 'types'"
          >
            <h3>题型正确率</h3>
            <div class="bar-chart">
              <div v-for="pt in stats.pair_types" :key="pt.pair_type" class="bar-row">
                <span class="bar-label">{{ pt.pair_type }}</span>
                <div class="bar-track">
                  <div class="bar-fill correct-fill" :style="{ width: `${Math.round(pt.correct_rate * 100)}%` }"></div>
                </div>
                <span class="bar-value">{{ Math.round(pt.correct_rate * 100) }}% {{ pt.correct }}/{{ pt.total }}</span>
              </div>
            </div>
          </button>
        </div>
      </div>
    </section>

    <section class="history-section">
      <h2>游戏历史</h2>

      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="history.length === 0" class="empty">暂无游戏记录</div>

      <div v-else class="history-list">
        <div v-for="item in history" :key="item.id" class="history-item" @click="viewDetail(item)">
          <div class="item-main">
            <span class="keyword">{{ item.keyword }}</span>
            <span class="date">{{ formatDate(item.created_at) }}</span>
          </div>
          <div class="item-stats">
            <span class="score">{{ item.score ?? 0 }}/{{ item.total }}</span>
            <span>{{ formatTime(item.time_used) }}</span>
            <span>{{ accuracy(item) }}</span>
          </div>
        </div>
      </div>

      <div v-if="totalPages > 1" class="pagination">
        <button :disabled="page === 1" type="button" @click="prevPage">
          <ChevronLeft :size="20" />
        </button>
        <span>{{ page }} / {{ totalPages }}</span>
        <button :disabled="page === totalPages" type="button" @click="nextPage">
          <ChevronRight :size="20" />
        </button>
      </div>
    </section>
  </main>
</template>

<style scoped>
.profile-page {
  min-height: 100vh;
  background:
    radial-gradient(ellipse at 30% 20%, rgba(255, 255, 255, 0.4) 0%, transparent 50%),
    radial-gradient(ellipse at 70% 80%, rgba(255, 255, 255, 0.3) 0%, transparent 50%),
    linear-gradient(135deg, #e8dcc8 0%, #d4c5a9 50%, #c9b896 100%);
  padding: 0 16px;
}

.topbar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

.icon-btn {
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  background: rgba(255, 255, 255, 0.55);
  border: 1px solid rgba(255, 255, 255, 0.7);
  border-radius: 8px;
  color: #1a1a1a;
  cursor: pointer;
}

.topbar > div {
  flex: 1;
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

.logout-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: white;
  border: 1px solid #d4c9b0;
  border-radius: 8px;
  font-size: 14px;
  color: #6b7280;
  cursor: pointer;
}

.logout-btn:hover {
  border-color: #ef4444;
  color: #ef4444;
}

.user-info,
.stats-section,
.history-section {
  max-width: 520px;
  margin-inline: auto;
}

.user-info {
  margin-top: 14px;
  margin-bottom: 12px;
  padding: 18px 18px;
  text-align: center;
  background: rgba(255, 255, 255, 0.62);
  backdrop-filter: blur(12px);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.68);
  box-shadow: 8px 8px 20px rgba(0, 0, 0, 0.1), -4px -4px 14px rgba(255, 255, 255, 0.9);
}

.email {
  font-size: 16px;
  font-weight: 700;
  color: #1a1a1a;
  margin-bottom: 12px;
}

.stats-summary {
  display: flex;
  justify-content: center;
  gap: 22px;
}

.stat-value {
  display: block;
  font-size: 26px;
  font-weight: 800;
  color: #246b55;
}

.stat-label,
.card-label {
  font-size: 12px;
  color: #6b7280;
}

.stats-section {
  position: relative;
  margin-bottom: 14px;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: 8px 8px 24px rgba(0, 0, 0, 0.12), -4px -4px 16px rgba(255, 255, 255, 0.8);
}

.section-toggle {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  background: rgba(255, 255, 255, 0.28);
  border: 0;
  font-size: 15px;
  font-weight: 700;
  color: #1a1a1a;
  cursor: pointer;
}

.section-toggle span:last-child {
  font-size: 12px;
  font-weight: 500;
  color: #246b55;
}

.stats-content {
  padding: 0 12px 12px;
}

.stats-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 10px;
}

.stat-card,
.tendency-block,
.chart-block,
.history-item,
.pagination {
  background: rgba(255, 255, 255, 0.68);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.62);
  box-shadow: 5px 5px 14px rgba(0, 0, 0, 0.09), -3px -3px 10px rgba(255, 255, 255, 0.82);
}

.stat-card {
  padding: 10px 8px;
  text-align: center;
}

.card-value {
  margin-top: 3px;
  font-size: 16px;
  font-weight: 800;
  color: #1a1a1a;
}

.tendency-block {
  margin-bottom: 10px;
  padding: 12px;
  background: rgba(240, 249, 246, 0.72);
}

.tendency-block h3,
.chart-block h3 {
  font-size: 14px;
  font-weight: 800;
  color: #1a1a1a;
  margin: 0 0 8px;
  text-align: left;
}

.tendency-text {
  font-size: 12px;
  color: #4b5563;
  line-height: 1.4;
  border-left: 3px solid #246b55;
  margin: 0;
  padding-left: 8px;
}

.chart-stack {
  position: relative;
  min-height: 180px;
}

.stacked-chart {
  position: absolute;
  inset-inline: 0;
  width: 100%;
  min-height: 156px;
  padding: 12px;
  text-align: initial;
  cursor: pointer;
  transition: transform 0.25s ease, opacity 0.25s ease, filter 0.25s ease;
}

.stacked-chart.active {
  z-index: 2;
  opacity: 1;
  filter: none;
  pointer-events: auto;
}

.chart-stack.is-periods .period-chart,
.chart-stack.is-types .type-chart {
  transform: translateY(0) scale(1);
}

.chart-stack.is-periods .type-chart,
.chart-stack.is-types .period-chart {
  z-index: 1;
  transform: translateY(34px) scale(0.95);
  opacity: 0.32;
  filter: grayscale(1) blur(0.6px);
}

.bar-chart {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.bar-row {
  display: grid;
  grid-template-columns: 74px 1fr 82px;
  align-items: center;
  gap: 6px;
}

.bar-label {
  min-width: 0;
  font-size: 11px;
  color: #4b5563;
  text-align: right;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bar-track {
  height: 12px;
  background: rgba(243, 244, 246, 0.85);
  border-radius: 4px;
  overflow: hidden;
  box-shadow: inset 2px 2px 4px rgba(0, 0, 0, 0.06);
}

.bar-fill {
  height: 100%;
  background: linear-gradient(135deg, #246b55 0%, #35c494 100%);
  border-radius: 4px;
  transition: width 0.6s ease;
}

.bar-fill.correct-fill {
  background: linear-gradient(135deg, #2f7f95 0%, #68d7ed 100%);
}

.bar-value {
  min-width: 0;
  font-size: 10px;
  color: #6b7280;
  white-space: nowrap;
}

.history-section {
  padding-bottom: 22px;
}

.history-section h2 {
  font-size: 16px;
  font-weight: 800;
  color: #1a1a1a;
  margin: 0 0 10px;
}

.loading,
.empty {
  text-align: center;
  padding: 40px;
  color: #6b7280;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.history-item {
  padding: 12px 12px;
  cursor: pointer;
  transition: transform 0.2s ease, background 0.2s ease;
}

.history-item:hover {
  transform: translateY(-2px);
  background: rgba(255, 255, 255, 0.86);
}

.item-main {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: center;
  margin-bottom: 6px;
}

.keyword {
  min-width: 0;
  font-size: 15px;
  font-weight: 800;
  color: #1a1a1a;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.date {
  flex-shrink: 0;
  font-size: 11px;
  color: #7b8190;
}

.item-stats {
  display: flex;
  gap: 10px;
  font-size: 12px;
  color: #6b7280;
}

.score {
  color: #246b55;
  font-weight: 800;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  margin-top: 10px;
  padding: 8px;
}

.pagination button {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid rgba(212, 201, 176, 0.5);
  border-radius: 8px;
  cursor: pointer;
}

.pagination button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

@media (max-width: 560px) {
  .stats-summary {
    gap: 14px;
  }

  .bar-row {
    grid-template-columns: 64px 1fr;
  }

  .bar-value {
    grid-column: 2;
  }

  .item-main {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
