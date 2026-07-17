
import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { stockApi, analysisApi } from '../utils/api'
import { Plus, X, Search, TrendingUp, DollarSign, Activity, BarChart2, Shield, Zap } from 'lucide-react'
import PriceChart from '../components/PriceChart'
import toast from 'react-hot-toast'

// Popular stocks for dropdown
const POPULAR_STOCKS = [
    { ticker: 'AAPL', name: 'Apple Inc.' },
    { ticker: 'GOOGL', name: 'Alphabet Inc.' },
    { ticker: 'MSFT', name: 'Microsoft Corp.' },
    { ticker: 'AMZN', name: 'Amazon.com Inc.' },
    { ticker: 'TSLA', name: 'Tesla Inc.' },
    { ticker: 'META', name: 'Meta Platforms' },
    { ticker: 'NVDA', name: 'NVIDIA Corp.' },
    { ticker: 'RELIANCE.NS', name: 'Reliance Industries' },
    { ticker: 'TCS.NS', name: 'Tata Consultancy Services' },
    { ticker: 'INFY.NS', name: 'Infosys Ltd.' },
    { ticker: 'HDFCBANK.NS', name: 'HDFC Bank' },
    { ticker: 'ICICIBANK.NS', name: 'ICICI Bank' },
    { ticker: 'WIPRO.NS', name: 'Wipro Ltd.' },
    { ticker: 'ITC.NS', name: 'ITC Ltd.' },
    { ticker: 'SBIN.NS', name: 'State Bank of India' },
]

