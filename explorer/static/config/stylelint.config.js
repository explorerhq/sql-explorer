module.exports = {
  rules: {
    'scss/at-extend-no-missing-placeholder': null,
    'selector-class-pattern': '^[a-z0-9\\-]+$', // allow double hyphens
  },
  extends: [
    // Use the Standard config as the base
    // https://github.com/stylelint/stylelint-config-standard
    'stylelint-config-standard-scss',
    // Enforce a standard order for CSS properties
    // https://github.com/stormwarning/stylelint-config-recess-order
    'stylelint-config-recess-order',
  ],
};
