import { resolve } from 'path';

export default {
  plugins: [],
  root: resolve(__dirname, '../'),
  base: '/static/',
  server: {
    open: false,
    watch: {
      usePolling: true,
      disableGlobbing: false,
    },
  },
  resolve: {
    extensions: ['.js', '.json'],
    alias: {
      '~bootstrap': resolve(__dirname, '../../../node_modules/bootstrap'),
      '~bootstrap-icons': resolve(__dirname, '../../../node_modules/bootstrap-icons'),
    },
  },
  build: {
    outDir: resolve(__dirname, '../../public/static/dist'),
    assetsDir: '',
    manifest: true,
    emptyOutDir: true,
    target: 'es2015',
    rollupOptions: {
      input: {
        main: resolve(__dirname, '../js/src/main.js'),
        styles: resolve(__dirname, '../scss/main.scss'),
      },
      output: {
        chunkFileNames: undefined,
      },
    },
  },
};
