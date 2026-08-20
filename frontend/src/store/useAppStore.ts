import { create } from 'zustand';

import { api } from '../services/api';
import type { GeneratedServer, SpecParseResult } from '../types';

interface AppState {
  servers: GeneratedServer[];
  currentSpec: SpecParseResult | null;
  loadingServers: boolean;
  fetchServers: () => Promise<void>;
  setCurrentSpec: (spec: SpecParseResult | null) => void;
  removeServer: (serverId: number) => Promise<void>;
}

export const useAppStore = create<AppState>((set, get) => ({
  servers: [],
  currentSpec: null,
  loadingServers: false,

  fetchServers: async () => {
    set({ loadingServers: true });
    try {
      const servers = await api.listServers();
      set({ servers });
    } finally {
      set({ loadingServers: false });
    }
  },

  setCurrentSpec: (spec) => set({ currentSpec: spec }),

  removeServer: async (serverId) => {
    await api.deleteServer(serverId);
    set({ servers: get().servers.filter((s) => s.id !== serverId) });
  },
}));
