const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: [],
  devServer: {
    host: '127.0.0.1',
    port: 3030,
    historyApiFallback: true,
  },
})

/* proxy: {
  '/': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    pathRewrite: {
      '^/': '/'
    }
  }
} */
