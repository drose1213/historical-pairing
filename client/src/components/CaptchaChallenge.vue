<script setup lang="ts">
import { ref, onMounted } from "vue";
import { RefreshCw } from "lucide-vue-next";
import { getCaptcha, type CaptchaData } from "../api";

const emit = defineEmits<{
  verified: [token: string, answer: string];
}>();

const captcha = ref<CaptchaData | null>(null);
const userAnswer = ref("");
const error = ref("");
const loading = ref(false);

async function loadCaptcha() {
  loading.value = true;
  error.value = "";
  userAnswer.value = "";
  try {
    captcha.value = await getCaptcha();
  } catch {
    error.value = "获取验证题失败，请重试";
  } finally {
    loading.value = false;
  }
}

function confirm() {
  if (!captcha.value || !userAnswer.value.trim()) {
    error.value = "请输入答案";
    return;
  }
  error.value = "";
  emit("verified", captcha.value.token, userAnswer.value.trim());
}

function refresh() {
  loadCaptcha();
}

onMounted(loadCaptcha);
</script>

<template>
  <div class="captcha-box">
    <div class="captcha-row">
      <span class="captcha-question" v-if="captcha">{{ captcha.question }}</span>
      <span class="captcha-question loading" v-else>加载中...</span>
      <button type="button" class="refresh-btn" :disabled="loading" @click="refresh" title="换一题">
        <RefreshCw :size="16" />
      </button>
    </div>
    <div class="captcha-input-row">
      <input
        v-model="userAnswer"
        type="text"
        placeholder="输入计算结果"
        class="captcha-input"
        @keyup.enter="confirm"
      />
      <button type="button" class="captcha-confirm-btn" :disabled="loading" @click="confirm">
        确认
      </button>
    </div>
    <p v-if="error" class="captcha-error">{{ error }}</p>
  </div>
</template>

<style scoped>
.captcha-box {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 12px;
  margin-bottom: 12px;
}

.captcha-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.captcha-question {
  font-size: 18px;
  font-weight: 700;
  color: #1a1a1a;
  letter-spacing: 2px;
  font-family: "Courier New", monospace;
}

.captcha-question.loading {
  font-size: 14px;
  font-weight: 400;
  color: #9ca3af;
}

.refresh-btn {
  padding: 6px;
  background: none;
  border: none;
  cursor: pointer;
  color: #6b7280;
  transition: color 0.2s;
}

.refresh-btn:hover {
  color: #246b55;
}

.captcha-input-row {
  display: flex;
  gap: 8px;
}

.captcha-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #d4c9b0;
  border-radius: 6px;
  font-size: 16px;
  outline: none;
}

.captcha-input:focus {
  border-color: #246b55;
}

.captcha-confirm-btn {
  padding: 8px 16px;
  background: #246b55;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
}

.captcha-confirm-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.captcha-error {
  color: #b42318;
  font-size: 13px;
  margin: 8px 0 0;
}
</style>
