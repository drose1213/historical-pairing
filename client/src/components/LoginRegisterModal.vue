<script setup lang="ts">
import { ref, computed } from "vue";
import { X, Mail, Lock, Eye, EyeOff } from "lucide-vue-next";
import { useAuthStore } from "../stores/auth";

const emit = defineEmits<{
  close: [];
  success: [];
}>();

const authStore = useAuthStore();

const mode = ref<"login" | "register">("login");
const email = ref("");
const password = ref("");
const code = ref("");
const showPassword = ref(false);
const loading = ref(false);
const sendingCode = ref(false);
const cooldown = ref(0);
const error = ref("");

const isRegister = computed(() => mode.value === "register");

async function sendCode() {
  if (cooldown.value > 0) return;

  sendingCode.value = true;
  error.value = "";
  try {
    await authStore.sendCode(email.value);
    cooldown.value = 60;
    const timer = setInterval(() => {
      cooldown.value--;
      if (cooldown.value <= 0) {
        clearInterval(timer);
      }
    }, 1000);
  } catch (err) {
    error.value = err instanceof Error ? err.message : "发送失败";
  } finally {
    sendingCode.value = false;
  }
}

async function submit() {
  loading.value = true;
  error.value = "";
  try {
    if (isRegister.value) {
      await authStore.register(email.value, code.value, password.value);
    } else {
      await authStore.login(email.value, password.value);
    }
    emit("success");
    emit("close");
  } catch (err) {
    error.value = err instanceof Error ? err.message : "操作失败";
  } finally {
    loading.value = false;
  }
}

function switchMode() {
  mode.value = isRegister.value ? "login" : "register";
  error.value = "";
}
</script>

<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal">
      <div class="modal-header">
        <h2>{{ isRegister ? "注册" : "登录" }}</h2>
        <button class="close-btn" @click="emit('close')">
          <X :size="20" />
        </button>
      </div>

      <p v-if="error" class="error">{{ error }}</p>

      <form @submit.prevent="submit">
        <div class="input-group">
          <Mail :size="18" class="input-icon" />
          <input
            v-model="email"
            type="email"
            placeholder="输入邮箱地址"
            required
          />
        </div>

        <div v-if="isRegister" class="input-group code-group">
          <input
            v-model="code"
            type="text"
            placeholder="验证码"
            maxlength="6"
            required
          />
          <button
            type="button"
            class="send-code-btn"
            :disabled="sendingCode || cooldown > 0"
            @click="sendCode"
          >
            {{ cooldown > 0 ? `${cooldown}秒` : "发送验证码" }}
          </button>
        </div>

        <div class="input-group">
          <Lock :size="18" class="input-icon" />
          <input
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            placeholder="输入密码"
            required
            minlength="6"
          />
          <button type="button" class="toggle-password" @click="showPassword = !showPassword">
            <EyeOff v-if="showPassword" :size="18" />
            <Eye v-else :size="18" />
          </button>
        </div>

        <button type="submit" class="submit-btn" :disabled="loading">
          {{ loading ? "处理中..." : (isRegister ? "注册" : "登录") }}
        </button>
      </form>

      <p class="switch-mode">
        {{ isRegister ? "已有账号？" : "没有账号？" }}
        <a href="#" @click.prevent="switchMode">{{ isRegister ? "登录" : "注册" }}</a>
      </p>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal {
  background: white;
  border-radius: 16px;
  width: min(420px, calc(100% - 32px));
  padding: 24px;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.modal-header h2 {
  font-size: 20px;
  font-weight: 800;
  color: #1a1a1a;
  margin: 0;
}

.close-btn {
  padding: 8px;
  background: none;
  border: none;
  cursor: pointer;
  color: #6b7280;
}

.error {
  background: #fef2f2;
  color: #b42318;
  padding: 12px;
  border-radius: 8px;
  font-size: 14px;
  margin: 0 0 16px;
}

.input-group {
  display: flex;
  align-items: center;
  gap: 8px;
  border: 1px solid #d4c9b0;
  border-radius: 10px;
  padding: 12px 14px;
  margin-bottom: 12px;
}

.input-group:focus-within {
  border-color: #246b55;
}

.input-icon {
  color: #9ca3af;
  flex-shrink: 0;
}

.input-group input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 16px;
  background: transparent;
}

.code-group input {
  width: 120px;
}

.send-code-btn {
  padding: 8px 12px;
  background: #f0f9f6;
  color: #246b55;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
}

.send-code-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.toggle-password {
  padding: 4px;
  background: none;
  border: none;
  cursor: pointer;
  color: #9ca3af;
}

.submit-btn {
  width: 100%;
  padding: 14px;
  background: #246b55;
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  margin-top: 8px;
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.switch-mode {
  text-align: center;
  font-size: 14px;
  color: #6b7280;
  margin: 16px 0 0;
}

.switch-mode a {
  color: #246b55;
  text-decoration: none;
  font-weight: 600;
}
</style>
