import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

// Панель раздаётся nginx по пути /admin/ и доступна только из VPN.
export default defineConfig({
  base: '/admin/',
  plugins: [react()],
  // Панель внутренняя, один бандл с antd проще кэшировать, чем десяток мелких
  build: { chunkSizeWarningLimit: 1600 },
  server: {
    port: 5173,
    proxy: { '/admin/v1': 'http://localhost:8000' },
  },
  test: { environment: 'jsdom', globals: true },
});
