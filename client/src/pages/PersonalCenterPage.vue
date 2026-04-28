<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { LogOut, ChevronLeft, ChevronRight } from "lucide-vue-next";
import { useAuthStore } from "../stores/auth";
import { getHistory, type HistoryItem } from "../api";

const router = useRouter();
const authStore = useAuthStore();

const history = ref<HistoryItem[]>([]);
const total = ref(0);
const page = ref(1);
const pageSize = 10;
const loading = ref(false);

const totalPages = computed(() => Math.ceil(total.value / pageSize));

import { computed } from "vue";

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
});
</script>

<template>
  <main class="profile-page">
    <header class="topbar">
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
          <span class="stat-value">{{ total }}</span>
          <span class="stat-label">总场次</span>
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
  max-width: 600px;
  margin: 30px auto;
  background: white;
  border-radius: 16px;
  padding: 24px;
  text-align: center;
}

.email {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 20px;
}

.stats-summary {
  display: flex;
  justify-content: center;
  gap: 40px;
}

.stat {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 32px;
  font-weight: 800;
  color: #246b55;
}

.stat-label {
  font-size: 14px;
  color: #6b7280;
}

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
  gap: 12px;
}

.history-item {
  background: white;
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: box-shadow 0.2s;
}

.history-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.item-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.keyword {
  font-weight: 700;
  color: #1a1a1a;
}

.date {
  font-size: 12px;
  color: #9ca3af;
}

.item-stats {
  display: flex;
  gap: 16px;
  font-size: 14px;
  color: #6b7280;
}

.score {
  color: #246b55;
  font-weight: 600;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 20px;
}

.pagination button {
  padding: 8px;
  background: white;
  border: 1px solid #d4c9b0;
  border-radius: 8px;
  cursor: pointer;
}

.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
