<script setup lang="ts">
import { onMounted, ref } from "vue";
import { Save, Settings2, X } from "lucide-vue-next";
import { listConfigs, updateConfig, type ConfigItem } from "./api";

const emit = defineEmits<{ close: [] }>();

const configs = ref<Record<string, string>>({});
const configured = ref<Record<string, boolean>>({});
const loading = ref(false);
const saving = ref<Record<string, boolean>>({});
const error = ref("");

onMounted(async () => {
  loading.value = true;
  error.value = "";
  try {
    const items = await listConfigs();
    items.forEach((item) => {
      configs.value[item.key] = item.value ?? "";
      configured.value[item.key] = item.configured;
    });
  } catch (err) {
    error.value = err instanceof Error ? err.message : "加载失败";
  } finally {
    loading.value = false;
  }
});

async function save(key: string) {
  saving.value = { ...saving.value, [key]: true };
  error.value = "";
  try {
    const updated = await updateConfig(key, configs.value[key] || "");
    configs.value[key] = updated.value ?? "";
    configured.value[key] = updated.configured;
  } catch (err) {
    error.value = err instanceof Error ? err.message : "保存失败";
  } finally {
    saving.value = { ...saving.value, [key]: false };
  }
}

const configFields = [
  { key: "openai_api_key", label: "API Key", placeholder: "输入新的 MiniMax 或 OpenAI API Key" },
  { key: "openai_base_url", label: "Base URL", placeholder: "https://api.minimax.chat/v1" },
  { key: "openai_model", label: "模型", placeholder: "MiniMax-Text-01" },
];
</script>

<template>
  <div class="settings-overlay" @click.self="emit('close')">
    <div class="settings-panel">
      <div class="settings-header">
        <div class="settings-title">
          <Settings2 :size="20" />
          <h2>API 设置</h2>
        </div>
        <button class="icon-button" @click="emit('close')">
          <X :size="20" />
        </button>
      </div>

      <p v-if="error" class="error-line">
        <span>{{ error }}</span>
      </p>

      <div v-if="loading" class="loading-text">加载中...</div>

      <div v-else class="config-list">
        <div v-for="field in configFields" :key="field.key" class="config-row">
          <label :for="field.key">{{ field.label }}</label>
          <div class="config-input-row">
            <input
              :id="field.key"
              v-model="configs[field.key]"
              :type="field.key === 'openai_api_key' ? 'password' : 'text'"
              :placeholder="field.key === 'openai_api_key' && configured[field.key] ? '已配置，如需更新请重新输入' : field.placeholder"
              class="config-input"
              autocomplete="off"
            />
            <button
              class="save-button"
              :disabled="saving[field.key]"
              @click="save(field.key)"
            >
              <Save :size="16" />
              <span>{{ saving[field.key] ? "保存中" : "保存" }}</span>
            </button>
          </div>
          <p v-if="field.key === 'openai_api_key' && configured[field.key]" class="secret-status">
            已配置密钥，出于安全考虑不回显原值。
          </p>
        </div>
      </div>

      <p class="config-hint">
        配置将保存到数据库，无需修改配置文件。
      </p>
    </div>
  </div>
</template>

<style scoped>
.settings-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.settings-panel {
  background: #ffffff;
  border-radius: 12px;
  width: min(520px, calc(100% - 32px));
  padding: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
}

.settings-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.settings-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.settings-title h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 800;
  color: #15191f;
}

.icon-button {
  width: 36px;
  height: 36px;
  border: 1px solid #cfd6df;
  border-radius: 8px;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #475467;
}

.icon-button:hover {
  background: #f4f1ea;
}

.error-line {
  margin: 0 0 16px;
  padding: 10px 14px;
  background: #fff2f0;
  border: 1px solid #df7b6f;
  border-radius: 8px;
  color: #b42318;
  font-weight: 700;
  font-size: 14px;
}

.loading-text {
  text-align: center;
  color: #6b7280;
  padding: 24px;
}

.config-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.config-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.config-row label {
  font-weight: 700;
  font-size: 14px;
  color: #344054;
}

.config-input-row {
  display: flex;
  gap: 8px;
}

.config-input {
  flex: 1;
  min-height: 42px;
  border: 1px solid #cfd6df;
  border-radius: 8px;
  background: #ffffff;
  color: #18202a;
  padding: 0 14px;
  font: inherit;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.config-input:focus {
  border-color: #2f6fed;
  box-shadow: 0 0 0 3px rgba(47, 111, 237, 0.14);
}

.save-button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 42px;
  border: 0;
  border-radius: 8px;
  padding: 0 14px;
  background: #246b55;
  color: #ffffff;
  font-weight: 800;
  font-size: 14px;
  white-space: nowrap;
}

.save-button:disabled {
  opacity: 0.56;
  cursor: not-allowed;
}

.config-hint {
  margin: 16px 0 0;
  font-size: 13px;
  color: #6b7280;
  text-align: center;
}

.secret-status {
  margin: 0;
  font-size: 12px;
  color: #246b55;
  font-weight: 700;
}
</style>
