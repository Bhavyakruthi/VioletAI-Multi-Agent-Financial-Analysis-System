
import React from 'react'
import Chart from 'react-apexcharts'
import { motion } from 'framer-motion'
import { TrendingUp, AlertCircle } from 'lucide-react'

export default function ForecastChart({ data, ticker }) {
    if (!data || data.length === 0) {
        return (
            <div className="chart-placeholder glass-card">
                <AlertCircle size={32} className="text-muted" />
                <p>No forecast data available</p>
            </div>
        )
    }

    // Prophet data: date, yhat (prediction), yhat_lower (lower bound), yhat_upper (upper bound)

    // Series 1: The Confidence Interval (Range Area)
    // We construct this as a range chart or use two lines?
    // ApexCharts "rangeArea" is best for confidence intervals
    const series = [
        {
            name: 'Prediction',
            type: 'line',
            data: data.map(d => ({
                x: new Date(d.date),
                y: d.yhat
            }))
        },
        {
            name: 'Confidence Interval',
            type: 'rangeArea',
            data: data.map(d => ({
                x: new Date(d.date),
                y: [d.yhat_lower, d.yhat_upper]
            }))
        }
    ]

    const options = {
        chart: {
            height: 350,
            type: 'rangeArea', // Primary type
            background: 'transparent',
            toolbar: { show: false },
            animations: { enabled: true }
        },
        colors: ['#7c3aed', '#a855f7'], // Prediction line, Interval fill
        stroke: {
            curve: 'smooth',
            width: [3, 0], // Line width for prediction, 0 for range border
        },
        fill: {
            type: ['solid', 'solid'],
            opacity: [1, 0.3], // High opacity line, low opacity interval
        },
        dataLabels: { enabled: false },
        theme: { mode: 'dark' },
        xaxis: {
            type: 'datetime',
            tooltip: { enabled: false },
            axisBorder: { show: false },
            axisTicks: { show: false }
        },
        yaxis: {
            labels: {
                formatter: (val) => val.toFixed(2)
            }
        },
        grid: {
            borderColor: 'rgba(255,255,255,0.05)',
            strokeDashArray: 4,
        },
        tooltip: {
            shared: true,
            intersect: false,
            theme: 'dark',
            x: { format: 'dd MMM yyyy' }
        },
        legend: {
            position: 'top',
            horizontalAlign: 'right'
        }
    }

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            className="forecast-chart-container glass-card"
        >
            <div className="chart-header-simple">
                <h4 className="outfit"><TrendingUp size={18} className="icon-accent" /> AI Price Prediction</h4>
                <span className="ticker-badge-sm">{ticker}</span>
            </div>

            <div className="chart-body">
                <Chart
                    options={options}
                    series={series}
                    type="rangeArea"
                    height={320}
                />
            </div>

            <style>{`
        .forecast-chart-container {
            padding: 1.5rem;
            margin: 1.5rem 0;
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            background: linear-gradient(180deg, rgba(124, 58, 237, 0.05) 0%, rgba(0,0,0,0) 100%);
        }
        .chart-header-simple {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid var(--glass-border);
        }
        .chart-header-simple h4 {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin: 0;
            color: var(--text-main);
        }
        .ticker-badge-sm {
            font-size: 0.75rem;
            background: rgba(255,255,255,0.1);
            padding: 0.2rem 0.6rem;
            border-radius: 12px;
            color: var(--text-muted);
        }
      `}</style>
        </motion.div>
    )
}
