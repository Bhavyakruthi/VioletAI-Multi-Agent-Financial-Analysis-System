
import React, { useState, useEffect } from 'react'
import { stockApi } from '../utils/api'
import { Play, ExternalLink, Youtube, Clock, User } from 'lucide-react'
import { motion } from 'framer-motion'

export default function VideoFeed({ ticker }) {
    const [videos, setVideos] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const fetchVideos = async () => {
            if (!ticker) return
            setLoading(true)
            try {
                const res = await stockApi.getVideos(ticker, 7)
                setVideos(res.data)
            } catch (error) {
                console.error("Failed to fetch videos", error)
            } finally {
                setLoading(false)
            }
        }

        fetchVideos()
    }, [ticker])

    if (loading) {
        return (
            <div className="video-feed-loading">
                <div className="skeleton-card"></div>
                <div className="skeleton-card"></div>
                <div className="skeleton-card"></div>
            </div>
        )
    }

    if (!videos || videos.length === 0) {
        return null // Hide if no videos
    }

    return (
        <div className="video-feed-section glass-card">
            <h3 className="section-title">
                <Youtube className="section-icon" color="#FF0000" />
                Latest Insights & Analysis
            </h3>

            <div className="video-grid">
                {videos.map((video, index) => (
                    <motion.a
                        key={index}
                        href={video.link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="video-card"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.1 }}
                        whileHover={{ y: -5 }}
                    >
                        <div className="thumbnail-wrapper">
                            <img src={video.thumbnail} alt={video.title} className="thumbnail" />
                            <div className="play-overlay">
                                <Play fill="white" stroke="white" />
                            </div>
                        </div>
                        <div className="video-content">
                            <h4 className="video-title" title={video.title}>{video.title}</h4>
                            <div className="video-meta">
                                <span className="channel"><User size={12} /> {video.channel}</span>
                                <span className="published"><Clock size={12} /> {video.published}</span>
                            </div>
                            <p className="video-summary">{video.description}</p>
                        </div>
                    </motion.a>
                ))}
            </div>

            <style>{`
                .video-feed-section {
                    margin-top: 2rem;
                    padding: 1.5rem;
                }
                .section-title {
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    margin-bottom: 1.5rem;
                    font-size: 1.25rem;
                }
                .video-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                    gap: 1.5rem;
                }
                .video-card {
                    display: flex;
                    flex-direction: column;
                    background: rgba(255,255,255,0.03);
                    border-radius: 12px;
                    overflow: hidden;
                    text-decoration: none;
                    color: inherit;
                    border: 1px solid var(--glass-border);
                    transition: all 0.2s ease;
                }
                .video-card:hover {
                    background: rgba(255,255,255,0.05);
                    border-color: var(--accent-primary);
                }
                .thumbnail-wrapper {
                    position: relative;
                    aspect-ratio: 16/9;
                    overflow: hidden;
                }
                .thumbnail {
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                }
                .play-overlay {
                    position: absolute;
                    inset: 0;
                    background: rgba(0,0,0,0.3);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    opacity: 0;
                    transition: opacity 0.2s;
                }
                .video-card:hover .play-overlay {
                    opacity: 1;
                }
                .video-content {
                    padding: 1rem;
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                }
                .video-title {
                    font-size: 0.95rem;
                    font-weight: 600;
                    margin-bottom: 0.5rem;
                    display: -webkit-box;
                    -webkit-line-clamp: 2;
                    -webkit-box-orient: vertical;
                    overflow: hidden;
                    line-height: 1.4;
                }
                .video-meta {
                    display: flex;
                    justify-content: space-between;
                    font-size: 0.75rem;
                    color: var(--text-muted);
                    margin-bottom: 0.75rem;
                }
                .video-meta span {
                    display: flex;
                    align-items: center;
                    gap: 0.25rem;
                }
                .video-summary {
                    font-size: 0.8rem;
                    color: var(--text-dim);
                    line-height: 1.5;
                    display: -webkit-box;
                    -webkit-line-clamp: 3;
                    -webkit-box-orient: vertical;
                    overflow: hidden;
                }

                .video-feed-loading {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                    gap: 1.5rem;
                    margin-top: 2rem;
                }
                .skeleton-card {
                    height: 250px;
                    background: rgba(255,255,255,0.05);
                    border-radius: 12px;
                    animation: pulse 1.5s infinite;
                }
                @keyframes pulse {
                    0% { opacity: 0.6; }
                    50% { opacity: 1; }
                    100% { opacity: 0.6; }
                }
            `}</style>
        </div>
    )
}
