import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../context/AuthContext'
import { chatApi, documentsApi } from '../utils/api'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import { Send, Bot, User, Sparkles, FileText, Trash2, MessageSquare, ChevronLeft, ChevronRight, Database } from 'lucide-react'

// Simple markdown renderer for chat messages
const renderMarkdown = (text) => {
    if (!text) return ''
    return text
        // Headers
        .replace(/^### (.*$)/gm, '<h3>$1</h3>')
        .replace(/^## (.*$)/gm, '<h2>$1</h2>')
        .replace(/^# (.*$)/gm, '<h1>$1</h1>')
        // Bold: **text** or __text__
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/__(.+?)__/g, '<strong>$1</strong>')
        // Italic: *text* or _text_
        .replace(/\*([^*]+)\*/g, '<em>$1</em>')
        .replace(/_([^_]+)_/g, '<em>$1</em>')
        // Code: `code`
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        // Horizontal rule
        .replace(/^---$/gm, '<hr/>')
        // Bullet points: * item or - item (Must be before line breaks)
        .replace(/^[\*\-]\s+(.+)$/gm, '<span class="bullet-item">• $1</span>')
        // Line breaks
        .replace(/\n/g, '<br/>')
}

export default function Chat() {
    const { session } = useAuth()
    const [messages, setMessages] = useState([])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const [documents, setDocuments] = useState([])
    const [selectedDocs, setSelectedDocs] = useState([])
    const [sidebarOpen, setSidebarOpen] = useState(true)
    const [currentTicker, setCurrentTicker] = useState('')
    const messagesEndRef = useRef(null)
    const inputRef = useRef(null)

    useEffect(() => {
        fetchDocuments()
        fetchHistory()
    }, [])

    useEffect(() => {
        scrollToBottom()
    }, [messages])

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }

    const fetchDocuments = async () => {
        try {
            const res = await documentsApi.list()
            setDocuments(res.data?.documents || [])
        } catch (error) {
            console.error('Error fetching documents:', error)
        }
    }

    const fetchHistory = async () => {
        try {
            const res = await chatApi.getHistory()
            setMessages(res.data?.messages || [])
        } catch (error) {
            console.error('Error fetching history:', error)
        }
    }

    const toggleDoc = (id) => {
        setSelectedDocs(prev =>
            prev.includes(id) ? prev.filter(d => d !== id) : [...prev, id]
        )
    }

    const handleSend = async (e) => {
        e.preventDefault()
        if (!input.trim() || loading) return

        const userMessage = { role: 'user', content: input, timestamp: new Date().toISOString() }
        setMessages(prev => [...prev, userMessage])
        setInput('')
        setLoading(true)

        try {
            const res = await chatApi.query(input, currentTicker || null, selectedDocs) // Pass ticker and docs
            const aiMessage = {
                role: 'assistant',
                content: res.data.response,
                sources: res.data.sources,
                timestamp: res.data.timestamp
            }
            setMessages(prev => [...prev, aiMessage])
        } catch (error) {
            toast.error('Failed to get response')
            console.error('Chat error:', error)
        } finally {
            setLoading(false)
            inputRef.current?.focus()
        }
    }

    const handleClearHistory = async () => {
        if (!confirm('Clear all conversation history?')) return
        try {
            await chatApi.clearHistory()
            setMessages([])
            toast.success('Conversation cleared')
        } catch (error) {
            toast.error('Failed to clear history')
        }
    }

    const quickPrompts = [
        { icon: <FileText size={18} />, text: "Summarize my documents" },
        { icon: <Sparkles size={18} />, text: "What are the key insights?" },
        { icon: <Database size={18} />, text: "Extract financial metrics" },
    ]

    // Stock-specific prompts (shown when ticker is set)
    const stockPrompts = currentTicker ? [
        { icon: <Sparkles size={18} />, text: `What's the outlook for ${currentTicker}?` },
        { icon: <MessageSquare size={18} />, text: `Summarize recent ${currentTicker} news` },
        { icon: <FileText size={18} />, text: `Compare ${currentTicker} to competitors` },
        { icon: <Database size={18} />, text: `What are the key risks for ${currentTicker}?` },
    ] : []

    const allPrompts = [...stockPrompts, ...quickPrompts]

    return (
        <div className="chat-container-gpt">
            {/* Collapsible Sidebar */}
            <aside className={`chat-sidebar-gpt ${sidebarOpen ? 'open' : 'collapsed'}`}>
                <button className="sidebar-toggle" onClick={() => setSidebarOpen(!sidebarOpen)}>
                    {sidebarOpen ? <ChevronLeft size={18} /> : <ChevronRight size={18} />}
                </button>

                {sidebarOpen && (
                    <>
                        <div className="sidebar-section">
                            <h3><Database size={16} /> Knowledge Base</h3>
                            <div className="sidebar-controls">
                                <button onClick={() => setSelectedDocs(documents.map(d => d.id))} className="text-link">Select All</button>
                                <button onClick={() => setSelectedDocs([])} className="text-link">Clear</button>
                            </div>
                            <p className="sidebar-hint">{selectedDocs.length} of {documents.length} sources active</p>
                        </div>

                        <div className="docs-list">
                            {documents.map(doc => (
                                <div
                                    key={doc.id}
                                    className={`doc-chip-selectable ${selectedDocs.includes(doc.id) ? 'active' : ''}`}
                                    onClick={() => toggleDoc(doc.id)}
                                >
                                    <input
                                        type="checkbox"
                                        checked={selectedDocs.includes(doc.id)}
                                        onChange={() => { }} // Controlled via parent div onClick
                                        className="doc-checkbox"
                                    />
                                    <FileText size={14} className="doc-icon" />
                                    <div className="doc-info-mini">
                                        <span className="doc-name">{doc.filename}</span>
                                        <span className="doc-tag">{doc.file_type === 'generated_report' ? 'Report' : 'File'}</span>
                                    </div>
                                </div>
                            ))}
                        </div>

                        {/* Stock Context Input */}
                        <div className="sidebar-section stock-context-section">
                            <h3><Sparkles size={16} /> Stock Context</h3>
                            <p className="sidebar-hint">Enter a ticker for stock-specific questions</p>
                            <input
                                type="text"
                                className="ticker-input-chat"
                                placeholder="e.g. AAPL, TSLA"
                                value={currentTicker}
                                onChange={(e) => setCurrentTicker(e.target.value.toUpperCase())}
                            />
                        </div>

                        <button onClick={handleClearHistory} className="btn-clear-gpt">
                            <Trash2 size={14} /> Clear Chat
                        </button>
                    </>
                )}
            </aside>

            {/* Main Chat Area */}
            <main className="chat-main-gpt">
                <div className="messages-container-gpt">
                    <AnimatePresence>
                        {messages.length === 0 ? (
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="welcome-screen-gpt"
                            >
                                <div className="welcome-icon">
                                    <Bot size={48} />
                                </div>
                                <h1 className="outfit">VioletAI Assistant</h1>
                                <p>Ask questions about your documents and research reports</p>

                                <div className="quick-prompts-gpt">
                                    {allPrompts.map((prompt, i) => (
                                        <button
                                            key={i}
                                            className="prompt-card-gpt"
                                            onClick={() => setInput(prompt.text)}
                                        >
                                            {prompt.icon}
                                            <span>{prompt.text}</span>
                                        </button>
                                    ))}
                                </div>
                            </motion.div>
                        ) : (
                            messages.map((msg, idx) => (
                                <motion.div
                                    key={idx}
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ duration: 0.2 }}
                                    className={`message-row-gpt ${msg.role}`}
                                >
                                    <div className="message-avatar">
                                        {msg.role === 'user' ? (
                                            <User size={20} />
                                        ) : (
                                            <Bot size={20} />
                                        )}
                                    </div>
                                    <div className="message-content-gpt">
                                        <div
                                            className="message-text"
                                            dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.content) }}
                                        />
                                        {msg.sources && msg.sources.length > 0 && (
                                            <div className="message-sources-gpt">
                                                <span className="sources-label">Sources:</span>
                                                {msg.sources.map((src, i) => (
                                                    <span key={i} className="source-chip">{src.source}</span>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </motion.div>
                            ))
                        )}
                    </AnimatePresence>

                    {loading && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="message-row-gpt assistant"
                        >
                            <div className="message-avatar">
                                <Bot size={20} />
                            </div>
                            <div className="message-content-gpt">
                                <div className="typing-indicator-gpt">
                                    <span></span><span></span><span></span>
                                </div>
                            </div>
                        </motion.div>
                    )}

                    <div ref={messagesEndRef} />
                </div>

                {/* Fixed Input Bar */}
                <div className="input-area-gpt">
                    <form onSubmit={handleSend} className="input-form-gpt">
                        <div className="input-wrapper-gpt">
                            <input
                                ref={inputRef}
                                type="text"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder="Message VioletAI..."
                                disabled={loading}
                            />
                            <button
                                type="submit"
                                className="send-btn-gpt"
                                disabled={loading || !input.trim()}
                            >
                                <Send size={18} />
                            </button>
                        </div>
                        <p className="input-hint">VioletAI uses RAG to search your documents for accurate answers</p>
                    </form>
                </div>
            </main>

            <style>{`
                .chat-container-gpt {
                    position: fixed;
                    top: 70px;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    display: flex;
                    background: var(--bg-dark-900);
                    overflow: hidden;
                    z-index: 5;
                }
                
                /* Markdown styling */
                .message-text strong { 
                    font-weight: 700; 
                    color: #a78bfa;
                }
                .message-text em { font-style: italic; }
                .message-text code {
                    background: rgba(139, 92, 246, 0.15);
                    padding: 0.15rem 0.4rem;
                    border-radius: 4px;
                    font-family: 'Fira Code', monospace;
                    font-size: 0.85em;
                    color: #c4b5fd;
                }
                .message-text .bullet-item {
                    display: block;
                    padding-left: 0.5rem;
                    margin: 0.25rem 0;
                }
                
                .message-text h1, .message-text h2, .message-text h3 {
                    margin: 1rem 0 0.5rem;
                    color: var(--text-main);
                    font-weight: 700;
                }
                .message-text h1 { font-size: 1.4rem; }
                .message-text h2 { font-size: 1.2rem; }
                .message-text h3 { font-size: 1.1rem; }
                .message-text hr {
                    border: none;
                    border-top: 1px solid rgba(255, 255, 255, 0.1);
                    margin: 1.5rem 0;
                }

                /* Sidebar */
                .chat-sidebar-gpt {
                    width: 280px;
                    background: var(--glass-bg);
                    backdrop-filter: blur(25px);
                    -webkit-backdrop-filter: blur(25px);
                    border-right: 1px solid var(--glass-border);
                    display: flex;
                    flex-direction: column;
                    padding: 1.5rem;
                    position: relative;
                    transition: width 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                    z-index: 10;
                }
                .chat-sidebar-gpt.collapsed {
                    width: 50px;
                    padding: 1rem 0.5rem;
                }
                .sidebar-toggle {
                    position: absolute;
                    right: -12px;
                    top: 1rem;
                    width: 24px;
                    height: 24px;
                    background: var(--bg-dark-700);
                    border: 1px solid var(--glass-border);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                    color: var(--text-main);
                    z-index: 10;
                }
                .sidebar-section {
                    margin-bottom: 1.5rem;
                }
                .sidebar-section h3 {
                    font-size: 0.85rem;
                    font-weight: 600;
                    color: var(--text-main);
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    margin: 0;
                }
                .sidebar-hint {
                    font-size: 0.75rem;
                    color: var(--text-muted);
                    margin: 0.25rem 0 0;
                }
                .ticker-input-chat {
                    width: 100%;
                    padding: 0.75rem;
                    border-radius: 8px;
                    border: 1px solid var(--glass-border);
                    background: var(--bg-dark-700);
                    color: var(--text-main);
                    font-family: inherit;
                    font-size: 0.9rem;
                    font-weight: 600;
                    text-transform: uppercase;
                    margin-top: 0.75rem;
                }
                .ticker-input-chat:focus {
                    outline: none;
                    border-color: var(--accent-primary);
                }
                .ticker-input-chat::placeholder {
                    color: var(--text-dim);
                    text-transform: none;
                }
                .stock-context-section {
                    border-top: 1px solid var(--glass-border);
                    padding-top: 1rem;
                }
                .docs-list {
                    flex: 1;
                    overflow-y: auto;
                    display: flex;
                    flex-direction: column;
                    gap: 0.5rem;
                    padding-right: 4px;
                }
                .doc-chip-selectable {
                    display: flex;
                    align-items: center;
                    gap: 0.75rem;
                    gap: 0.75rem;
                    padding: 0.8rem 1rem;
                    background: var(--bg-dark-700);
                    border: 1px solid var(--glass-border);
                    border-radius: 12px;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    position: relative;
                }
                .doc-chip-selectable:hover {
                    background: rgba(139, 92, 246, 0.05);
                    border-color: rgba(139, 92, 246, 0.3);
                    transform: translateX(2px);
                }
                .doc-chip-selectable.active {
                    background: rgba(139, 92, 246, 0.12);
                    border-color: rgba(139, 92, 246, 0.5);
                    box-shadow: 0 4px 15px rgba(139, 92, 246, 0.1);
                }
                .doc-checkbox {
                    accent-color: #8b5cf6;
                    cursor: pointer;
                    width: 14px;
                    height: 14px;
                }
                .doc-icon {
                    color: rgba(255, 255, 255, 0.5);
                }
                .active .doc-icon {
                    color: #a78bfa;
                }
                .doc-info-mini {
                    display: flex;
                    flex-direction: column;
                    min-width: 0;
                }
                .doc-name {
                    font-size: 0.85rem;
                    color: var(--text-main);
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }
                .doc-tag {
                    font-size: 0.65rem;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    color: var(--text-muted);
                    margin-top: 1px;
                }
                .sidebar-controls {
                    display: flex;
                    gap: 0.75rem;
                    margin-top: 0.5rem;
                }
                .text-link {
                    background: none;
                    border: none;
                    color: #8b5cf6;
                    font-size: 0.7rem;
                    padding: 0;
                    cursor: pointer;
                    font-weight: 500;
                }
                .text-link:hover {
                    text-decoration: underline;
                    color: #a78bfa;
                }
                .btn-clear-gpt {
                    margin-top: 1rem;
                    padding: 0.75rem;
                    background: transparent;
                    border: 1px solid var(--glass-border);
                    border-radius: 8px;
                    color: var(--text-dim);
                    font-size: 0.8rem;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 0.5rem;
                    transition: all 0.2s;
                }
                .btn-clear-gpt:hover {
                    background: rgba(239, 68, 68, 0.1);
                    border-color: rgba(239, 68, 68, 0.3);
                    color: #ef4444;
                }

                /* Main Chat */
                .chat-main-gpt {
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                    overflow: hidden;
                }
                .messages-container-gpt {
                    flex: 1;
                    overflow-y: auto;
                    padding: 2rem 0;
                }

                /* Welcome Screen */
                .welcome-screen-gpt {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    height: 100%;
                    text-align: center;
                    padding: 2rem;
                }
                .welcome-icon {
                    width: 80px;
                    height: 80px;
                    background: linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white; /* Contrast against accent gradient background */
                    margin-bottom: 1.5rem;
                }
                .welcome-screen-gpt h1 {
                    font-size: 2rem;
                    margin: 0;
                    color: var(--text-main);
                }
                .welcome-screen-gpt p {
                    color: var(--text-dim);
                    margin: 0.5rem 0 2rem;
                }
                .quick-prompts-gpt {
                    display: flex;
                    gap: 1rem;
                    flex-wrap: wrap;
                    justify-content: center;
                    max-width: 700px;
                }
                .prompt-card-gpt {
                    display: flex;
                    align-items: center;
                    gap: 0.75rem;
                    padding: 1rem 1.25rem;
                    background: var(--bg-dark-700);
                    border: 1px solid var(--glass-border);
                    border-radius: 12px;
                    color: var(--text-dim);
                    font-size: 0.9rem;
                    cursor: pointer;
                    transition: all 0.2s;
                }
                .prompt-card-gpt:hover {
                    background: var(--bg-dark-700);
                    border-color: var(--accent-primary);
                    color: var(--text-main);
                    transform: translateY(-2px);
                }

                /* Message Rows - ChatGPT Style */
                .message-row-gpt {
                    display: flex;
                    gap: 1rem;
                    padding: 1.5rem 2rem;
                    max-width: 900px;
                    margin: 0 auto;
                    width: 100%;
                }
                .message-row-gpt.user {
                    background: rgba(139, 92, 246, 0.05);
                }
                .message-row-gpt.assistant {
                    background: transparent;
                }
                .message-avatar {
                    width: 36px;
                    height: 36px;
                    border-radius: 8px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    flex-shrink: 0;
                }
                .message-row-gpt.user .message-avatar {
                    background: linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%);
                    color: white;
                }
                .message-row-gpt.assistant .message-avatar {
                    background: rgba(16, 185, 129, 0.15);
                    color: #10b981;
                }
                .message-content-gpt {
                    flex: 1;
                    min-width: 0;
                }
                .message-text {
                    color: var(--text-main);
                    line-height: 1.7;
                    font-size: 0.95rem;
                    white-space: pre-wrap;
                }
                .message-sources-gpt {
                    margin-top: 0.75rem;
                    display: flex;
                    flex-wrap: wrap;
                    align-items: center;
                    gap: 0.5rem;
                }
                .sources-label {
                    font-size: 0.75rem;
                    color: rgba(255, 255, 255, 0.4);
                    font-weight: 500;
                }
                .source-chip {
                    font-size: 0.7rem;
                    padding: 0.25rem 0.5rem;
                    background: rgba(139, 92, 246, 0.15);
                    color: #a78bfa;
                    border-radius: 4px;
                }

                /* Typing Indicator */
                .typing-indicator-gpt {
                    display: flex;
                    gap: 4px;
                    padding: 0.5rem 0;
                }
                .typing-indicator-gpt span {
                    width: 8px;
                    height: 8px;
                    background: rgba(255, 255, 255, 0.3);
                    border-radius: 50%;
                    animation: bounce 1.4s infinite;
                }
                .typing-indicator-gpt span:nth-child(2) { animation-delay: 0.2s; }
                .typing-indicator-gpt span:nth-child(3) { animation-delay: 0.4s; }
                @keyframes bounce {
                    0%, 60%, 100% { transform: translateY(0); }
                    30% { transform: translateY(-4px); }
                }

                /* Input Area - Fixed Bottom */
                .input-area-gpt {
                    border-top: 1px solid var(--glass-border);
                    padding: 2rem;
                    background: linear-gradient(0deg, var(--bg-dark-900) 0%, transparent 100%);
                    backdrop-filter: blur(10px);
                }
                .input-form-gpt {
                    max-width: 850px;
                    margin: 0 auto;
                }
                .input-wrapper-gpt {
                    display: flex;
                    align-items: center;
                    background: var(--bg-dark-800);
                    border: 1px solid var(--glass-border);
                    border-radius: 16px;
                    padding: 0.5rem 0.75rem 0.5rem 1.25rem;
                    transition: all 0.2s;
                }
                .input-wrapper-gpt:focus-within {
                    border-color: rgba(139, 92, 246, 0.5);
                    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
                }
                .input-wrapper-gpt input {
                    flex: 1;
                    background: transparent;
                    border: none;
                    color: var(--text-main);
                    font-size: 1rem;
                    padding: 0.75rem 0;
                }
                .input-wrapper-gpt input::placeholder {
                    color: rgba(255, 255, 255, 0.4);
                }
                .input-wrapper-gpt input:focus {
                    outline: none;
                }
                .send-btn-gpt {
                    width: 42px;
                    height: 42px;
                    background: linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%);
                    border: none;
                    border-radius: 12px;
                    color: white; /* White for contrast on gradient */
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.2s;
                }
                .send-btn-gpt:hover:not(:disabled) {
                    transform: scale(1.05);
                    box-shadow: 0 4px 15px rgba(139, 92, 246, 0.4);
                }
                .send-btn-gpt:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                }
                .input-hint {
                    text-align: center;
                    font-size: 0.75rem;
                    color: rgba(255, 255, 255, 0.35);
                    margin: 0.75rem 0 0;
                }
            `}</style>
        </div>
    )
}
