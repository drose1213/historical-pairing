<script setup lang="ts">
import { onMounted } from "vue";
import { RouterView } from "vue-router";
import { useAuthStore } from "./stores/auth";

const authStore = useAuthStore();

onMounted(() => {
  authStore.initFromStorage();
  if (authStore.token) {
    authStore.fetchMe();
  }
});
</script>

<template>
  <RouterView />
</template>
