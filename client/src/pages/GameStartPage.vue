<script setup lang="ts">
import { ref, onMounted } from "vue";
import { Sparkles, ChevronDown, ChevronUp } from "lucide-vue-next";
import { useRouter, useRoute } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { useGameStore } from "../stores/game";
import { trackEvent, getRecentKeywords } from "../api";
import LoginRegisterModal from "../components/LoginRegisterModal.vue";

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();
const gameStore = useGameStore();

const keyword = ref((route.query.keyword as string) || "");
const recentKeywords = ref<string[]>([]);
const topicsLoading = ref(true);

const RANK_LABELS = ["壹", "贰", "叁", "肆", "伍"];

onMounted(() => {
  const qk = route.query.keyword as string | undefined;
  if (qk) {
    keyword.value = qk;
  }
  loadRecentKeywords();
});

async function loadRecentKeywords() {
  topicsLoading.value = true;
  try {
    const resp = await getRecentKeywords();
    recentKeywords.value = resp.keywords;
  } catch {
    recentKeywords.value = ["三国", "唐朝", "秦始皇", "法国大革命", "工业革命"];
  } finally {
    topicsLoading.value = false;
  }
}

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

  const trimmedKeyword = keyword.value.trim();
  if (!trimmedKeyword) {
    error.value = "请输入历史人物或事件关键词";
    return;
  }

  loading.value = true;
  error.value = "";

  try {
    await trackEvent("action_submit_keyword", undefined, { keyword: trimmedKeyword });
    const game = await gameStore.createGame(trimmedKeyword);
    await trackEvent("game_session_start", game.gameId, {
      question_set_id: game.gameId,
      topic_keyword: game.keyword,
    });
    router.push(`/play/${game.gameId}`);
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    error.value = msg || "生成失败，请稍后重试";
  } finally {
    loading.value = false;
  }
}

function selectTopic(topic: string) {
  keyword.value = topic;
}
</script>

<template>
  <main class="start-page">
    <header class="topbar">
      <div>
        <p class="eyebrow">History Matching</p>
        <h1>历史配对</h1>
      </div>
      <div class="topbar-right">
        <button class="nav-link" @click="router.push('/leaderboard')">排行榜</button>
        <button v-if="authStore.isLoggedIn" class="user-badge" @click="router.push('/profile')">
          {{ authStore.user?.email }}
        </button>
        <button v-else class="login-btn" @click="showLoginModal = true">登录</button>
      </div>
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

      <div class="history-scroll">
        <div class="scroll-ornament top-ornament"></div>
        <div class="scroll-header">
          <span class="scroll-deco-left">&#9670;</span>
          <h2 class="scroll-title">以史为鉴</h2>
          <span class="scroll-deco-right">&#9670;</span>
        </div>
        <p class="scroll-subtitle">
          {{ authStore.isLoggedIn ? "您的最近探索" : "探索历史长河" }}
        </p>
        <div v-if="topicsLoading" class="topics-skeleton">
          <div v-for="i in 5" :key="i" class="skeleton-item"></div>
        </div>
        <div v-else class="topic-list">
          <button
            v-for="(topic, i) in recentKeywords"
            :key="topic"
            class="topic-item"
            @click="selectTopic(topic)"
          >
            <span class="topic-rank">{{ RANK_LABELS[i] }}</span>
            <span class="topic-text">{{ topic }}</span>
          </button>
        </div>
        <div class="scroll-ornament bottom-ornament"></div>
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

.topbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.nav-link {
  background: none;
  border: none;
  color: #246b55;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 8px;
  transition: background 0.2s;
}

.nav-link:hover {
  background: rgba(36, 107, 85, 0.08);
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

/* 历史卷轴风格话题区块 */
.history-scroll {
  margin-top: 32px;
  background: linear-gradient(180deg, #faf6ee 0%, #f0e8d6 100%);
  border: 2px solid #c9b98a;
  border-radius: 12px;
  padding: 0;
  position: relative;
  box-shadow: 0 4px 20px rgba(139, 109, 56, 0.12);
}

.scroll-ornament {
  height: 6px;
  background: repeating-linear-gradient(
    90deg,
    #c9b98a 0px,
    #c9b98a 8px,
    transparent 8px,
    transparent 16px
  );
  border-radius: 0;
}

.top-ornament {
  border-radius: 10px 10px 0 0;
}

.bottom-ornament {
  border-radius: 0 0 10px 10px;
}

.scroll-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 20px 24px 4px;
}

.scroll-deco-left,
.scroll-deco-right {
  color: #c9b98a;
  font-size: 10px;
}

.scroll-title {
  font-size: 20px;
  font-weight: 800;
  color: #5c4a2a;
  margin: 0;
  letter-spacing: 6px;
  font-family: "STKaiti", "KaiTi", "SimSun", serif;
}

.scroll-subtitle {
  font-size: 13px;
  color: #8b7355;
  text-align: center;
  margin: 4px 0 16px;
  letter-spacing: 2px;
}

.topics-skeleton {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 0 24px 20px;
}

.skeleton-item {
  height: 44px;
  background: linear-gradient(90deg, #e8dcc8 25%, #f0e8d6 50%, #e8dcc8 75%);
  background-size: 200% 100%;
  animation: shimmer 1.4s ease-in-out infinite;
  border-radius: 8px;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.topic-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 0 24px 20px;
}

.topic-item {
  display: flex;
  align-items: center;
  gap: 14px;
  width: 100%;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid #d4c9b0;
  border-radius: 8px;
  font-size: 15px;
  color: #3d3019;
  cursor: pointer;
  transition: all 0.25s ease;
  text-align: left;
}

.topic-item:hover {
  background: rgba(255, 255, 255, 0.95);
  border-color: #246b55;
  transform: translateX(4px);
  box-shadow: 0 2px 12px rgba(36, 107, 85, 0.12);
}

.topic-rank {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: #246b55;
  color: #fff;
  border-radius: 50%;
  font-size: 13px;
  font-weight: 700;
  font-family: "STKaiti", "KaiTi", serif;
  flex-shrink: 0;
}

.topic-text {
  font-weight: 600;
  letter-spacing: 1px;
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
