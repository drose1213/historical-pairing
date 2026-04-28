<script setup lang="ts">
import { ref, onMounted } from "vue";
import { Users, Gamepad2, Clock, TrendingUp, Save, ChevronLeft, ChevronRight } from "lucide-vue-next";
import { useAuthStore } from "../stores/auth";
import {
  getAdminStats,
  getAdminUsers,
  getAdminGames,
  getAdminConfigs,
  updateAdminConfig,
  type AdminStats,
  type UserListItem,
  type GameListItem,
  type ConfigItem,
} from "../api";

const authStore = useAuthStore();

const stats = ref<AdminStats | null>(null);
const users = ref<UserListItem[]>([]);
const games = ref<GameListItem[]>([]);
const configs = ref<ConfigItem[]>([]);
const userPage = ref(1);
const gamePage = ref(1);
const pageSize = 10;
const userTotal = ref(0);
const gameTotal = ref(0);
const loading = ref(false);
const saving = ref<Record<string, boolean>>({});

async function fetchStats() {
  try {
    stats.value = await getAdminStats();
  } catch (err) {
    console.error("Failed to fetch stats:", err);
  }
}

async function fetchUsers() {
  try {
    const response = await getAdminUsers(userPage.value, pageSize);
    users.value = response.items;
    userTotal.value = response.total;
  } catch (err) {
    console.error("Failed to fetch users:", err);
  }
}

async function fetchGames() {
  try {
    const response = await getAdminGames(gamePage.value, pageSize);
    games.value = response.items;
    gameTotal.value = response.total;
  } catch (err) {
    console.error("Failed to fetch games:", err);
  }
}

async function fetchConfigs() {
  try {
    configs.value = await getAdminConfigs();
  } catch (err) {
    console.error("Failed to fetch configs:", err);
  }
}

async function saveConfig(key: string, value: string) {
  saving.value = { ...saving.value, [key]: true };
  try {
    await updateAdminConfig(key, value);
    await fetchConfigs();
  } catch (err) {
    console.error("Failed to save config:", err);
  } finally {
    saving.value = { ...saving.value, [key]: false };
  }
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString("zh-CN");
}

function formatPercent(value: number) {
  return `${(value * 100).toFixed(1)}%`;
}

function userPrevPage() {
  if (userPage.value > 1) {
    userPage.value--;
    fetchUsers();
  }
}

function userNextPage() {
  if (userPage.value < Math.ceil(userTotal.value / pageSize)) {
    userPage.value++;
    fetchUsers();
  }
}

function gamePrevPage() {
  if (gamePage.value > 1) {
    gamePage.value--;
    fetchGames();
  }
}

function gameNextPage() {
  if (gamePage.value < Math.ceil(gameTotal.value / pageSize)) {
    gamePage.value++;
    fetchGames();
  }
}

onMounted(() => {
  fetchStats();
  fetchUsers();
  fetchGames();
  fetchConfigs();
});
</script>

