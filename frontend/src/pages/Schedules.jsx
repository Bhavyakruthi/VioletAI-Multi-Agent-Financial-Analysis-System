// Schedules Page
// ==========================
// View and manage recurring stock analyses

import React, { useState, useEffect } from 'react'
import { analysisApi } from '../utils/api'
import { Clock, Calendar, Trash2, Plus, Play, CheckCircle2, AlertCircle, Loader2, Search, TrendingUp, BarChart3, Activity } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'

export default function Schedules() {
    const [schedules, setSchedules] = useState([])
    const [loading, setLoading] = useState(true)
    const [showAddModal, setShowAddModal] = useState(false)
    const [newSchedule, setNewSchedule] = useState({ ticker: '', interval: 'daily' })
    const [creating, setCreating] = useState(false)

    useEffect(() => {
        fetchSchedules()
    }, [])

    const fetchSchedules = async () => {
        setLoading(true)
        try {
            const res = await analysisApi.getSchedules()
            setSchedules(res.data)
        } catch (error) {
            console.error("Failed to fetch schedules", error)
            toast.error("Failed to load schedules")
        } finally {
            setLoading(false)
        }
    }

    const handleCreateSchedule = async (e) => {
        e.preventDefault()
        if (!newSchedule.ticker) return

        setCreating(true)
        try {
            await analysisApi.createSchedule(newSchedule)
            toast.success(`Automated analysis scheduled for ${newSchedule.ticker.toUpperCase()}`)
            setShowAddModal(false)
            setNewSchedule({ ticker: '', interval: 'daily' })
            fetchSchedules()
        } catch (error) {
            toast.error("Failed to create schedule")
        } finally {
            setCreating(false)
        }
    }

    const handleDeleteSchedule = async (id) => {
        if (!window.confirm("Are you sure you want to stop this automated analysis?")) return

        try {
            await analysisApi.deleteSchedule(id)
            setSchedules(schedules.filter(s => s.id !== id))
            toast.success("Schedule removed")
        } catch (error) {
            toast.error("Failed to remove schedule")
        }
    }

    const getIntervalLabel = (val) => {
        return {
            hourly: "Every Hour",
            daily: "Every Day (9AM UTC)",
            weekly: "Every Monday"
        }[val] || val
    }

    return (
        <div className="schedules-page">
            <header className="page-header">
                <div className="header-content">
                    <h1><Clock size={28} className="icon-accent" /> Analysis Automation</h1>
                    <p>Configure recurring AI intelligence checkups for your core holdings.</p>
                </div>
                <button className="btn-primary-v2" onClick={() => setShowAddModal(true)}>
                    <Plus size={18} /> New Automation
                </button>
            </header>

            {loading ? (
                <div className="loading-state">
                    <Loader2 className="spinner-icon" size={40} />
                    <p>Loading your automations...</p>
                </div>
            ) : schedules.length === 0 ? (
                <div className="empty-state glass-card">
                    <div className="empty-icon"><Activity size={48} /></div>
                    <h3>No Active Automations</h3>
                    <p>Schedule recurring research reports to be generated automatically.</p>
                    <button className="btn-secondary-v2" onClick={() => setShowAddModal(true)}>
                        <Plus size={18} /> Schedule First Analysis
                    </button>
                </div>
            ) : (
                <div className="schedules-grid">
                    {schedules.map((schedule, idx) => (
                        <motion.div
                            key={schedule.id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: idx * 0.1 }}
                            className="glass-card schedule-card"
                        >
                            <div className="card-header">
                                <div className="ticker-badge">
                                    <TrendingUp size={16} />
                                    <span>{schedule.ticker}</span>
                                </div>
                                <button className="btn-delete-icon" onClick={() => handleDeleteSchedule(schedule.id)}>
                                    <Trash2 size={16} />
                                </button>
                            </div>

                            <div className="schedule-info">
                                <div className="info-item">
                                    <Clock size={14} />
                                    <span>{getIntervalLabel(schedule.interval)}</span>
                                </div>
                                <div className="info-item">
                                    <Calendar size={14} />
                                    <span>Created: {new Date(schedule.created_at).toLocaleDateString()}</span>
                                </div>
                            </div>

                            <div className="last-run-status">
                                <div className="status-label">Last Execution</div>
                                <div className="status-value">
                                    {schedule.last_run ? (
                                        <>
                                            <span className={`status-dot ${schedule.last_status === 'Success' ? 'success' : 'failed'}`}></span>
                                            <span>{new Date(schedule.last_run).toLocaleString()}</span>
                                        </>
                                    ) : (
                                        "Pending First Run"
                                    )}
                                </div>
                            </div>

                            <div className="card-actions">
                                <button className="btn-outline-v2" onClick={() => toast("Feature coming soon: Manual Trigger")}>
                                    <Play size={14} /> Run Now
                                </button>
                                <button className="btn-text-v2" onClick={() => toast("View generated reports in the Reports tab")}>
                                    View Reports
                                </button>
                            </div>
                        </motion.div>
                    ))}
                </div>
            )}

            <AnimatePresence>
                {showAddModal && (
                    <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.9, opacity: 0 }}
                            className="modal-content"
                            onClick={e => e.stopPropagation()}
                        >
                            <div className="modal-header">
                                <h3><Plus size={20} /> New Automation</h3>
                                <button className="btn-close-modal" onClick={() => setShowAddModal(false)}>×</button>
                            </div>
                            <form onSubmit={handleCreateSchedule}>
                                <div className="modal-form-group">
                                    <label>Stock Ticker</label>
                                    <input
                                        type="text"
                                        placeholder="e.g. AAPL, RELIANCE.NS"
                                        value={newSchedule.ticker}
                                        onChange={e => setNewSchedule({ ...newSchedule, ticker: e.target.value.toUpperCase() })}
                                        autoFocus
                                        required
                                    />
                                </div>
                                <div className="modal-form-group">
                                    <label>Interval</label>
                                    <select
                                        value={newSchedule.interval}
                                        onChange={e => setNewSchedule({ ...newSchedule, interval: e.target.value })}
                                    >
                                        <option value="hourly">Hourly (Intense Monitoring)</option>
                                        <option value="daily">Daily (Swing Trading)</option>
                                        <option value="weekly">Weekly (Long Term)</option>
                                    </select>
                                </div>
                                <div className="modal-actions">
                                    <button type="button" className="btn-ghost" onClick={() => setShowAddModal(false)}>Cancel</button>
                                    <button type="submit" className="btn-primary-v2" disabled={creating}>
                                        {creating ? <Loader2 className="spinner-icon" size={18} /> : <CheckCircle2 size={18} />}
                                        Create Automation
                                    </button>
                                </div>
                            </form>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>

            <style>{`
                .schedules-page {
                    max-width: 1200px;
                    margin: 0 auto;
                }
                .page-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 2.5rem;
                }
                .header-content h1 {
                    font-size: 2rem;
                    margin-bottom: 0.5rem;
                    display: flex;
                    align-items: center;
                    gap: 0.75rem;
                }
                .header-content p {
                    color: var(--text-dim);
                }
                .loading-state, .empty-state {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    padding: 5rem;
                    text-align: center;
                    gap: 1.5rem;
                }
                .empty-icon {
                    color: var(--accent-primary);
                    opacity: 0.5;
                }
                .schedules-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
                    gap: 1.5rem;
                }
                .schedule-card {
                    padding: 1.5rem;
                    display: flex;
                    flex-direction: column;
                    gap: 1.25rem;
                }
                .card-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .ticker-badge {
                    background: rgba(124, 58, 237, 0.1);
                    color: var(--accent-primary);
                    padding: 0.4rem 0.8rem;
                    border-radius: 8px;
                    font-weight: 700;
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    border: 1px solid rgba(124, 58, 237, 0.2);
                }
                .btn-delete-icon {
                    background: none;
                    border: none;
                    color: var(--text-muted);
                    cursor: pointer;
                    transition: all 0.2s;
                    padding: 0.5rem;
                    border-radius: 6px;
                }
                .btn-delete-icon:hover {
                    color: #ef4444;
                    background: rgba(239, 68, 68, 0.1);
                }
                .schedule-info {
                    display: flex;
                    flex-direction: column;
                    gap: 0.5rem;
                }
                .info-item {
                    display: flex;
                    align-items: center;
                    gap: 0.75rem;
                    color: var(--text-dim);
                    font-size: 0.9rem;
                }
                .last-run-status {
                    border-top: 1px solid var(--glass-border);
                    padding-top: 1rem;
                    margin-top: 0.5rem;
                }
                .status-label {
                    font-size: 0.75rem;
                    text-transform: uppercase;
                    color: var(--text-muted);
                    margin-bottom: 0.5rem;
                    font-weight: 600;
                }
                .status-value {
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    font-size: 0.85rem;
                    color: var(--text-main);
                }
                .status-dot {
                    width: 8px; height: 8px; border-radius: 50%;
                }
                .status-dot.success { background: #10b981; box-shadow: 0 0 10px #10b981; }
                .status-dot.failed { background: #ef4444; box-shadow: 0 0 10px #ef4444; }

                .card-actions {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-top: auto;
                }
                .btn-outline-v2 {
                    background: transparent;
                    border: 1px solid var(--glass-border);
                    color: var(--text-main);
                    padding: 0.5rem 1rem;
                    border-radius: 8px;
                    font-size: 0.85rem;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                }
                .btn-text-v2 {
                    background: none;
                    border: none;
                    color: var(--accent-primary);
                    font-size: 0.85rem;
                    cursor: pointer;
                }
            `}</style>
        </div>
    )
}
