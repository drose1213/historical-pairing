import { defineStore } from "pinia";
import { ref, computed } from "vue";
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
    localStorage.setItem("token", response.access_token);
  }

  async function register(email: string, code: string, password: string) {
    const response = await api.register(email, code, password);
    token.value = response.access_token;
    user.value = response.user;
    localStorage.setItem("token", response.access_token);
  }

  async function sendCode(email: string) {
    await api.sendCode(email);
  }

  function logout() {
    user.value = null;
    token.value = null;
    localStorage.removeItem("token");
  }

  function initFromStorage() {
    const storedToken = localStorage.getItem("token");
    if (storedToken) {
      token.value = storedToken;
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
});
