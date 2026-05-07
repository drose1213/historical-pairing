<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { LogOut, ChevronLeft, ChevronRight, ArrowLeft } from "lucide-vue-next";
import { useAuthStore } from "../stores/auth";
import { getHistory, getUserStats, type HistoryItem, type UserStatsResponse } from "../api";

const router = useRouter();
const authStore = useAuthStore();

const history = ref<HistoryItem[]>([]);
const total = ref(0);
const page = ref(1);
const pageSize = 10;
const loading = ref(false);
const stats = ref<UserStatsResponse | null>(null);
const statsLoading = ref(false);
const showStats = ref(true);

const totalPages = computed(() => Math.ceil(total.value / pageSize));

function formatDate(dateStr: string) {
  const date = new Date(dateStr);
  return date.toLocaleDateString("zh-CN", {
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
  return `${Math.round((value / max) * 100)}%`;
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
    fetchHistory();
  }
}

function nextPage() {
  if (page.value < totalPages.value) {
    page.value++;
    fetchHistory();
  }
}

function viewDetail(item: HistoryItem) {
  router.push(`/results/${item.id}`);
}

function logout() {
  authStore.logout();
  router.push("/");
}

onMounted(() => {
  fetchHistory();
  fetchStats();
});
</script>

<template>
  <main class="profile-page">
    <header class="topbar">
      <button class="back-btn" @click="router.push('/')">
        <ArrowLeft :size="20" />
      </button>
      <div>
        <p class="eyebrow">个人中心</p>
        <h1>我的战绩</h1>
      </div>
      <button class="logout-btn" @click="logout">
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
        <div class="stat" v-if="stats && stats.total_games > 0">
          <span class="stat-value">{{ stats.avg_score.toFixed(1) }}</span>
          <span class="stat-label">平均分</span>
        </div>
        <div class="stat" v-if="stats && stats.total_games > 0">
          <span class="stat-value">{{ stats.max_score }}</span>
          <span class="stat-label">最高分</span>
        </div>
      </div>
    </section>

    <section v-if="stats && stats.total_games > 0" class="stats-section">
      <button class="section-toggle" @click="showStats = !showStats">
        <span>数据分析</span>
        <span>{{ showStats ? '收起' : '展开' }}</span>
      </button>

      <div v-if="showStats" class="stats-content">
        <!-- Score & Time Summary -->
        <div class="stats-cards">
          <div class="stat-card">
            <div class="card-label">分数区间</div>
            <div class="card-value">{{ stats.min_score }} - {{ stats.max_score }}</div>
          </div>
          <div class="stat-card">
            <div class="card-label">平均用时</div>
            <div class="card-value">{{ stats.avg_time ? `${stats.avg_time.toFixed(0)}秒` : '-' }}</div>
          </div>
          <div class="stat-card">
            <div class="card-label">最快用时</div>
            <div class="card-value">{{ stats.min_time ? `${stats.min_time}秒` : '-' }}</div>
          </div>
          <div class="stat-card">
            <div class="card-label">最慢用时</div>
            <div class="card-value">{{ stats.max_time ? `${stats.max_time}秒` : '-' }}</div>
          </div>
        </div>

        <!-- Period Distribution -->
        <div v-if="stats.periods.length > 0" class="chart-block">
          <h3>题目时期分布</h3>
          <div class="bar-chart">
            <div v-for="p in stats.periods" :key="p.keyword" class="bar-row">
              <span class="bar-label">{{ p.keyword }}</span>
              <div class="bar-track">
                <div
                  class="bar-fill"
                  :style="{ width: barWidth(p.count, Math.max(...stats.periods.map(x => x.count))) }"
                ></div>
              </div>
              <span class="bar-value">{{ p.count }}次 (均分{{ p.avg_score.toFixed(1) }})</span>
            </div>
          </div>
        </div>

        <!-- Pair Type Performance -->
        <div v-if="stats.pair_types.length > 0" class="chart-block">
          <h3>题型正确率</h3>
          <div class="bar-chart">
            <div v-for="pt in stats.pair_types" :key="pt.pair_type" class="bar-row">
              <span class="bar-label">{{ pt.pair_type }}</span>
              <div class="bar-track">
                <div
                  class="bar-fill correct-fill"
                  :style="{ width: `${Math.round(pt.correct_rate * 100)}%` }"
                ></div>
              </div>
              <span class="bar-value">{{ Math.round(pt.correct_rate * 100) }}% ({{ pt.correct }}/{{ pt.total }})</span>
            </div>
          </div>
        </div>

        <!-- Tendency -->
        <div class="tendency-block">
          <h3>用户倾向</h3>
          <p class="tendency-text">{{ stats.tendency }}</p>
        </div>
      </div>
    </section>

    <section class="history-section">
      <h2>游戏历史</h2>

      <div v-if="loading" class="loading">加载中...</div>

      <div v-else-if="history.length === 0" class="empty">
        暂无游戏记录
      </div>

      <div v-else class="history-list">
        <div
          v-for="item in history"
          :key="item.id"
          class="history-item"
          @click="viewDetail(item)"
        >
          <div class="item-main">
            <span class="keyword">{{ item.keyword }}</span>
            <span class="date">{{ formatDate(item.created_at) }}</span>
          </div>
          <div class="item-stats">
            <span class="score">{{ item.score ?? 0 }}/{{ item.total }}</span>
            <span class="time">{{ formatTime(item.time_used) }}</span>
            <span class="accuracy">{{ accuracy(item) }}</span>
          </div>
        </div>
      </div>

      <div v-if="totalPages > 1" class="pagination">
        <button :disabled="page === 1" @click="prevPage">
          <ChevronLeft :size="20" />
        </button>
        <span>{{ page }} / {{ totalPages }}</span>
        <button :disabled="page === totalPages" @click="nextPage">
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

.back-btn {
  padding: 8px;
  background: none;
  border: none;
  cursor: pointer;
  color: #1a1a1a;
}

.topbar > div {
  flex: 1;
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

.user-info {
  position: relative;
  max-width: 600px;
  margin: 30px auto;
  padding: 28px 24px;
  text-align: center;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(12px);
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow:
    8px 8px 20px rgba(0, 0, 0, 0.1),
    -4px -4px 14px rgba(255, 255, 255, 0.9),
    inset 0 0 40px rgba(255, 255, 255, 0.4);
}

.email {
  position: relative;
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 22px;
  text-shadow: 0 1px 3px rgba(255, 255, 255, 0.8);
}

.stats-summary {
  position: relative;
  display: flex;
  justify-content: center;
  gap: 40px;
}

.stat {
  position: relative;
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 34px;
  font-weight: 800;
  color: #246b55;
  text-shadow: 0 2px 4px rgba(36, 107, 85, 0.2);
}

.stat-label {
  font-size: 14px;
  color: #6b7280;
}

/* Stats Section */
.stats-section {
  max-width: 600px;
  margin: 0 auto 30px;
  position: relative;
}

.stats-section::before {
  content: '';
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 20px;
  backdrop-filter: blur(8px);
  box-shadow:
    8px 8px 24px rgba(0, 0, 0, 0.12),
    -4px -4px 16px rgba(255, 255, 255, 0.8),
    inset 0 0 60px rgba(255, 255, 255, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.5);
}

.section-toggle {
  position: relative;
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: none;
  border: none;
  font-size: 16px;
  font-weight: 700;
  color: #1a1a1a;
  cursor: pointer;
}

.section-toggle span:last-child {
  font-size: 13px;
  font-weight: 500;
  color: #246b55;
}

.stats-content {
  position: relative;
  padding: 0 20px 20px;
}

.stats-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  position: relative;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(12px);
  border-radius: 14px;
  padding: 18px 14px;
  text-align: center;
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow:
    4px 4px 12px rgba(0, 0, 0, 0.08),
    -2px -2px 8px rgba(255, 255, 255, 0.9),
    inset 0 0 20px rgba(255, 255, 255, 0.4);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.stat-card:nth-child(1) { transform: rotate(-1.5deg) translateY(2px); }
.stat-card:nth-child(2) { transform: rotate(1.5deg) translateY(-2px); }
.stat-card:nth-child(3) { transform: rotate(1deg) translateY(3px); }
.stat-card:nth-child(4) { transform: rotate(-1deg) translateY(-1px); }

.stat-card:hover {
  transform: rotate(0deg) translateY(0) scale(1.02);
  box-shadow:
    6px 6px 20px rgba(0, 0, 0, 0.15),
    -3px -3px 12px rgba(255, 255, 255, 0.95),
    inset 0 0 30px rgba(255, 255, 255, 0.5);
}

.card-label {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 6px;
}

.card-value {
  font-size: 22px;
  font-weight: 800;
  color: #1a1a1a;
  text-shadow: 0 1px 2px rgba(255, 255, 255, 0.8);
}

.chart-block {
  position: relative;
  margin-bottom: 24px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow:
    6px 6px 16px rgba(0, 0, 0, 0.08),
    -3px -3px 10px rgba(255, 255, 255, 0.9),
    inset 0 0 30px rgba(255, 255, 255, 0.3);
}

.chart-block h3 {
  font-size: 15px;
  font-weight: 700;
  color: #1a1a1a;
  margin: 0 0 14px;
}

.bar-chart {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.bar-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.bar-label {
  width: 80px;
  font-size: 13px;
  color: #4b5563;
  text-align: right;
  flex-shrink: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bar-track {
  flex: 1;
  height: 20px;
  background: rgba(243, 244, 246, 0.8);
  border-radius: 4px;
  overflow: hidden;
  box-shadow: inset 2px 2px 4px rgba(0, 0, 0, 0.06);
}

.bar-fill {
  height: 100%;
  background: linear-gradient(135deg, #246b55 0%, #2d8f72 100%);
  border-radius: 4px;
  transition: width 0.6s ease;
  min-width: 2px;
  box-shadow: 2px 2px 6px rgba(36, 107, 85, 0.3);
}

.bar-fill.correct-fill {
  background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%);
  box-shadow: 2px 2px 6px rgba(59, 130, 246, 0.3);
}

.bar-value {
  width: 120px;
  font-size: 12px;
  color: #6b7280;
  flex-shrink: 0;
}

.tendency-block {
  position: relative;
  margin-bottom: 8px;
  padding: 20px;
  background: rgba(240, 249, 246, 0.6);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow:
    6px 6px 16px rgba(0, 0, 0, 0.08),
    -3px -3px 10px rgba(255, 255, 255, 0.9),
    inset 0 0 30px rgba(255, 255, 255, 0.3);
}

.tendency-block h3 {
  font-size: 15px;
  font-weight: 700;
  color: #1a1a1a;
  margin: 0 0 10px;
}

.tendency-text {
  font-size: 14px;
  color: #4b5563;
  line-height: 1.6;
  background: rgba(255, 255, 255, 0.5);
  padding: 14px 18px;
  border-radius: 12px;
  border-left: 4px solid #246b55;
  margin: 0;
  box-shadow: inset 2px 2px 6px rgba(0, 0, 0, 0.04);
}

/* History Section */
.history-section {
  max-width: 600px;
  margin: 0 auto;
  padding-bottom: 40px;
}

.history-section h2 {
  font-size: 18px;
  font-weight: 700;
  color: #1a1a1a;
  margin: 0 0 16px;
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
  gap: 16px;
  position: relative;
}

.history-item {
  position: relative;
  background: rgba(255, 255, 255, 0.65);
  backdrop-filter: blur(10px);
  border-radius: 14px;
  padding: 18px 16px;
  cursor: pointer;
  border: 1px solid rgba(255, 255, 255, 0.5);
  box-shadow:
    5px 5px 14px rgba(0, 0, 0, 0.1),
    -3px -3px 10px rgba(255, 255, 255, 0.8),
    inset 0 0 25px rgba(255, 255, 255, 0.4);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.history-item:nth-child(odd) {
  transform: rotate(-0.8deg) translateX(3px);
}

.history-item:nth-child(even) {
  transform: rotate(0.8deg) translateX(-3px);
}

.history-item:hover {
  transform: rotate(0deg) translateX(0) scale(1.02);
  box-shadow:
    8px 8px 20px rgba(0, 0, 0, 0.14),
    -4px -4px 14px rgba(255, 255, 255, 0.95),
    inset 0 0 35px rgba(255, 255, 255, 0.5);
  background: rgba(255, 255, 255, 0.85);
}

.item-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.keyword {
  font-weight: 700;
  color: #1a1a1a;
  text-shadow: 0 1px 2px rgba(255, 255, 255, 0.8);
}

.date {
  font-size: 12px;
  color: #9ca3af;
}

.item-stats {
  display: flex;
  gap: 18px;
  font-size: 14px;
  color: #6b7280;
}

.score {
  color: #246b55;
  font-weight: 700;
  text-shadow: 0 1px 2px rgba(36, 107, 85, 0.15);
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 24px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.5);
}

.pagination button {
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(212, 201, 176, 0.5);
  border-radius: 8px;
  cursor: pointer;
  box-shadow: 3px 3px 8px rgba(0, 0, 0, 0.08);
  transition: all 0.2s ease;
}

.pagination button:hover:not(:disabled) {
  background: white;
  box-shadow: 4px 4px 12px rgba(0, 0, 0, 0.12);
  transform: translateY(-1px);
}

.pagination button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  transform: none;
}
</style>
