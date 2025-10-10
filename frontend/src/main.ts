import './style.css'
import { App } from './App'

const appContainer = document.querySelector<HTMLDivElement>('#app')!
const app = new App(appContainer)
app.render()