export default function Compare() {
    // We manage 3 slots. Each slot can be null (empty) or have data.
    // Structure: { ticker: 'AAPL', priceData: {}, history: [], analysis: {} }
    const [slots, setSlots] = useState([null, null, null])
    const [loading, setLoading] = useState([false, false, false])
    const [inputs, setInputs] = useState(['', '', ''])
    const [showDropdown, setShowDropdown] = useState([false, false, false])

    useEffect(() => {
        const handleClickOutside = () => setShowDropdown([false, false, false])
        window.addEventListener('click', handleClickOutside)
        return () => window.removeEventListener('click', handleClickOutside)
    }, [])

    // Helper to fetch data for a specific slot index
    const fetchSlotData = async (index, ticker) => {
        if (!ticker) return

        // Set loading for this slot
        const newLoading = [...loading]
        newLoading[index] = true
        setLoading(newLoading)

        // Close dropdown
        const newDropdowns = [...showDropdown]
        newDropdowns[index] = false
        setShowDropdown(newDropdowns)

        try {
            // Parallel fetch: Stock Data, History, and Sentiment
            const [stockRes, infoRes, historyRes, sentimentRes] = await Promise.all([
                stockApi.getData(ticker),
                stockApi.getInfo(ticker),
                stockApi.getHistory(ticker, '1y'),
                analysisApi.sentiment({ ticker }) // Get quick sentiment
            ]).catch(err => {
                throw err
            })

            const newSlotData = {
                ticker: ticker.toUpperCase(),
                name: infoRes.data.longName,
                price: stockRes.data,
                info: infoRes.data,
                history: historyRes.data.data,
                sentiment: sentimentRes.data.sentiment,
                fhi: sentimentRes.data.fhi
            }

            setSlots(prev => {
                const next = [...prev]
                next[index] = newSlotData
                return next
            })

            // Clear input
            const newInputs = [...inputs]
            newInputs[index] = ''
            setInputs(newInputs)

        } catch (error) {
            console.error(error)
            toast.error(`Failed to load ${ticker}`)
        } finally {
            const newLoading = [...loading]
            newLoading[index] = false
            setLoading(newLoading)
        }
    }

    const removeSlot = (index) => {
        setSlots(prev => {
            const next = [...prev]
            next[index] = null
            return next
        })
    }

    const handleKeyDown = (e, index) => {
        if (e.key === 'Enter') {
            fetchSlotData(index, inputs[index])
        }
    }

    const handleInputFocus = (e, index) => {
        e.stopPropagation()
        const newDropdowns = [...showDropdown]
        newDropdowns[index] = true
        setShowDropdown(newDropdowns)
    }

    const handleInputChange = (e, index) => {
        const newInputs = [...inputs]
        newInputs[index] = e.target.value.toUpperCase()
        setInputs(newInputs)

        const newDropdowns = [...showDropdown]
        newDropdowns[index] = true
        setShowDropdown(newDropdowns)
    }

    // Color helpers
    const getScoreColor = (score) => {
        if (!score) return 'var(--text-muted)'
        if (score >= 70) return '#10b981' // Green
        if (score >= 40) return '#f59e0b' // Orange
        return '#ef4444' // Red
    }

    return (
        <div className="compare-page">
            <header className="page-header">
                <h1><BarChart2 size={28} className="header-icon" /> Portfolio Comparison</h1>
                <p>Analyze assets side-by-side to make smarter allocation decisions</p>
            </header>

            <div className="compare-grid">
                {[0, 1, 2].map((i) => {
                    // Filter stocks for this input
                    const filteredStocks = POPULAR_STOCKS.filter(
                        stock =>
                            stock.ticker.toLowerCase().includes(inputs[i].toLowerCase()) ||
                            stock.name.toLowerCase().includes(inputs[i].toLowerCase())
                    )

                    return (
                        <motion.div
                            key={i}
                            className={`compare-slot glass-card ${!slots[i] ? 'empty' : ''}`}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.1 }}
                        >
                            {!slots[i] ? (
                                <div className="empty-state">
                                    <div className="add-icon">
                                        {loading[i] ? <Activity className="spin" /> : <Plus />}
                                    </div>
                                    <h3>Add Asset</h3>
                                    <div className="slot-search-container" onClick={(e) => e.stopPropagation()}>
                                        <div className="slot-search">
                                            <input
                                                type="text"
                                                placeholder="Enter Ticker..."
                                                value={inputs[i]}
                                                onChange={(e) => handleInputChange(e, i)}
                                                onFocus={(e) => handleInputFocus(e, i)}
                                                onKeyDown={(e) => handleKeyDown(e, i)}
                                            />
                                            <button onClick={() => fetchSlotData(i, inputs[i])} disabled={loading[i]}>
                                                <Search size={16} />
                                            </button>
                                        </div>

                                        {showDropdown[i] && (
                                            <div className="stock-dropdown-mini">
                                                {filteredStocks.map(stock => (
                                                    <div
                                                        key={stock.ticker}
                                                        className="dropdown-item-mini"
                                                        onClick={() => fetchSlotData(i, stock.ticker)}
                                                    >
                                                        <span className="ticker">{stock.ticker}</span>
                                                        <span className="name">{stock.name}</span>
                                                    </div>
                                                ))}
                                                {filteredStocks.length === 0 && (
                                                    <div className="dropdown-item-mini empty">No stocks found</div>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ) : (
                                <div className="filled-slot">
                                    <div className="slot-header">
                                        <div>
                                            <h2>{slots[i].ticker}</h2>
                                            <span className="slot-name">{slots[i].name}</span>
                                        </div>
                                        <button onClick={() => removeSlot(i)} className="btn-close"><X size={18} /></button>
                                    </div>

                                    <div className="metrics-grid">
                                        <div className="metric-row main-price">
                                            <span className="label">Price</span>
                                            <span className="value">
                                                {slots[i].info.currency === 'INR' ? '₹' : '$'}
                                                {slots[i].price.current_price?.toFixed(2)}
                                            </span>
                                        </div>
                                        <div className="metric-row">
                                            <span className="label">Change</span>
                                            <span className={`value ${slots[i].price.change >= 0 ? 'pos' : 'neg'}`}>
                                                {slots[i].price.change >= 0 ? '+' : ''}{slots[i].price.change_percent?.toFixed(2)}%
                                            </span>
                                        </div>
                                        <div className="metric-row">
                                            <span className="label">Market Cap</span>
                                            <span className="value compact">
                                                {slots[i].info.marketCap ? (slots[i].info.marketCap / 1e9).toFixed(2) + 'B' : 'N/A'}
                                            </span>
                                        </div>
                                        <div className="metric-row">
                                            <span className="label">Beta (Risk)</span>
                                            <span className="value">
                                                {slots[i].info.beta !== undefined && slots[i].info.beta !== null ? slots[i].info.beta.toFixed(2) : 'N/A'}
                                            </span>
                                        </div>
                                    </div>

                                    <div className="chart-wrapper-mini">
                                        <PriceChart data={slots[i].history} ticker={slots[i].ticker} period="1y" />
                                    </div>

                                    <div className="health-grid">
                                        <div className="health-item" style={{ borderColor: getScoreColor(slots[i].fhi?.score) }}>
                                            <span className="health-label"><Shield size={14} /> FHI Score</span>
                                            <span className="health-val" style={{ color: getScoreColor(slots[i].fhi?.score) }}>
                                                {slots[i].fhi?.score || 'N/A'}
                                            </span>
                                        </div>
                                        <div className="health-item" style={{ borderColor: slots[i].sentiment?.label === 'Positive' ? '#10b981' : slots[i].sentiment?.label === 'Negative' ? '#ef4444' : '#f59e0b' }}>
                                            <span className="health-label"><Zap size={14} /> Sentiment</span>
                                            <span className="health-val" style={{ color: slots[i].sentiment?.label === 'Positive' ? '#10b981' : slots[i].sentiment?.label === 'Negative' ? '#ef4444' : '#f59e0b' }}>
                                                {slots[i].sentiment?.label || 'N/A'}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </motion.div>
                    )
                })}
            </div>

            <style>{`
                .compare-page {
                    max-width: 1400px;
                    margin: 0 auto;
                    padding: 0 1rem;
                }
                .compare-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
                    gap: 1.5rem;
                    margin-top: 2rem;
                }
                .compare-slot {
                    min-height: 600px;
                    display: flex;
                    flex-direction: column;
                    padding: 1.5rem;
                    transition: all 0.3s ease;
                }
                .compare-slot.empty {
                    justify-content: center;
                    align-items: center;
                    border-style: dashed;
                    border-width: 2px;
                    background: rgba(255,255,255,0.02);
                }
                .empty-state {
                    text-align: center;
                    width: 100%;
                }
                .add-icon {
                    width: 60px;
                    height: 60px;
                    background: rgba(124, 58, 237, 0.1);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: var(--accent-primary);
                    margin: 0 auto 1rem;
                    font-size: 1.5rem;
                }
                .slot-search-container {
                    position: relative;
                    margin-top: 1.5rem;
                }
                .slot-search {
                    display: flex;
                    gap: 0.5rem;
                    background: var(--bg-dark-800);
                    padding: 0.5rem;
                    border-radius: 12px;
                    border: 1px solid var(--glass-border);
                }
                .slot-search input {
                    background: transparent;
                    border: none;
                    color: white;
                    width: 100%;
                    outline: none;
                    text-transform: uppercase;
                    font-weight: 600;
                    padding-left: 0.5rem;
                }
                .slot-search button {
                    background: var(--accent-primary);
                    color: white;
                    border: none;
                    padding: 0.5rem;
                    border-radius: 8px;
                    cursor: pointer;
                }

                .stock-dropdown-mini {
                    position: absolute;
                    top: calc(100% + 8px);
                    left: 0;
                    right: 0;
                    background: var(--bg-dark-800);
                    border: 1px solid var(--glass-border);
                    border-radius: 12px;
                    max-height: 200px;
                    overflow-y: auto;
                    z-index: 50;
                    box-shadow: 0 10px 25px rgba(0,0,0,0.5);
                    padding: 0.5rem;
                }
                .dropdown-item-mini {
                    display: flex;
                    justify-content: space-between;
                    padding: 0.6rem 0.8rem;
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 0.2s;
                    border-bottom: 1px solid rgba(255,255,255,0.05);
                }
                .dropdown-item-mini:last-child { border-bottom: none; }
                .dropdown-item-mini:hover {
                    background: rgba(124, 58, 237, 0.15);
                }
                .dropdown-item-mini .ticker {
                    font-weight: 700;
                    color: var(--accent-secondary);
                }
                .dropdown-item-mini .name {
                    font-size: 0.8rem;
                    color: var(--text-muted);
                    max-width: 120px;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }
                .dropdown-item-mini.empty {
                    justify-content: center;
                    color: var(--text-muted);
                    cursor: default;
                }

                .filled-slot {
                    display: flex;
                    flex-direction: column;
                    gap: 1.5rem;
                    height: 100%;
                }
                .slot-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-start;
                }
                .slot-header h2 {
                    font-size: 1.5rem;
                    margin: 0;
                    color: var(--accent-secondary);
                }
                .slot-name {
                    font-size: 0.85rem;
                    color: var(--text-dim);
                }
                .btn-close {
                    background: transparent;
                    border: none;
                    color: var(--text-muted);
                    cursor: pointer;
                    padding: 0.2rem;
                }
                .btn-close:hover { color: #ef4444; }

                .metrics-grid {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 1rem;
                    background: rgba(0,0,0,0.2);
                    padding: 1rem;
                    border-radius: 12px;
                }
                .metric-row {
                    display: flex;
                    flex-direction: column;
                }
                .metric-row.main-price .value {
                    font-size: 1.5rem;
                    color: white;
                    font-weight: 700;
                }
                .metric-row .label {
                    font-size: 0.75rem;
                    color: var(--text-muted);
                    text-transform: uppercase;
                }
                .metric-row .value {
                    font-weight: 600;
                    color: var(--text-dim);
                }
                .value.pos { color: #10b981; }
                .value.neg { color: #ef4444; }
                
                .chart-wrapper-mini {
                    margin: 0 -1rem;
                }
                /* Override chart container styles for mini mode */
                .chart-wrapper-mini .price-chart-container {
                    border: none;
                    background: transparent;
                    padding: 0;
                    margin: 0;
                }
                .chart-wrapper-mini .chart-header {
                    display: none; /* Hide controls for cleaner look */
                }
                
                .health-grid {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 1rem;
                    margin-top: auto;
                }
                .health-item {
                    border: 1px solid var(--glass-border);
                    padding: 0.75rem;
                    border-radius: 12px;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    text-align: center;
                    background: rgba(255,255,255,0.02);
                }
                .health-label {
                    font-size: 0.75rem;
                    color: var(--text-muted);
                    display: flex;
                    align-items: center;
                    gap: 0.25rem;
                    margin-bottom: 0.25rem;
                }
                .health-val {
                    font-size: 1.1rem;
                    font-weight: 700;
                }

                .spin {
                    animation: spin 1s linear infinite;
                }
                @keyframes spin { 100% { transform: rotate(360deg); } }
            `}</style>
        </div>
    )
}
