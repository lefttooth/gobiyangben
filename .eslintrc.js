module.exports = {
  root: true,
  env: {
    node: true
  },
  extends: [
    'plugin:vue/vue3-essential',
    'eslint:recommended'
  ],
  parserOptions: {
    ecmaVersion: 2020
  },
  rules: {
    'no-console': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
    'no-debugger': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
    // 禁用未使用变量检查
    'no-unused-vars': 'off',
    'vue/no-unused-vars': 'off',
    // 其他可能需要禁用的规则
    'vue/multi-word-component-names': 'off'
  }
}