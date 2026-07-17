
import React, { useState, useEffect } from 'react'
import Chart from 'react-apexcharts'
import { motion } from 'framer-motion'
import { Calendar, BarChart2, Activity } from 'lucide-react'

export default function PriceChart({ data, ticker, period = '1y' }) {
    const [chartType, setChartType] = useState('candlestick') // 'candlestick' or 'area'

    if (!data || data.length === 0) {
        return (
            <div className="chart-placeholder glass-card">
                <Activity size={32} className="text-muted" />
                <p>No price history available</p>
            </div>
        )
    }

    // Format data for ApexCharts
    // Candlestick format: [x, [open, high, low, close]]
    // Area format: [x, close]
    const series = [{
        name: 'Price',
        data: data.map(d => ({
            x: new Date(d.date),
            y: chartType === 'candlestick'
                ? [d.open, d.high, d.low, d.close]
                : d.close
        }))
    }]

    const options = {
        chart: {
            type: chartType,
            height: 350,
            background: 'transparent',
            toolbar: {
                show: true,
                tools: {
                    download: false,
                    selection: true,
                    zoom: true,
                    zoomin: true,
                    zoomout: true,
                    pan: true,
                    reset: true
                },
                autoSelected: 'zoom'
            },
            foreColor: '#94a3b8'
        },
        grid: {
            borderColor: 'rgba(255,255,255,0.05)',
            strokeDashArray: 4,
        },
        plotOptions: {
            candlestick: {
                colors: {
                    upward: '#10b981',
                    downward: '#ef4444'
                },
                wick: {
                    useFillColor: true
                }
            }
        },
        stroke: {
            width: chartType === 'area' ? 2 : 1,
            curve: 'smooth'
        },
        fill: {
            type: chartType === 'area' ? 'gradient' : 'solid',
            gradient: {
                shadeIntensity: 1,
                opacityFrom: 0.7,
                opacityTo: 0.1,
                stops: [0, 90, 100]
            }
        },
        colors: ['#7c3aed'], // Primary accent color for Area chart
        xaxis: {
            type: 'datetime',
            tooltip: {
                enabled: true
            },
            axisBorder: { show: false },
            axisTicks: { show: false }
        },
        yaxis: {
            tooltip: {
                enabled: true
            },
            labels: {
                formatter: (val) => val.toFixed(2)
            }
        },
        theme: {
            mode: 'dark'
        }
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="price-chart-container glass-card"
        >
            <div className="chart-header">
                <div className="chart-title">
                    <span className="ticker-badge">{ticker}</span>
                    <span className="period-badge">{period}</span>
                </div>
                <div className="chart-controls">
                    <button
                        className={`chart-btn ${chartType === 'candlestick' ? 'active' : ''}`}
                        onClick={() => setChartType('candlestick')}
                        title="Candlestick"
                    >
                        <BarChart2 size={16} />
                    </button>
                    <button
                        className={`chart-btn ${chartType === 'area' ? 'active' : ''}`}
                        onClick={() => setChartType('area')}
                        title="Line"
                    >
                        <Activity size={16} />
                    </button>
                </div>
            </div>

            <div className="chart-body">
                <Chart
                    options={options}
                    series={series}
                    type={chartType}
                    height={350}
                />
            </div>

            <style>{`
        .price-chart-container {
            padding: 1.5rem;
            margin-bottom: 2rem;
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            background: var(--glass-bg);
            backdrop-filter: blur(12px);
        }
        .chart-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }
        .chart-title {
            display: flex;
            gap: 0.75rem;
            align-items: center;
        }
        .ticker-badge {
            font-weight: 700;
            font-size: 1.1rem;
            color: var(--text-main);
        }
        .period-badge {
            font-size: 0.75rem;
            padding: 0.2rem 0.5rem;
            background: rgba(124, 58, 237, 0.1);
            color: var(--accent-primary);
            border-radius: 6px;
            text-transform: uppercase;
            font-weight: 600;
        }
        .chart-controls {
            display: flex;
            gap: 0.5rem;
            background: rgba(0,0,0,0.2);
            padding: 0.25rem;
            border-radius: 8px;
        }
        .chart-btn {
            background: transparent;
            border: none;
            color: var(--text-muted);
            padding: 0.4rem;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .chart-btn:hover {
            color: var(--text-main);
            background: rgba(255,255,255,0.05);
        }
        .chart-btn.active {
            background: var(--bg-dark-800);
            color: var(--accent-primary);
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        .chart-placeholder {
            height: 350px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 1rem;
            color: var(--text-muted);
        }
      `}</style>
        </motion.div>
    )
}
