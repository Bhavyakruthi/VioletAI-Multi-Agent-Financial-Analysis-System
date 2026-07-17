// SentimentTrend Component
// ========================
// Line chart showing sentiment scores over time

import React, { useState, useEffect } from 'react'
import Chart from 'react-apexcharts'
import { stockApi } from '../utils/api'
import { TrendingUp, TrendingDown, Minus, Activity } from 'lucide-react'
import { motion } from 'framer-motion'

export default function SentimentTrend({ ticker }) {
    const [data, setData] = useState([])
    const [trend, setTrend] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const fetchHistory = async () => {
            if (!ticker) return
            setLoading(true)
            try {
                const res = await stockApi.getSentimentHistory(ticker, 30)
                setData(res.data.data || [])
                setTrend(res.data.trend)
            } catch (error) {
                console.error("Failed to fetch sentiment history", error)
            } finally {
                setLoading(false)
            }
        }

        fetchHistory()
    }, [ticker])

    if (loading) {
        return (
            <div className="sentiment-trend-loading">
                <div className="skeleton-chart"></div>
            </div>
        )
    }

    if (!data || data.length < 2) {
        return null // Not enough data to show trend
    }

    const trendIcon = {
        IMPROVING: <TrendingUp size={18} color="#10b981" />,
        DECLINING: <TrendingDown size={18} color="#ef4444" />,
        STABLE: <Minus size={18} color="#6b7280" />,
    }[trend] || <Activity size={18} />

    const trendColor = {
        IMPROVING: "#10b981",
        DECLINING: "#ef4444",
        STABLE: "#6b7280",
    }[trend] || "#7c3aed"

    const chartOptions = {
        chart: {
            type: 'area',
            sparkline: { enabled: false },
            toolbar: { show: false },
            background: 'transparent',
            animations: {
                enabled: true,
                speed: 800,
            },
        },
        colors: [trendColor],
        fill: {
            type: 'gradient',
            gradient: {
                shadeIntensity: 1,
                opacityFrom: 0.4,
                opacityTo: 0.1,
                stops: [0, 100]
            }
        },
        stroke: {
            curve: 'smooth',
            width: 2,
        },
        grid: {
            borderColor: 'rgba(255,255,255,0.06)',
            padding: { left: 10, right: 10 },
        },
        xaxis: {
            type: 'datetime',
            labels: {
                style: { colors: '#9ca3af', fontSize: '10px' },
                datetimeFormatter: {
                    day: 'MMM dd',
                }
            },
            axisBorder: { show: false },
            axisTicks: { show: false },
        },
        yaxis: {
            min: -1,
            max: 1,
            labels: {
                style: { colors: '#9ca3af', fontSize: '10px' },
                formatter: (val) => val.toFixed(1)
            },
        },
        tooltip: {
            theme: 'dark',
            x: { format: 'MMM dd, yyyy' },
            y: { formatter: (val) => `Score: ${val.toFixed(2)}` }
        },
        dataLabels: { enabled: false },
    }

    const chartSeries = [{
        name: 'Sentiment',
        data: data.map(d => ({
            x: new Date(d.timestamp).getTime(),
            y: d.compound
        }))
    }]

    return (
        <motion.div
            className="sentiment-trend-card glass-card"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
        >
            <div className="trend-header">
                <h3><Activity size={18} /> Sentiment Trend</h3>
                <span className={`trend-badge trend-${trend?.toLowerCase() || 'neutral'}`}>
                    {trendIcon} {trend || 'N/A'}
                </span>
            </div>
            <div className="trend-chart">
                <Chart options={chartOptions} series={chartSeries} type="area" height={180} />
            </div>
            <style>{`
                .sentiment-trend-card {
                    padding: 1.25rem;
                    margin-top: 1.5rem;
                }
                .trend-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 1rem;
                }
                .trend-header h3 {
                    font-size: 1rem;
                    font-weight: 600;
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    margin: 0;
                }
                .trend-badge {
                    display: flex;
                    align-items: center;
                    gap: 0.4rem;
                    padding: 0.35rem 0.75rem;
                    border-radius: 20px;
                    font-size: 0.75rem;
                    font-weight: 600;
                    text-transform: uppercase;
                }
                .trend-improving {
                    background: rgba(16, 185, 129, 0.1);
                    color: #10b981;
                    border: 1px solid rgba(16, 185, 129, 0.3);
                }
                .trend-declining {
                    background: rgba(239, 68, 68, 0.1);
                    color: #ef4444;
                    border: 1px solid rgba(239, 68, 68, 0.3);
                }
                .trend-stable {
                    background: rgba(107, 114, 128, 0.1);
                    color: #9ca3af;
                    border: 1px solid rgba(107, 114, 128, 0.3);
                }
                .sentiment-trend-loading {
                    padding: 1.5rem;
                }
                .skeleton-chart {
                    height: 180px;
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
        </motion.div>
    )
}
