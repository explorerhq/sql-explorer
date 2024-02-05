import { resolve } from 'path';

export default {
  plugins: [],
  root: resolve(__dirname, './'),
  base: '',
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
      '~bootstrap': resolve(__dirname, './node_modules/bootstrap'),
      '~bootstrap-icons': resolve(__dirname, './node_modules/bootstrap-icons'),
    },
  },
  build: {
    outDir: resolve(__dirname, './explorer/static/explorer'),
    assetsDir: '',
    emptyOutDir: true,
    target: 'es2015',
    rollupOptions: {
      input: {
        main: resolve(__dirname, '/explorer/src/js/main.js'),
        // Some magic here; Vite always builds to styles.css, we named our entrypoint SCSS file the same thing
        // so that in the base template HTML file we can include 'styles.scss', and rename just the extension
        // in the vite template tag, and get both the dev and prod builds to work.
        styles: resolve(__dirname, '/explorer/src/scss/styles.scss'),
      },
      output: {
        entryFileNames: `[name].js`,
        chunkFileNames: `[name].js`,
        assetFileNames: `[name].[ext]`
      },
    },
  },
};
