import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import QueryWidget from './components/QueryWidget';

function App() {
  const [count, setCount] = useState(0)

  return (
    <QueryWidget />
  )
}

export default App
