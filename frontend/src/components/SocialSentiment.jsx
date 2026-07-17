// SocialSentiment Component
// ==========================
// Display Social Media sentiment (Reddit, StockTwits, Twitter) for a stock

import React, { useState, useEffect } from 'react'
import { stockApi } from '../utils/api'
import { MessageCircle, TrendingUp, TrendingDown, Minus, ExternalLink, ThumbsUp, MessageSquare, Bird, Twitter, Heart, Activity } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

export default function SocialSentiment({ ticker }) {
    const [redditData, setRedditData] = useState(null)
    const [stData, setStData] = useState(null)
    const [twitterData, setTwitterData] = useState(null)
    const [activeTab, setActiveTab] = useState('reddit') // 'reddit', 'stocktwits', 'twitter'
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const fetchAllSentiment = async () => {
            if (!ticker) return
            setLoading(true)
            try {
                const [redditRes, stRes, twitterRes] = await Promise.all([
                    stockApi.getSocialSentiment(ticker),
                    stockApi.getStockTwitsSentiment(ticker),
                    stockApi.getTwitterSentiment(ticker)
                ])
                setRedditData(redditRes.data)
                setStData(stRes.data)
                setTwitterData(twitterRes.data)

                // Smart tab selection
                if (redditRes.data?.mention_count > 0) setActiveTab('reddit')
                else if (stRes.data?.mention_count > 0) setActiveTab('stocktwits')
                else if (twitterRes.data?.mention_count > 0) setActiveTab('twitter')

            } catch (error) {
                console.error("Failed to fetch social sentiment", error)
            } finally {
                setLoading(false)
            }
        }

        fetchAllSentiment()
    }, [ticker])

    if (loading) {
        return (
            <div className="social-sentiment-loading">
                <div className="skeleton-social"></div>
            </div>
        )
    }

    const currentData = {
        reddit: redditData,
        stocktwits: stData,
        twitter: twitterData
    }[activeTab]

    const hasData = currentData && currentData.mention_count > 0
    const anyData = (redditData?.mention_count > 0) || (stData?.mention_count > 0) || (twitterData?.mention_count > 0)

    if (!anyData) return null

    const sentimentIcon = {
        Bullish: <TrendingUp size={18} color="#10b981" />,
        Bearish: <TrendingDown size={18} color="#ef4444" />,
        Mixed: <Minus size={18} color="#f59e0b" />,
    }[currentData?.sentiment_label] || <Minus size={18} />

    const sentimentColor = {
        Bullish: "#10b981",
        Bearish: "#ef4444",
        Mixed: "#f59e0b",
    }[currentData?.sentiment_label] || "#6b7280"

    const platformIcon = {
        reddit: <MessageCircle size={14} />,
        stocktwits: <MessageSquare size={14} />,
        twitter: <Twitter size={14} />
    }[activeTab]

    const platformTitle = {
        reddit: 'Reddit',
        stocktwits: 'StockTwits',
        twitter: 'X (Twitter)'
    }[activeTab]

    return (
        <motion.div
            className="social-sentiment-card glass-card"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
        >
            <div className="social-tabs">
                <button
                    className={`tab-btn ${activeTab === 'reddit' ? 'active' : ''}`}
                    onClick={() => setActiveTab('reddit')}
                >
                    <MessageCircle size={14} /> Reddit
                    {redditData?.mention_count > 0 && <span className="tab-indicator"></span>}
                </button>
                <button
                    className={`tab-btn ${activeTab === 'stocktwits' ? 'active' : ''}`}
                    onClick={() => setActiveTab('stocktwits')}
                >
                    <MessageSquare size={14} /> StockTwits
                    {stData?.mention_count > 0 && <span className="tab-indicator"></span>}
                </button>
                <button
                    className={`tab-btn ${activeTab === 'twitter' ? 'active' : ''}`}
                    onClick={() => setActiveTab('twitter')}
                >
                    <Twitter size={14} /> Twitter
                    {twitterData?.mention_count > 0 && <span className="tab-indicator"></span>}
                </button>
            </div>

            <AnimatePresence mode="wait">
                <motion.div
                    key={activeTab}
                    initial={{ opacity: 0, x: 10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -10 }}
                    transition={{ duration: 0.2 }}
                >
                    {!hasData ? (
                        <div className="no-social-data">
                            <p>No recent mentions found on {platformTitle}</p>
                        </div>
                    ) : (
                        <>
                            <div className="social-header">
                                <h3>
                                    {activeTab === 'reddit' ? <MessageCircle size={18} /> :
                                        activeTab === 'twitter' ? <Twitter size={18} /> : <MessageSquare size={18} />}
                                    {platformTitle} Sentiment
                                </h3>
                                <div className={`social-badge social-${currentData.sentiment_label?.toLowerCase() || 'neutral'}`}>
                                    {sentimentIcon} {currentData.sentiment_label}
                                </div>
                            </div>

                            <div className="social-stats">
                                <div className="stat-item">
                                    <span className="stat-value">{currentData.mention_count}</span>
                                    <span className="stat-label">Mentions</span>
                                </div>
                                <div className="stat-item">
                                    <span className="stat-value" style={{ color: sentimentColor }}>
                                        {currentData.sentiment_score > 0 ? '+' : ''}{currentData.sentiment_score}
                                    </span>
                                    <span className="stat-label">Score</span>
                                </div>
                            </div>

                            <div className="social-posts">
                                <h4>Top Discussions</h4>
                                {(activeTab === 'reddit' ? currentData.posts : currentData.messages || currentData.posts).slice(0, 3).map((post, i) => (
                                    <a
                                        key={i}
                                        href={post.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="post-item"
                                    >
                                        <div className="post-content">
                                            <span className="post-title">
                                                {activeTab === 'reddit' ? post.title : post.text}
                                            </span>
                                            <span className="post-meta">
                                                <span className="post-subreddit">
                                                    {activeTab === 'reddit' ? `r/${post.subreddit}` : `@${post.user}`}
                                                </span>
                                                <span className="post-stats">
                                                    {activeTab === 'reddit' ? (
                                                        <>
                                                            <ThumbsUp size={12} /> {post.score}
                                                            <MessageSquare size={12} /> {post.num_comments}
                                                        </>
                                                    ) : (
                                                        activeTab === 'stocktwits' ? (
                                                            post.st_sentiment && (
                                                                <span className={`st-label ${post.st_sentiment.toLowerCase()}`}>
                                                                    {post.st_sentiment}
                                                                </span>
                                                            )
                                                        ) : (
                                                            <>
                                                                <Heart size={12} /> {post.likes || 0}
                                                                <Activity size={12} /> {post.retweets || 0}
                                                            </>
                                                        )
                                                    )}
                                                </span>
                                            </span>
                                        </div>
                                        <ExternalLink size={14} className="post-link-icon" />
                                    </a>
                                ))}
                            </div>
                        </>
                    )}
                </motion.div>
            </AnimatePresence>

            <style>{`
                .social-sentiment-card {
                    padding: 1.25rem;
                    margin-top: 1.5rem;
                    min-height: 400px;
                }
                .social-tabs {
                    display: flex;
                    gap: 0.5rem;
                    margin-bottom: 1.5rem;
                    border-bottom: 1px solid rgba(255,255,255,0.06);
                    padding-bottom: 0.5rem;
                    overflow-x: auto;
                }
                .tab-btn {
                    padding: 0.5rem 1rem;
                    border-radius: 8px;
                    background: transparent;
                    border: none;
                    color: var(--text-muted);
                    font-size: 0.85rem;
                    font-weight: 500;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    transition: all 0.2s;
                    position: relative;
                    white-space: nowrap;
                }
                .tab-btn:hover {
                    background: rgba(255,255,255,0.04);
                    color: var(--text-primary);
                }
                .tab-btn.active {
                    background: rgba(124, 58, 237, 0.1);
                    color: var(--accent-primary);
                    border: 1px solid rgba(124, 58, 237, 0.2);
                }
                .tab-indicator {
                    width: 6px;
                    height: 6px;
                    background: var(--accent-primary);
                    border-radius: 50%;
                    position: absolute;
                    top: 4px;
                    right: 4px;
                    box-shadow: 0 0 8px var(--accent-primary);
                }
                .social-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 1rem;
                }
                .social-header h3 {
                    font-size: 1rem;
                    font-weight: 600;
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    margin: 0;
                }
                .social-badge {
                    display: flex;
                    align-items: center;
                    gap: 0.4rem;
                    padding: 0.35rem 0.75rem;
                    border-radius: 20px;
                    font-size: 0.75rem;
                    font-weight: 600;
                }
                .social-bullish {
                    background: rgba(16, 185, 129, 0.1);
                    color: #10b981;
                    border: 1px solid rgba(16, 185, 129, 0.3);
                }
                .social-bearish {
                    background: rgba(239, 68, 68, 0.1);
                    color: #ef4444;
                    border: 1px solid rgba(239, 68, 68, 0.3);
                }
                .social-mixed {
                    background: rgba(245, 158, 11, 0.1);
                    color: #f59e0b;
                    border: 1px solid rgba(245, 158, 11, 0.3);
                }
                .social-stats {
                    display: flex;
                    gap: 2rem;
                    margin-bottom: 1rem;
                }
                .stat-item {
                    display: flex;
                    flex-direction: column;
                }
                .stat-value {
                    font-size: 1.5rem;
                    font-weight: 700;
                }
                .stat-label {
                    font-size: 0.75rem;
                    color: var(--text-muted);
                    text-transform: uppercase;
                }
                .social-posts {
                    border-top: 1px solid rgba(255,255,255,0.06);
                    padding-top: 1rem;
                }
                .social-posts h4 {
                    font-size: 0.85rem;
                    font-weight: 600;
                    margin: 0 0 0.75rem;
                    color: var(--text-dim);
                }
                .post-item {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    padding: 0.75rem;
                    border-radius: 8px;
                    background: rgba(255,255,255,0.02);
                    margin-bottom: 0.5rem;
                    text-decoration: none;
                    color: inherit;
                    transition: all 0.2s;
                }
                .post-item:hover {
                    background: rgba(255,255,255,0.05);
                }
                .post-content {
                    display: flex;
                    flex-direction: column;
                    gap: 0.25rem;
                    flex: 1;
                    min-width: 0;
                }
                .post-title {
                    font-size: 0.85rem;
                    font-weight: 500;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }
                .post-meta {
                    display: flex;
                    align-items: center;
                    gap: 1rem;
                    font-size: 0.7rem;
                    color: var(--text-muted);
                }
                .post-subreddit {
                    color: var(--accent-primary);
                }
                .post-stats {
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                }
                .st-label {
                    font-size: 0.65rem;
                    font-weight: 700;
                    padding: 1px 6px;
                    border-radius: 4px;
                    text-transform: uppercase;
                }
                .st-label.bullish { background: rgba(16, 185, 129, 0.2); color: #10b981; }
                .st-label.bearish { background: rgba(239, 68, 68, 0.2); color: #ef4444; }
                
                .no-social-data {
                    padding: 2rem;
                    text-align: center;
                    color: var(--text-muted);
                    font-size: 0.85rem;
                }
                .social-sentiment-loading {
                    padding: 1.5rem;
                }
                .skeleton-social {
                    height: 250px;
                    background: rgba(255,255,255,0.05);
                    border-radius: 12px;
                    animation: pulse 1.5s infinite;
                }
            `}</style>
        </motion.div>
    )
}