<template>
  <main class="admin-page">
    <header class="topbar">
      <div>
        <p class="eyebrow">管理后台</p>
        <h1>数据看板</h1>
      </div>
    </header>

    <section class="stats-grid">
      <div class="stat-card">
        <Users :size="24" class="stat-icon" />
        <div class="stat-content">
          <span class="stat-value">{{ stats?.total_users ?? 0 }}</span>
          <span class="stat-label">总用户数</span>
        </div>
      </div>
      <div class="stat-card">
        <Users :size="24" class="stat-icon" />
        <div class="stat-content">
          <span class="stat-value">{{ stats?.active_users_7d ?? 0 }}</span>
          <span class="stat-label">活跃用户(7天)</span>
        </div>
      </div>
      <div class="stat-card">
        <Gamepad2 :size="24" class="stat-icon" />
        <div class="stat-content">
          <span class="stat-value">{{ stats?.total_games ?? 0 }}</span>
          <span class="stat-label">总游戏场次</span>
        </div>
      </div>
      <div class="stat-card">
        <TrendingUp :size="24" class="stat-icon" />
        <div class="stat-content">
          <span class="stat-value">{{ stats?.avg_correct_rate ? formatPercent(stats.avg_correct_rate) : "-" }}</span>
          <span class="stat-label">平均正确率</span>
        </div>
      </div>
      <div class="stat-card">
        <Clock :size="24" class="stat-icon" />
        <div class="stat-content">
          <span class="stat-value">{{ stats?.avg_time_used ? `${Math.round(stats.avg_time_used)}秒` : "-" }}</span>
          <span class="stat-label">平均用时</span>
        </div>
      </div>
    </section>

    <section class="section">
      <h2>用户列表</h2>
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>邮箱</th>
              <th>注册时间</th>
              <th>游戏次数</th>
              <th>最后游戏</th>
              <th>角色</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.id">
              <td>{{ user.email }}</td>
              <td>{{ formatDate(user.created_at) }}</td>
              <td>{{ user.total_games }}</td>
              <td>{{ user.last_game_at ? formatDate(user.last_game_at) : "-" }}</td>
              <td>{{ user.is_admin ? "管理员" : "用户" }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="pagination">
        <button :disabled="userPage === 1" @click="userPrevPage">
          <ChevronLeft :size="20" />
        </button>
        <span>{{ userPage }} / {{ Math.ceil(userTotal / pageSize) || 1 }}</span>
        <button :disabled="userPage >= Math.ceil(userTotal / pageSize)" @click="userNextPage">
          <ChevronRight :size="20" />
        </button>
      </div>
    </section>

    <section class="section">
      <h2>游戏记录</h2>
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>用户</th>
              <th>关键词</th>
              <th>得分</th>
              <th>用时</th>
              <th>时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="game in games" :key="game.id">
              <td>{{ game.user_email || "匿名" }}</td>
              <td>{{ game.keyword }}</td>
              <td>{{ game.score ?? 0 }}/{{ game.total }}</td>
              <td>{{ game.time_used ? `${game.time_used}秒` : "-" }}</td>
              <td>{{ formatDate(game.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="pagination">
        <button :disabled="gamePage === 1" @click="gamePrevPage">
          <ChevronLeft :size="20" />
        </button>
        <span>{{ gamePage }} / {{ Math.ceil(gameTotal / pageSize) || 1 }}</span>
        <button :disabled="gamePage >= Math.ceil(gameTotal / pageSize)" @click="gameNextPage">
          <ChevronRight :size="20" />
        </button>
      </div>
    </section>

    <section class="section">
      <h2>API 配置</h2>
      <div class="config-list">
        <div v-for="config in configs" :key="config.key" class="config-item">
          <label>{{ config.key }}</label>
          <div class="config-input-row">
            <input
              :type="config.key === 'openai_api_key' ? 'password' : 'text'"
              :value="config.key === 'openai_api_key' ? (config.configured ? '******' : '') : config.value"
              :placeholder="config.key === 'openai_api_key' ? '输入新的 API Key' : config.value"
              @change="(e) => saveConfig(config.key, (e.target as HTMLInputElement).value)"
            />
            <button :disabled="saving[config.key]" @click="(e) => {
              const input = (e.target as HTMLButtonElement).previousElementSibling as HTMLInputElement;
              saveConfig(config.key, input.value);
            }">
              <Save :size="16" />
              <span>{{ saving[config.key] ? "保存中..." : "保存" }}</span>
            </button>
          </div>
          <p v-if="config.key === 'openai_api_key' && config.configured" class="config-hint">
            已配置密钥，不显示原值
          </p>
        </div>
      </div>
    </section>
  </main>
</template>

<style scoped>
.admin-page {
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

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  max-width: 1000px;
  margin: 30px auto;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.stat-icon {
  color: #246b55;
}

.stat-content {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 24px;
  font-weight: 800;
  color: #1a1a1a;
}

.stat-label {
  font-size: 12px;
  color: #6b7280;
}

.section {
  max-width: 1000px;
  margin: 0 auto 40px;
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.section h2 {
  font-size: 18px;
  font-weight: 700;
  color: #1a1a1a;
  margin: 0 0 16px;
}

.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  text-align: left;
  padding: 12px;
  border-bottom: 1px solid #e5e7eb;
}

th {
  font-size: 12px;
  font-weight: 700;
  color: #6b7280;
  text-transform: uppercase;
}

td {
  font-size: 14px;
  color: #1a1a1a;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 16px;
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

.config-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.config-item label {
  display: block;
  font-size: 14px;
  font-weight: 700;
  color: #344054;
  margin-bottom: 6px;
}

.config-input-row {
  display: flex;
  gap: 8px;
}

.config-input-row input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid #d4c9b0;
  border-radius: 8px;
  font-size: 14px;
}

.config-input-row button {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  background: #246b55;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
}

.config-input-row button:disabled {
  opacity: 0.6;
}

.config-hint {
  font-size: 12px;
  color: #246b55;
  margin: 4px 0 0;
}
</style>
