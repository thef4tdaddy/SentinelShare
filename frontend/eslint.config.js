import baseConfig from './configs/linting/eslint.config.js';

export default [
    ...baseConfig,
    {
        ignores: ['**/*.cjs', 'dist/**']
    }
];
