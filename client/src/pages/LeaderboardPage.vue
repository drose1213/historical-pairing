<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { Trophy, ArrowLeft, ChevronUp, ChevronDown } from "lucide-vue-next";
import { getLeaderboard, type LeaderboardItem, type LeaderboardResponse } from "../api";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const authStore = useAuthStore();

const items = ref<LeaderboardItem[]>([]);
const total = ref(0);
const page = ref(1);
const pageSize = 10;
const loading = ref(false);

const sortBy = ref<"avg_score" | "total_games" | "best_score" | "total_correct">("avg_score");
const sortOrder = ref<"asc" | "desc">("desc");

const medalColors: Record<number, string> = { 1: "#FFD700", 2: "#C0C0C0", 3: "#CD7F32" };

const columns = [
  { key: "avg_score", label: "均分" },
  { key: "total_games", label: "对局" },
  { key: "best_score", label: "最高" },
  { key: "total_correct", label: "总正确" },
] as const;

async function load() {
  loading.value = true;
  try {
    const data: LeaderboardResponse = await getLeaderboard(page.value, pageSize, sortBy.value, sortOrder.value);
    items.value = data.items;
    total.value = data.total;
  } catch {
    items.value = [];
  } finally {
    loading.value = false;
  }
}

function setSort(key: typeof sortBy.value) {
  if (sortBy.value === key) {
    sortOrder.value = sortOrder.value === "desc" ? "asc" : "desc";
  } else {
    sortBy.value = key;
    sortOrder.value = "desc";
  }
  page.value = 1;
  load();
}

function prevPage() {
  if (page.value > 1) {
    page.value--;
    load();
  }
}

function nextPage() {
  if (page.value * pageSize < total.value) {
    page.value++;
    load();
  }
}

onMounted(load);
</script>

<template>
  <main class="leaderboard-page">
    <header class="topbar">
      <button class="back-btn" @click="router.push('/')">
        <ArrowLeft :size="20" />
      </button>
      <div>
        <p class="eyebrow">Leaderboard</p>
        <h1>排行榜</h1>
      </div>
      <div style="width: 40px"></div>
    </header>

    <section class="leaderboard-table">
      <div v-if="loading" class="loading">加载中...</div>

      <template v-else>
        <div class="table-header">
          <span class="col-rank">排名</span>
          <span class="col-email">用户</span>
          <span v-for="col in columns" :key="col.key" class="col-stat sortable" @click="setSort(col.key)">
            {{ col.label }}
            <span class="sort-icon">
              <ChevronUp
                v-if="sortBy === col.key && sortOrder === 'asc'"
                :size="14"
                class="sort-active"
              />
              <ChevronDown
                v-else-if="sortBy === col.key && sortOrder === 'desc'"
                :size="14"
                class="sort-active"
              />
              <ChevronUp v-else :size="14" class="sort-inactive" />
            </span>
          </span>
        </div>

        <div
          v-for="item in items"
          :key="item.rank"
          class="table-row"
          :class="{ 'is-me': authStore.user?.email && item.email.includes(authStore.user.email.slice(0, 2)) }"
        >
          <span class="col-rank">
            <span v-if="item.rank <= 3" class="medal" :style="{ color: medalColors[item.rank] }">
              <Trophy :size="18" />
            </span>
            <span v-else>{{ item.rank }}</span>
          </span>
          <span class="col-email">{{ item.email }}</span>
          <span class="col-stat">{{ item.total_games }}</span>
          <span class="col-stat">{{ item.avg_score.toFixed(1) }}</span>
          <span class="col-stat">{{ item.best_score }}</span>
          <span class="col-stat">{{ item.total_correct }}</span>
        </div>

        <div v-if="items.length === 0" class="empty">暂无数据</div>

        <div v-if="total > pageSize" class="pagination">
          <button :disabled="page <= 1" @click="prevPage">上一页</button>
          <span>{{ page }} / {{ Math.ceil(total / pageSize) }}</span>
          <button :disabled="page * pageSize >= total" @click="nextPage">下一页</button>
        </div>
      </template>
    </section>
  </main>
</template>

<style scoped>
.leaderboard-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f0e6 0%, #e8dcc8 100%);
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

.leaderboard-table {
  max-width: 700px;
  margin: 32px auto;
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.loading {
  padding: 40px;
  text-align: center;
  color: #6b7280;
}

.table-header {
  display: flex;
  padding: 14px 20px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
  font-size: 13px;
  font-weight: 600;
  color: #6b7280;
}

.col-stat.sortable {
  cursor: pointer;
  user-select: none;
  display: flex;
  align-items: center;
  gap: 2px;
}

.col-stat.sortable:hover {
  color: #246b55;
}

.sort-icon {
  display: inline-flex;
  align-items: center;
}

.sort-active {
  color: #246b55;
}

.sort-inactive {
  color: #d1d5db;
}

.table-row {
  display: flex;
  padding: 14px 20px;
  border-bottom: 1px solid #f3f4f6;
  align-items: center;
  font-size: 15px;
  transition: background 0.15s;
}

.table-row:hover {
  background: #f9fafb;
}

.table-row.is-me {
  background: #f0f9f6;
  font-weight: 600;
}

.col-rank {
  width: 60px;
  text-align: center;
  flex-shrink: 0;
}

.col-email {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.col-stat {
  width: 70px;
  text-align: center;
  flex-shrink: 0;
  color: #4b5563;
}

.medal {
  display: inline-flex;
}

.empty {
  padding: 40px;
  text-align: center;
  color: #9ca3af;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  padding: 16px;
  border-top: 1px solid #e5e7eb;
}

.pagination button {
  padding: 8px 16px;
  background: #f3f4f6;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
}

.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pagination span {
  font-size: 14px;
  color: #6b7280;
}
</style>
