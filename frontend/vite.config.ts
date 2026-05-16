import path from 'node:path';
import { fileURLToPath } from 'node:url';

import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

const workspaceRoot = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  '..',
);

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    fs: {
      allow: [workspaceRoot],
    },
    proxy: {
      '/projects': 'http://127.0.0.1:8000',
      '/online-learning': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
    },
  },
});
