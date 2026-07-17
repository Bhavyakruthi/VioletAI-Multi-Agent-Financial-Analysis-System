import { useState, useEffect } from 'react'
import { ExternalLink, TrendingUp } from 'lucide-react'
import { motion } from 'framer-motion'

const NewsScroller = () => {
    const [news, setNews] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetchNews()
        const interval = setInterval(fetchNews, 5 * 60 * 1000)
        return () => clearInterval(interval)
    }, [])

    const fetchNews = async () => {
        const sampleNews = [
            { title: "Tech Stocks Rally as AI Investments Surge", link: "https://finance.yahoo.com", publisher: "Yahoo Finance" },
            { title: "Federal Reserve Signals Potential Rate Cuts", link: "https://www.cnbc.com", publisher: "CNBC" },
            { title: "Oil Prices Rise on Supply Concerns", link: "https://www.reuters.com", publisher: "Reuters" },
            { title: "Major Tech Earnings Beat Expectations", link: "https://www.bloomberg.com", publisher: "Bloomberg" },
            { title: "Market Volatility Increases Amid Trade Tensions", link: "https://www.wsj.com", publisher: "Wall Street Journal" },
            { title: "S&P 500 Reaches New Record High", link: "https://www.marketwatch.com", publisher: "MarketWatch" },
            { title: "Gold Prices Surge as Dollar Weakens", link: "https://www.kitco.com", publisher: "Kitco News" },
            { title: "Cryptocurrency Market Shows Strong Recovery", link: "https://www.coindesk.com", publisher: "CoinDesk" },
            { title: "Housing Market Cools as Rates Rise", link: "https://www.zillow.com", publisher: "Zillow" },
            { title: "Jobless Claims Fall to Lowest Level This Year", link: "https://www.bls.gov", publisher: "Bureau of Labor Statistics" },
        ]
        setNews(sampleNews)
        setLoading(false)
    }

    if (loading) return null;

    // Duplicating for infinite scroll
    const scrollingNews = [...news, ...news, ...news];

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            style={{
                width: '100%',
                overflow: 'hidden',
                background: 'rgba(10, 11, 20, 0.4)',
                padding: '28px 0',
                borderBottom: '1px solid rgba(139, 92, 246, 0.1)',
                borderTop: '1px solid rgba(139, 92, 246, 0.05)',
                position: 'relative',
                marginTop: '10px',
                marginBottom: '30px',
                zIndex: 10,
                backdropFilter: 'blur(5px)'
            }}
        >
            {/* Visual fade masks with violet tint */}
            <div style={{
                position: 'absolute', left: 0, top: 0, bottom: 0, width: '150px',
                background: 'linear-gradient(to right, #0a0b14, rgba(10, 11, 20, 0))', zIndex: 11, pointerEvents: 'none'
            }} />
            <div style={{
                position: 'absolute', right: 0, top: 0, bottom: 0, width: '150px',
                background: 'linear-gradient(to left, #0a0b14, rgba(10, 11, 20, 0))', zIndex: 11, pointerEvents: 'none'
            }} />

            <div style={{ display: 'flex', alignItems: 'center' }}>
                <motion.div
                    animate={{ x: [0, -2800] }}
                    transition={{
                        x: {
                            repeat: Infinity,
                            repeatType: "loop",
                            duration: 55,
                            ease: "linear",
                        },
                    }}
                    style={{
                        display: 'flex',
                        gap: '30px',
                        paddingLeft: '50px',
                        whiteSpace: 'nowrap'
                    }}
                >
                    {scrollingNews.map((item, index) => (
                        <motion.a
                            key={index}
                            href={item.link}
                            target="_blank"
                            rel="noopener noreferrer"
                            whileHover={{ scale: 1.02, y: -2 }}
                            style={{
                                display: 'flex',
                                flexDirection: 'column',
                                gap: '10px',
                                padding: '20px',
                                minWidth: '320px',
                                maxWidth: '320px',
                                background: 'rgba(23, 25, 48, 0.4)',
                                backdropFilter: 'blur(16px)',
                                WebkitBackdropFilter: 'blur(16px)',
                                borderRadius: '20px',
                                border: '1px solid rgba(139, 92, 246, 0.15)',
                                textDecoration: 'none',
                                transition: 'all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275)',
                                color: 'white',
                                boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.37)'
                            }}
                            onMouseOver={(e) => {
                                e.currentTarget.style.borderColor = 'rgba(124, 58, 237, 0.6)';
                                e.currentTarget.style.background = 'rgba(30, 32, 60, 0.6)';
                                e.currentTarget.style.boxShadow = '0 0 20px rgba(139, 92, 246, 0.2)';
                            }}
                            onMouseOut={(e) => {
                                e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.15)';
                                e.currentTarget.style.background = 'rgba(23, 25, 48, 0.4)';
                                e.currentTarget.style.boxShadow = '0 8px 32px 0 rgba(0, 0, 0, 0.37)';
                            }}
                        >
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span style={{
                                    fontSize: '11px',
                                    fontWeight: '800',
                                    color: '#a78bfa', // Violet color
                                    letterSpacing: '2px',
                                    textTransform: 'uppercase',
                                    pointerEvents: 'none'
                                }}>
                                    {item.publisher}
                                </span>
                                <ExternalLink size={14} style={{ opacity: 0.4, color: '#a78bfa', pointerEvents: 'none' }} />
                            </div>
                            <h3 style={{
                                fontSize: '15px',
                                fontWeight: '600',
                                margin: 0,
                                whiteSpace: 'normal',
                                display: '-webkit-box',
                                WebkitLineClamp: 2,
                                WebkitBoxOrient: 'vertical',
                                overflow: 'hidden',
                                lineHeight: '1.5',
                                color: '#f8f8f8',
                                pointerEvents: 'none'
                            }}>
                                {item.title}
                            </h3>
                            <div style={{
                                marginTop: '6px',
                                height: '2px',
                                width: '40px',
                                background: 'linear-gradient(to right, #8b5cf6, transparent)',
                                borderRadius: '2px',
                                pointerEvents: 'none'
                            }} />
                        </motion.a>
                    ))}
                </motion.div>
            </div>
        </motion.div>
    )
}

export default NewsScroller
