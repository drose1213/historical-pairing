import { defineStore } from "pinia";
import { ref, computed, watch } from "vue";
import { api } from "../api";

export interface User {
  id: string;
  email: string;
  isAdmin: boolean;
}

export const useAuthStore = defineStore("auth", () => {
  const user = ref<User | null>(null);
  const token = ref<string | null>(null);

  const isLoggedIn = computed(() => !!user.value);
  const isAdmin = computed(() => user.value?.isAdmin ?? false);

  async function fetchMe() {
    try {
      const response = await api.getMe();
      user.value = response;
    } catch {
      user.value = null;
      token.value = null;
    }
  }

  async function login(email: string, password: string) {
    const response = await api.login(email, password);
    token.value = response.access_token;
    user.value = response.user;
  }

  async function register(email: string, code: string, password: string) {
    const response = await api.register(email, code, password);
    token.value = response.access_token;
    user.value = response.user;
  }

  async function sendCode(email: string, captchaToken: string, captchaAnswer: string) {
    await api.sendCode(email, captchaToken, captchaAnswer);
  }

  function logout() {
    user.value = null;
    token.value = null;
  }

  function initFromStorage() {
    if (token.value) {
      fetchMe();
    }
  }

  return {
    user,
    token,
    isLoggedIn,
    isAdmin,
    fetchMe,
    login,
    register,
    sendCode,
    logout,
    initFromStorage,
  };
}, {
  persist: {
    key: "auth",
    storage: localStorage,
    paths: ["token"],
  },
});
