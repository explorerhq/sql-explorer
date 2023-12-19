const isDevMode = process.env.NODE_ENV === 'development';

module.exports = {
  ignorePatterns: ['public/static/', 'collected_static/', 'htmlcov/'],
  root: true,

  env: {
    node: true,
    browser: true,
  },

  globals: {},

  extends: [
    'airbnb-base',
  ],

  rules: {

    // Allow console.error or console.warn in production and no warnings in development
    'no-console': isDevMode ? 'off' : ['error', { allow: ['warn', 'error'] }],

    // Allow debugger in development
    'no-debugger': isDevMode ? 'off' : 'error',

    // Allow build dependencies to be in devDependencies instead of dependencies
    'import/no-extraneous-dependencies': ['error', { devDependencies: true }],

    // just one var declaration per function
    'one-var': ['error', 'always'],

  },
};
