import { defineStore } from "pinia";
import { ref } from "vue";
import { api, type CreateGameResponse, type SubmitResponse } from "../api";

export const useGameStore = defineStore("game", () => {
  const currentGame = ref<CreateGameResponse | null>(null);
  const results = ref<SubmitResponse | null>(null);
  const timeUsed = ref<number | null>(null);
  const gameId = ref<string | null>(null);

  async function createGame(keyword: string) {
    const game = await api.createGame(keyword);
    currentGame.value = game;
    gameId.value = game.gameId;
    results.value = null;
    timeUsed.value = null;
    return game;
  }

  async function submitGame(matches: Array<{ leftId: string; rightId: string }>, time: number) {
    if (!gameId.value) throw new Error("No game in progress");
    const result = await api.submitGame(gameId.value, matches);
    results.value = result;
    timeUsed.value = time;
    return result;
  }

  function reset() {
    currentGame.value = null;
    results.value = null;
    timeUsed.value = null;
    gameId.value = null;
  }

  return {
    currentGame,
    results,
    timeUsed,
    gameId,
    createGame,
    submitGame,
    reset,
  };
});
