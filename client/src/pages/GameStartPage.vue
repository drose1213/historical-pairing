<script setup lang="ts">
import { ref } from "vue";
import { Sparkles, ChevronDown, ChevronUp } from "lucide-vue-next";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { useGameStore } from "../stores/game";
import { trackEvent } from "../api";
import LoginRegisterModal from "../components/LoginRegisterModal.vue";

const router = useRouter();
const authStore = useAuthStore();
const gameStore = useGameStore();

const keyword = ref("");
const loading = ref(false);
const error = ref("");
const showRules = ref(false);
const showLoginModal = ref(false);

const rules = [
  "游戏开始后，系统会展示4张人物卡片和4张事件卡片",
  "您需要通过点击或拖拽将左侧人物与右侧事件进行配对",
  "每组配对只能使用一次，所有配对完成后可提交答案",
  "游戏限时30秒，倒计时结束后自动提交",
  "正确匹配得分，错误匹配不得分",
];

async function startGame() {
  if (!authStore.isLoggedIn) {
    showLoginModal.value = true;
    return;
  }

  loading.value = true;
  error.value = "";

  try {
    await trackEvent("action_submit_keyword", undefined, { keyword: keyword.value || "random" });
    const game = await gameStore.createGame(keyword.value);
    await trackEvent("game_session_start", game.gameId, {
      question_set_id: game.gameId,
      topic_keyword: game.keyword,
    });
    router.push(`/play/${game.gameId}`);
  } catch (err) {
    error.value = err instanceof Error ? err.message : "生成失败";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <main class="start-page">
    <header class="topbar">
      <div>
        <p class="eyebrow">History Matching</p>
        <h1>历史配对</h1>
      </div>
      <button v-if="authStore.isLoggedIn" class="user-badge" @click="router.push('/profile')">
        {{ authStore.user?.email }}
      </button>
      <button v-else class="login-btn" @click="showLoginModal = true">登录</button>
    </header>

    <section class="hero">
      <div class="search-section">
        <input
          v-model="keyword"
          class="keyword-input"
          maxlength="100"
          placeholder="输入历史人物或事件关键词，如'秦始皇'、'工业革命'"
          @keydown.enter="startGame"
        />
        <button class="start-btn" :disabled="loading" @click="startGame">
          <Sparkles :size="18" />
          <span>{{ loading ? "生成中..." : "开始游戏" }}</span>
        </button>
      </div>
      <p v-if="error" class="error-line">{{ error }}</p>

      <div class="quick-topics">
        <span class="topics-label">快速开始：</span>
        <button @click="keyword = '三国'">三国</button>
        <button @click="keyword = '唐朝'">唐朝</button>
        <button @click="keyword = '秦始皇'">秦始皇</button>
        <button @click="keyword = '法国大革命'">法国大革命</button>
        <button @click="keyword = '工业革命'">工业革命</button>
      </div>
    </section>

    <section class="rules-section">
      <button class="rules-toggle" @click="showRules = !showRules">
        <span>游戏规则</span>
        <ChevronUp v-if="showRules" :size="20" />
        <ChevronDown v-else :size="20" />
      </button>
      <div v-if="showRules" class="rules-content">
        <ul>
          <li v-for="(rule, i) in rules" :key="i">{{ rule }}</li>
        </ul>
      </div>
    </section>

    <LoginRegisterModal v-if="showLoginModal" @close="showLoginModal = false" @success="startGame" />
  </main>
</template>

<style scoped>
.start-page {
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

.user-badge {
  background: #246b55;
  color: white;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  border: none;
  cursor: pointer;
}

.login-btn {
  background: #246b55;
  color: white;
  padding: 8px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  border: none;
  cursor: pointer;
}

.hero {
  max-width: 600px;
  margin: 60px auto;
  text-align: center;
}

.search-section {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.keyword-input {
  flex: 1;
  padding: 14px 18px;
  border: 2px solid #d4c9b0;
  border-radius: 12px;
  font-size: 16px;
  background: white;
  outline: none;
  transition: border-color 0.2s;
}

.keyword-input:focus {
  border-color: #246b55;
}

.start-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 24px;
  background: #246b55;
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.2s;
}

.start-btn:hover:not(:disabled) {
  background: #1d5243;
}

.start-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-line {
  color: #b42318;
  font-size: 14px;
  margin: 12px 0;
}

.quick-topics {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: center;
}

.quick-topics .topics-label {
  font-size: 14px;
  color: #6b7280;
}

.quick-topics button {
  padding: 6px 14px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid #d4c9b0;
  border-radius: 20px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.quick-topics button:hover {
  background: white;
  border-color: #246b55;
  color: #246b55;
}

.rules-section {
  max-width: 600px;
  margin: 0 auto;
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.rules-toggle {
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

.rules-content {
  padding: 0 20px 20px;
}

.rules-content ul {
  margin: 0;
  padding-left: 20px;
}

.rules-content li {
  font-size: 14px;
  color: #4b5563;
  line-height: 1.8;
}
</style>
