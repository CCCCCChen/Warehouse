const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true
})

module.exports = {
  devServer: {
    port: 3030,
    historyApiFallback: true,
    client: {
      webSocketURL: {
        hostname: 'localhost',
        port: 8000,
        pathname: '/ws',
        protocol: 'ws',
      },
    },

  }
}

/* proxy: {
  '/': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    pathRewrite: {
      '^/': '/'
    }
  }
} */