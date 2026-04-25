import { useState, useRef, useEffect } from 'react'
import './App.css'

function App() {
  const [messages, setMessages] = useState([
    { role: 'bot', text: 'Hello! I am the UCAR Institutional Intelligence Assistant. How can I help you today?' }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage = input.trim()
    setMessages(prev => [...prev, { role: 'user', text: userMessage }])
    setInput('')
    setIsLoading(true)

    try {
      const response = await fetch('https://hacathon-ucar-production.up.railway.app/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: userMessage })
      })

      const data = await response.json()
      
      if (data.error) {
        setMessages(prev => [...prev, { role: 'bot', text: `❌ Error: ${data.error}` }])
      } else {
        setMessages(prev => [...prev, { role: 'bot', text: data.answer }])
      }
    } catch (error) {
      setMessages(prev => [...prev, { role: 'bot', text: '❌ Failed to connect to server. Make sure server.py is running.' }])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="chat-card">
      <div className="chat-header">
        <div className="status-dot"></div>
        <h2>UCAR Smart Query Engine</h2>
      </div>

      <div className="chat-messages">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.role}`}>
            {msg.text}
          </div>
        ))}
        {isLoading && (
          <div className="message bot">
            <span className="loading-dots">Consulting agents</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask a question about UCAR..."
          disabled={isLoading}
        />
        <button onClick={handleSend} disabled={isLoading || !input.trim()}>
          Send
        </button>
      </div>
    </div>
  )
}

export default App
