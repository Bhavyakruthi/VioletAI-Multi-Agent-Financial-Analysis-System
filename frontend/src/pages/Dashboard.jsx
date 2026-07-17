import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { documentsApi, reportsApi, stockApi } from '../utils/api'
import { motion } from 'framer-motion'
import NewsScroller from '../components/NewsScroller'

export default function Dashboard() {
    const { user } = useAuth()
    const [stats, setStats] = useState({
        documents: 0,
        reports: 0,
        recentTicker: null
    })
    const [recentReports, setRecentReports] = useState([])
    const [marketPulse, setMarketPulse] = useState([])
    const [loading, setLoading] = useState(true)
    const [watchlist, setWatchlist] = useState(() => JSON.parse(localStorage.getItem('violet-watchlist') || '[]'))
    const [recentSearches, setRecentSearches] = useState(() => JSON.parse(localStorage.getItem('violet-recents') || '[]'))

    useEffect(() => {
        localStorage.setItem('violet-watchlist', JSON.stringify(watchlist))
    }, [watchlist])

    useEffect(() => {
        localStorage.setItem('violet-recents', JSON.stringify(recentSearches))
    }, [recentSearches])

    useEffect(() => {
        fetchData()

        const handleSync = () => {
            setWatchlist(JSON.parse(localStorage.getItem('violet-watchlist') || '[]'))
            setRecentSearches(JSON.parse(localStorage.getItem('violet-recents') || '[]'))
        }
        window.addEventListener('storage', handleSync)
        return () => window.removeEventListener('storage', handleSync)
    }, [])

    const fetchData = async () => {
        try {
            const [docsRes, reportsRes, marketRes] = await Promise.all([
                documentsApi.list().catch(() => ({ data: { documents: [] } })),
                reportsApi.list().catch(() => ({ data: { reports: [] } })),
                stockApi.getMarketIndices().catch(() => ({ data: [] }))
            ])

            if (marketRes?.data) {
                setMarketPulse(marketRes.data)
            }

            const reports = reportsRes.data?.reports || []
            setRecentReports(reports.slice(0, 3))

            // Auto-track the last analyzed ticker from reports as a recent search
            if (reports[0]?.ticker) {
                updateRecentSearches(reports[0].ticker)
            }

            setStats({
                documents: docsRes.data?.documents?.length || 0,
                reports: reports.length || 0,
                recentTicker: reports[0]?.ticker || null
            })
        } catch (error) {
            console.error('Error fetching dashboard data:', error)
        } finally {
            setLoading(false)
        }
    }

    const updateRecentSearches = (ticker) => {
        setRecentSearches(prev => {
            const filtered = prev.filter(t => t !== ticker)
            const updated = [ticker, ...filtered].slice(0, 8)
            return updated
        })
    }

    const toggleWatchlist = (ticker) => {
        setWatchlist(prev =>
            prev.includes(ticker)
                ? prev.filter(t => t !== ticker)
                : [...prev, ticker]
        )
    }

    return (
        <div className="dashboard-v2">
            <motion.header
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="dashboard-header"
            >
                <div>
                    <h1 className="outfit">Welcome back, {user?.email?.split('@')[0]}</h1>
                    <p className="subtitle">Operational status: <span className="status-online">System Online</span></p>
                </div>
                <div className="header-date">
                    {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
                </div>
            </motion.header>

            {/* Live News Scroller */}
            <NewsScroller />

            {/* Market Pulse Widget */}
            <div className="market-pulse-container">
                {marketPulse.map((item, i) => (
                    <motion.div
                        key={item.symbol}
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.1 }}
                        className="market-widget"
                    >
                        <span className="market-symbol">{item.symbol}</span>
                        <span className="market-value">{item.value}</span>
                        <span className={`market-change ${item.up ? 'up' : 'down'}`}>
                            {item.up ? '▲' : '▼'} {item.change}
                        </span>
                    </motion.div>
                ))}
            </div>

            <div className="dashboard-grid">
                {/* Main Stats Column */}
                <div className="dashboard-main">
                    <section className="stats-section">
                        <div className="glass-card stat-card-v2">
                            <span className="stat-label">Total Knowledge base</span>
                            <div className="stat-val-group">
                                <span className="stat-value">{stats.documents}</span>
                                <span className="stat-unit">Docs</span>
                            </div>
                            <div className="stat-footer">
                                <Link to="/documents" className="stat-link">Manage Library →</Link>
                            </div>
                        </div>

                        <div className="glass-card stat-card-v2 accent">
                            <span className="stat-label">Generated Intel</span>
                            <div className="stat-val-group">
                                <span className="stat-value">{stats.reports}</span>
                                <span className="stat-unit">Reports</span>
                            </div>
                            <div className="stat-footer">
                                <Link to="/reports" className="stat-link">View Vault →</Link>
                            </div>
                        </div>
                    </section>

                    <section className="quick-nav-section">
                        <div className="section-header-row">
                            <h3 className="outfit section-title">Strategic Hub</h3>
                            <div className="info-badge" title="Access depth analysis and document-aware chat features from this hub.">ⓘ Hub Info</div>
                        </div>
                        <div className="nav-cards">
                            <Link to="/analysis" className="nav-card-v2">
                                <div className="nav-icon-v2">📈</div>
                                <div>
                                    <h4 className="outfit">Depth Analysis</h4>
                                    <p>Full AI structural breakdown</p>
                                </div>
                            </Link>
                            <Link to="/chat" className="nav-card-v2">
                                <div className="nav-icon-v2">💬</div>
                                <div>
                                    <h4 className="outfit">Contextual Chat</h4>
                                    <p>Query your document database</p>
                                </div>
                            </Link>
                        </div>
                    </section>
                </div>

                {/* Side Activity Column */}
                <aside className="dashboard-aside">
                    <div className="glass-card recent-activity">
                        <div className="section-header-row">
                            <h3 className="outfit">Recent Intelligence</h3>
                            <div className="info-icon" title="List of the most recent automated equity reports you've generated.">ⓘ</div>
                        </div>
                        {recentReports.length > 0 ? (
                            <div className="activity-list">
                                {recentReports.map((report, i) => (
                                    <div key={i} className="activity-item">
                                        <div className="activity-indicator"></div>
                                        <div className="activity-content">
                                            <span className="activity-ticker">{report.ticker}</span>
                                            <span className="activity-type">Equity Report</span>
                                            <span className="activity-time">{new Date(report.created_at).toLocaleDateString()}</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p className="no-activity">No recent reports found.</p>
                        )}
                        <Link to="/reports" className="btn-secondary-v2">View All Reports</Link>
                    </div>

                    <div className="glass-card platform-vitals">
                        <div className="section-header-row" style={{ marginBottom: '1rem' }}>
                            <h4 className="outfit">Market Tools</h4>
                            <div className="info-icon" title="Quick access to your pinned stocks and history.">ⓘ</div>
                        </div>
                        <div className="watchlist-section">
                            <span className="tiny-label">WATCHLIST</span>
                            {watchlist.length > 0 ? (
                                <div className="ticker-tags">
                                    {watchlist.map(ticker => (
                                        <Link key={ticker} to={`/analysis?ticker=${ticker}`} className="ticker-tag active" state={{ autoFetch: true }}>
                                            {ticker}
                                        </Link>
                                    ))}
                                </div>
                            ) : (
                                <p className="tiny-text">Your watchlist is empty.</p>
                            )}
                        </div>
                        <div className="recent-section" style={{ marginTop: '1rem' }}>
                            <span className="tiny-label">RECENT SEARCHES</span>
                            <div className="ticker-tags">
                                {recentSearches.map(ticker => (
                                    <Link key={ticker} to={`/analysis?ticker=${ticker}`} className="ticker-tag" state={{ autoFetch: true }}>
                                        {ticker}
                                    </Link>
                                ))}
                            </div>
                        </div>
                    </div>

                    <div className="glass-card platform-vitals">
                        <h4 className="outfit">Platform Vitals</h4>
                        <div className="vital-row">
                            <span>NLP Engine</span>
                            <span className="vital-status">Gemini 2.5 Flash</span>
                        </div>
                        <div className="vital-row">
                            <span>Forecasting</span>
                            <span className="vital-status">Prophet v1.1</span>
                        </div>
                    </div>
                </aside>
            </div>

            <style>{`
                .dashboard-v2 {
                    display: flex;
                    flex-direction: column;
                    gap: 2.5rem;
                }
                .section-header-row {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 1.5rem;
                }
                .info-badge {
                    font-size: 0.65rem;
                    background: rgba(124, 58, 237, 0.1);
                    border: 1px solid rgba(124, 58, 237, 0.2);
                    padding: 0.25rem 0.6rem;
                    border-radius: 6px;
                    color: var(--accent-secondary);
                    cursor: help;
                }
                .info-icon {
                    font-size: 0.9rem;
                    color: var(--text-muted);
                    cursor: help;
                    opacity: 0.7;
                    transition: opacity 0.2s;
                }
                .info-icon:hover { opacity: 1; color: var(--accent-primary); }
                .dashboard-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-end;
                }
                .subtitle {
                    color: var(--text-dim);
                    font-size: 0.95rem;
                    margin-top: 0.5rem;
                }
                .status-online {
                    color: #22c55e;
                    font-weight: 600;
                    display: inline-flex;
                    align-items: center;
                    gap: 0.4rem;
                }
                .status-online::before {
                    content: '';
                    width: 8px;
                    height: 8px;
                    background: #22c55e;
                    border-radius: 50%;
                    display: inline-block;
                }
                .header-date {
                    font-weight: 500;
                    color: var(--text-dim);
                    padding-bottom: 0.5rem;
                }
                .market-pulse-container {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 1.5rem;
                }
                .market-widget {
                    background: var(--glass-bg);
                    backdrop-filter: var(--glass-blur);
                    border: 1px solid var(--glass-border);
                    padding: 1.25rem 1.5rem;
                    border-radius: 16px;
                    display: flex;
                    flex-direction: column;
                    gap: 0.25rem;
                    transition: all 0.3s ease;
                    box-shadow: var(--shadow-premium);
                }
                .market-widget:hover {
                    transform: translateY(-4px);
                    background: var(--bg-dark-700);
                    border-color: var(--accent-primary);
                    box-shadow: var(--shadow-premium);
                }
                .market-symbol {
                    font-size: 0.75rem;
                    font-weight: 700;
                    color: var(--text-muted);
                    letter-spacing: 0.05em;
                }
                .market-value {
                    font-size: 1.15rem;
                    font-weight: 700;
                    color: var(--text-main);
                }
                .market-change {
                    font-size: 0.85rem;
                    font-weight: 600;
                }
                .market-change.up { color: #16a34a; }
                .market-change.down { color: #dc2626; }

                .dashboard-grid {
                    display: grid;
                    grid-template-columns: 1fr 340px;
                    gap: 2.5rem;
                }
                .dashboard-main {
                    display: flex;
                    flex-direction: column;
                    gap: 2.5rem;
                }
                .stats-section {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 1.5rem;
                }
                .stat-card-v2 {
                    padding: 2.5rem;
                    position: relative;
                    overflow: hidden;
                    background: var(--glass-bg);
                    border: 1px solid var(--glass-border);
                    border-radius: 20px;
                    box-shadow: var(--shadow-premium);
                }
                .stat-card-v2.accent {
                    background: linear-gradient(135deg, rgba(124, 58, 237, 0.12), var(--glass-bg));
                    border-color: var(--accent-primary);
                }
                .stat-label {
                    color: var(--text-dim);
                    font-size: 0.875rem;
                    text-transform: uppercase;
                    letter-spacing: 0.1em;
                    font-weight: 600;
                }
                .stat-val-group {
                    display: flex;
                    align-items: baseline;
                    gap: 0.75rem;
                    margin: 1rem 0;
                }
                .stat-value {
                    font-size: 3.5rem;
                    font-weight: 800;
                    color: var(--text-main);
                    font-family: 'Outfit', sans-serif;
                }
                .stat-unit {
                    font-size: 1.1rem;
                    color: var(--text-muted);
                    font-weight: 500;
                }
                .stat-footer {
                    margin-top: 1rem;
                }
                .stat-link {
                    color: var(--accent-secondary);
                    text-decoration: none;
                    font-size: 0.9rem;
                    font-weight: 600;
                    transition: var(--transition-smooth);
                }
                .stat-link:hover {
                    color: var(--accent-primary);
                    transform: translateX(5px);
                }

                .section-title {
                    font-size: 1.25rem;
                    color: var(--text-main);
                    margin-bottom: 1.5rem;
                }
                .nav-cards {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 1.5rem;
                }
                .nav-card-v2 {
                    background: var(--glass-bg);
                    backdrop-filter: var(--glass-blur);
                    border: 1px solid var(--glass-border);
                    border-radius: 20px;
                    padding: 1.75rem;
                    display: flex;
                    align-items: center;
                    gap: 1.5rem;
                    text-decoration: none;
                    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                    box-shadow: var(--shadow-premium);
                }
                .nav-card-v2:hover {
                    border-color: var(--accent-primary);
                    background: var(--bg-dark-700);
                    transform: translateY(-8px) scale(1.02);
                    box-shadow: var(--shadow-premium);
                }
                .nav-icon-v2 {
                    width: 50px;
                    height: 50px;
                    background: rgba(124, 58, 237, 0.1);
                    border-radius: 12px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 1.5rem;
                }
                .nav-card-v2 h4 {
                    color: var(--text-main);
                    font-size: 1.1rem;
                    margin-bottom: 0.25rem;
                }
                .nav-card-v2 p {
                    color: var(--text-dim);
                    font-size: 0.85rem;
                }

                .dashboard-aside {
                    display: flex;
                    flex-direction: column;
                    gap: 1.5rem;
                }
                .recent-activity {
                    padding: 1.5rem;
                }
                .activity-list {
                    display: flex;
                    flex-direction: column;
                    gap: 1.25rem;
                    margin-top: 1.5rem;
                }
                .activity-item {
                    display: flex;
                    gap: 1rem;
                    align-items: flex-start;
                }
                .activity-indicator {
                    width: 8px;
                    height: 8px;
                    background: var(--accent-primary);
                    border-radius: 50%;
                    box-shadow: 0 0 10px var(--accent-glow);
                    margin-top: 6px;
                }
                .activity-content {
                    display: flex;
                    flex-direction: column;
                    gap: 0.1rem;
                }
                .activity-ticker {
                    font-weight: 700;
                    color: var(--text-main);
                }
                .activity-type {
                    font-size: 0.75rem;
                    color: var(--text-muted);
                }
                .activity-time {
                    font-size: 0.75rem;
                    color: var(--text-dim);
                }
                .btn-secondary-v2 {
                    display: block;
                    width: 100%;
                    text-align: center;
                    padding: 0.85rem;
                    margin-top: 1.5rem;
                    background: var(--glass-bg);
                    backdrop-filter: var(--glass-blur);
                    border: 1px solid var(--glass-border);
                    border-radius: 12px;
                    color: var(--text-dim);
                    text-decoration: none;
                    font-weight: 700;
                    font-size: 0.9rem;
                    transition: all 0.3s ease;
                }
                .btn-secondary-v2:hover {
                    background: var(--bg-dark-700);
                    color: var(--accent-primary);
                    border-color: var(--accent-primary);
                    transform: scale(1.02);
                }
                .platform-vitals {
                    padding: 1.5rem;
                }
                .vital-row {
                    display: flex;
                    justify-content: space-between;
                    margin-top: 0.75rem;
                    font-size: 0.85rem;
                    color: var(--text-dim);
                }
                .vital-status {
                    color: var(--accent-secondary);
                    font-weight: 600;
                }
                .tiny-label {
                    font-size: 0.65rem;
                    font-weight: 800;
                    color: var(--text-muted);
                    display: block;
                    margin-bottom: 0.75rem;
                }
                .tiny-text {
                    font-size: 0.75rem;
                    color: var(--text-dim);
                    font-style: italic;
                }
                .ticker-tags {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 0.5rem;
                }
                .ticker-tag {
                    padding: 0.4rem 0.8rem;
                    background: var(--glass-bg);
                    border: 1px solid var(--glass-border);
                    border-radius: 8px;
                    color: var(--text-dim);
                    text-decoration: none;
                    font-size: 0.75rem;
                    font-weight: 700;
                    transition: all 0.2s ease;
                }
                .ticker-tag:hover {
                    background: var(--bg-dark-700);
                    border-color: var(--accent-primary);
                    color: var(--accent-secondary);
                }
                .ticker-tag.active {
                    background: var(--accent-primary);
                    border-color: var(--accent-secondary);
                    color: white; /* Contrast against dark accent background */
                }
            `}</style>
        </div>
    )
}
