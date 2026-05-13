import App from './App.vue'
import { createApp } from 'vue'
import { initStore } from './store'
import { initRouter } from './router'
import '@styles/core/tailwind.css'
import '@styles/index.scss'
import { setupGlobDirectives } from './directives'
import { setupErrorHandle } from './utils/sys/error-handle'

const app = createApp(App)

initStore(app)
initRouter(app)
setupGlobDirectives(app)
setupErrorHandle(app)

app.mount('#app')
