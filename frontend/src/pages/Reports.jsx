import { useState, useEffect } from 'react'
import { Eye, Download, Trash2 } from 'lucide-react'
import { reportsApi } from '../utils/api'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import { useNavigate, Link } from 'react-router-dom'

export default function Reports() {
    const [reports, setReports] = useState([])
    const [loading, setLoading] = useState(true)
    const navigate = useNavigate()

    useEffect(() => {
        fetchReports()
    }, [])

    const fetchReports = async () => {
        try {
            const res = await reportsApi.list()
            setReports(res.data?.reports || [])
        } catch (error) {
            toast.error('Failed to load reports')
        } finally {
            setLoading(false)
        }
    }

    const handleDownload = async (reportId, filename) => {
        try {
            const res = await reportsApi.download(reportId)
            const url = window.URL.createObjectURL(new Blob([res.data]))
            const link = document.createElement('a')
            link.href = url
            link.setAttribute('download', filename || `${reportId}.pdf`)
            document.body.appendChild(link)
            link.click()
            link.remove()
            window.URL.revokeObjectURL(url)
            toast.success('Report downloaded!')
        } catch (error) {
            toast.error('Download failed')
        }
    }

    const handleDelete = async (reportId) => {
        if (!confirm('Delete this report?')) return
        try {
            await reportsApi.delete(reportId)
            toast.success('Report deleted')
            fetchReports()
        } catch (error) {
            toast.error('Failed to delete report')
        }
    }

    return (
        <div className="reports-section-v2">
            <header className="page-header">
                <h1 className="outfit">📑 Intelligence Vault</h1>
                <p>Access your historical equity structural breakdowns</p>
            </header>

            {loading ? (
                <div className="loading-v2">
                    <div className="spinner-violet"></div>
                    <p>Accessing Secure Vault...</p>
                </div>
            ) : reports.length === 0 ? (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="glass-card empty-vault"
                >
                    <span className="empty-icon">�</span>
                    <h3 className="outfit">Vault Currently Empty</h3>
                    <p>Run a full structural analysis to populate your intelligence vault.</p>
                    <Link to="/analysis" className="btn-primary" style={{ textDecoration: 'none', display: 'inline-block', marginTop: '1.5rem' }}>
                        Initiate Analysis
                    </Link>
                </motion.div>
            ) : (
                <div className="reports-grid-v2">
                    {reports.map((report, i) => (
                        <motion.div
                            key={report.id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.05 }}
                            className="glass-card report-card-v2"
                        >
                            <div className="report-header-v2">
                                <span className="report-ticker-v2">{report.ticker}</span>
                                <span className="report-badge-v2">Full Report</span>
                            </div>
                            <div className="report-meta-v2">
                                <div className="meta-item">
                                    <span className="meta-label">Generated</span>
                                    <span className="meta-val">{new Date(report.created_at).toLocaleDateString()}</span>
                                </div>
                                <div className="meta-item">
                                    <span className="meta-label">Payload</span>
                                    <span className="meta-val">{report.file_size_kb} KB</span>
                                </div>
                            </div>
                            <div className="report-actions-v2">
                                <button
                                    onClick={() => navigate('/analysis', { state: { reportId: report.id } })}
                                    className="btn-primary-v2"
                                >
                                    <Eye size={18} /> View Analysis
                                </button>
                                <button
                                    onClick={() => handleDownload(report.id, report.filename)}
                                    className="btn-secondary-v2"
                                    title="Download PDF"
                                >
                                    <Download size={18} />
                                </button>
                                <button
                                    onClick={() => handleDelete(report.id)}
                                    className="btn-trash-v2"
                                    title="Delete Report"
                                >
                                    <Trash2 size={18} />
                                </button>
                            </div>
                        </motion.div>
                    ))}
                </div>
            )
            }

            <style>{`
                .reports-section-v2 {
                    display: flex;
                    flex-direction: column;
                    gap: 2.5rem;
                }
                .loading-v2 {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: 1.5rem;
                    padding: 5rem;
                }
                .empty-vault {
                    text-align: center;
                    padding: 5rem;
                    max-width: 600px;
                    margin: 0 auto;
                }
                .empty-icon { font-size: 3rem; margin-bottom: 1rem; display: block; }
                
                .reports-grid-v2 {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                    gap: 1.5rem;
                }
                .report-card-v2 {
                    padding: 1.5rem;
                    display: flex;
                    flex-direction: column;
                    gap: 1.5rem;
                }
                .report-header-v2 {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .report-ticker-v2 {
                    font-size: 1.5rem;
                    font-weight: 800;
                    color: white;
                    font-family: 'Outfit', sans-serif;
                }
                .report-badge-v2 {
                    background: rgba(124, 58, 237, 0.1);
                    color: var(--accent-secondary);
                    padding: 0.25rem 0.75rem;
                    border-radius: 999px;
                    font-size: 0.75rem;
                    font-weight: 700;
                    text-transform: uppercase;
                }
                .report-meta-v2 {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 1rem;
                    padding: 1rem;
                    background: rgba(255, 255, 255, 0.02);
                    border-radius: 8px;
                }
                .meta-item {
                    display: flex;
                    flex-direction: column;
                    gap: 0.1rem;
                }
                .meta-label {
                    font-size: 0.7rem;
                    color: var(--text-muted);
                    text-transform: uppercase;
                }
                .meta-val {
                    font-size: 0.9rem;
                    font-weight: 600;
                    color: var(--text-dim);
                }
                .report-actions-v2 {
                    display: flex;
                    gap: 0.75rem;
                }
                .btn-primary-v2 {
                    flex: 2;
                    padding: 0.75rem;
                    background: var(--accent-primary);
                    border: none;
                    border-radius: 8px;
                    color: white;
                    font-weight: 600;
                    cursor: pointer;
                    transition: var(--transition-smooth);
                    display: flex; align-items: center; justify-content: center; gap: 0.5rem;
                    white-space: nowrap;
                }
                .btn-primary-v2:hover {
                    box-shadow: 0 0 15px var(--accent-glow);
                    transform: translateY(-2px);
                }
                .btn-secondary-v2 {
                    flex: 1;
                    padding: 0.75rem;
                    background: rgba(255, 255, 255, 0.05);
                    border: 1px solid var(--glass-border);
                    border-radius: 8px;
                    color: white;
                    cursor: pointer;
                    transition: var(--transition-smooth);
                }
                .btn-secondary-v2:hover {
                    background: rgba(255, 255, 255, 0.1);
                }
                .btn-trash-v2 {
                    padding: 0.75rem;
                    background: rgba(239, 68, 68, 0.1);
                    border: 1px solid rgba(239, 68, 68, 0.2);
                    border-radius: 8px;
                    cursor: pointer;
                    transition: var(--transition-smooth);
                    color: #ef4444;
                    display: flex; align-items: center; justify-content: center;
                }
                .btn-trash-v2:hover {
                    background: #ef4444;
                    color: white;
                    box-shadow: 0 0 10px rgba(239, 68, 68, 0.4);
                }
            `}</style>
        </div >
    )
}

