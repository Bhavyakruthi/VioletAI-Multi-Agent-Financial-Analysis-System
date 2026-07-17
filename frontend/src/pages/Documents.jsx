import { useState, useEffect, useRef } from 'react'
import { documentsApi } from '../utils/api'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'

export default function Documents() {
    const [documents, setDocuments] = useState([])
    const [loading, setLoading] = useState(true)
    const [uploading, setUploading] = useState(false)
    const [searchQuery, setSearchQuery] = useState('')
    const [searchResults, setSearchResults] = useState([])
    const [searching, setSearching] = useState(false)
    const fileInputRef = useRef(null)

    useEffect(() => {
        fetchDocuments()
    }, [])

    const fetchDocuments = async () => {
        try {
            const res = await documentsApi.list()
            setDocuments(res.data?.documents || [])
        } catch (error) {
            toast.error('Failed to load documents')
        } finally {
            setLoading(false)
        }
    }

    const handleUpload = async (e) => {
        const file = e.target.files[0]
        if (!file) return
        const allowedTypes = ['.pdf', '.docx', '.txt']
        const ext = '.' + file.name.split('.').pop().toLowerCase()
        if (!allowedTypes.includes(ext)) {
            toast.error('Please upload PDF, DOCX, or TXT files only')
            return
        }
        setUploading(true)
        try {
            const res = await documentsApi.upload(file)
            toast.success(`Uploaded ${res.data.filename}`)
            fetchDocuments()
        } catch (error) {
            toast.error('Upload failed: ' + (error.response?.data?.detail || error.message))
        } finally {
            setUploading(false)
            if (fileInputRef.current) fileInputRef.current.value = ''
        }
    }

    const handleDelete = async (docId, filename) => {
        if (!confirm(`Delete "${filename}"?`)) return
        try {
            await documentsApi.delete(docId)
            toast.success('Document deleted')
            fetchDocuments()
        } catch (error) {
            toast.error('Failed to delete document')
        }
    }

    const handleSearch = async (e) => {
        e.preventDefault()
        if (!searchQuery.trim()) return
        setSearching(true)
        try {
            const res = await documentsApi.search(searchQuery)
            setSearchResults(res.data || [])
        } catch (error) {
            toast.error('Search failed')
        } finally {
            setSearching(false)
        }
    }

    const formatBytes = (bytes) => {
        if (bytes < 1024) return bytes + ' B'
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
    }

    return (
        <div className="documents-vault">
            <header className="page-header">
                <h1 className="outfit">📄 Knowledge Library</h1>
                <p>Equip the AI with custom research, earnings reports, and structural data</p>
            </header>

            <div className="doc-controls-grid">
                <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="glass-card upload-card"
                >
                    <h3 className="outfit">Intelligence Influx</h3>
                    <p className="card-subtitle">Upload structural data for RAG context</p>

                    <div className="upload-dropzone" onClick={() => fileInputRef.current?.click()}>
                        <input
                            type="file"
                            ref={fileInputRef}
                            onChange={handleUpload}
                            accept=".pdf,.docx,.txt"
                            style={{ display: 'none' }}
                        />
                        <div className="dropzone-content">
                            {uploading ? (
                                <div className="spinner-violet"></div>
                            ) : (
                                <>
                                    <span className="upload-icon">📁</span>
                                    <span className="upload-text">Click to ingest research</span>
                                    <span className="upload-limit">PDF, DOCX, TXT (Max 50MB)</span>
                                </>
                            )}
                        </div>
                    </div>
                </motion.div>

                <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="glass-card search-card"
                >
                    <h3 className="outfit">Library Query</h3>
                    <p className="card-subtitle">Semantic search across uploaded intelligence</p>

                    <form onSubmit={handleSearch} className="mini-search-form">
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Query knowledge base..."
                            className="mini-input"
                        />
                        <button type="submit" className="btn-search-icon" disabled={searching}>
                            {searching ? '...' : '🔍'}
                        </button>
                    </form>

                    <AnimatePresence>
                        {searchResults.length > 0 && (
                            <motion.div
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: 10 }}
                                className="search-preview-list"
                            >
                                {searchResults.slice(0, 3).map((result, idx) => (
                                    <div key={idx} className="preview-item">
                                        <span className="preview-source">{result.source}</span>
                                        <p className="preview-snippet">{result.content.substring(0, 80)}...</p>
                                    </div>
                                ))}
                            </motion.div>
                        )}
                    </AnimatePresence>
                </motion.div>
            </div>

            <section className="library-section">
                <div className="section-header">
                    <h3 className="outfit">Archived Intelligence ({documents.length})</h3>
                </div>

                {loading ? (
                    <div className="library-loading">
                        <div className="spinner-violet"></div>
                    </div>
                ) : documents.length === 0 ? (
                    <div className="empty-library">
                        <span className="empty-ico">�</span>
                        <p>No intelligence files archived yet.</p>
                    </div>
                ) : (
                    <div className="glass-card library-table-container">
                        <table className="premium-table">
                            <thead>
                                <tr>
                                    <th>Classification</th>
                                    <th>Format</th>
                                    <th>Payload</th>
                                    <th>Fragments</th>
                                    <th>Ingested On</th>
                                    <th className="text-right">Operation</th>
                                </tr>
                            </thead>
                            <tbody>
                                {documents.map((doc, idx) => (
                                    <motion.tr
                                        key={doc.id}
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        transition={{ delay: idx * 0.05 }}
                                    >
                                        <td className="font-bold white">{doc.filename}</td>
                                        <td><span className="format-badge">{doc.file_type}</span></td>
                                        <td className="text-dim">{formatBytes(doc.size_bytes)}</td>
                                        <td className="text-violet">{doc.chunk_count}</td>
                                        <td className="text-dim">{new Date(doc.uploaded_at).toLocaleDateString()}</td>
                                        <td className="text-right">
                                            <button
                                                onClick={() => handleDelete(doc.id, doc.filename)}
                                                className="btn-trash-mini"
                                            >
                                                🗑️
                                            </button>
                                        </td>
                                    </motion.tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </section>

            <style>{`
                .documents-vault {
                    display: flex;
                    flex-direction: column;
                    gap: 2.5rem;
                }
                .doc-controls-grid {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 1.5rem;
                }
                .upload-card, .search-card {
                    padding: 2rem;
                }
                .card-subtitle {
                    font-size: 0.85rem;
                    color: var(--text-muted);
                    margin-bottom: 1.5rem;
                }
                
                /* Upload Zone */
                .upload-dropzone {
                    border: 2px dashed var(--glass-border);
                    border-radius: 12px;
                    padding: 2.5rem;
                    text-align: center;
                    cursor: pointer;
                    transition: var(--transition-smooth);
                    background: rgba(255,255,255,0.01);
                }
                .upload-dropzone:hover {
                    border-color: var(--accent-primary);
                    background: rgba(124, 58, 237, 0.05);
                }
                .upload-icon { font-size: 2rem; display: block; margin-bottom: 0.5rem; }
                .upload-text { display: block; font-weight: 600; color: white; }
                .upload-limit { font-size: 0.75rem; color: var(--text-muted); margin-top: 0.25rem; }

                /* Mini Search */
                .mini-search-form {
                    display: flex;
                    gap: 0.75rem;
                }
                .mini-input {
                    flex: 1;
                    background: var(--bg-dark-800);
                    border: 1px solid var(--glass-border);
                    border-radius: 8px;
                    padding: 0.75rem 1rem;
                    color: white;
                    font-size: 0.95rem;
                }
                .mini-input:focus {
                    outline: none;
                    border-color: var(--accent-primary);
                }
                .btn-search-icon {
                    padding: 0.75rem;
                    background: var(--bg-dark-800);
                    border: 1px solid var(--glass-border);
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 0.2s;
                }
                .btn-search-icon:hover {
                    background: var(--accent-primary);
                }

                .search-preview-list {
                    margin-top: 1.5rem;
                    display: flex;
                    flex-direction: column;
                    gap: 0.75rem;
                }
                .preview-item {
                    padding: 0.6rem 1rem;
                    background: rgba(255,255,255,0.02);
                    border-radius: 6px;
                    font-size: 0.8rem;
                }
                .preview-source { color: var(--accent-secondary); font-weight: 700; display: block; }
                .preview-snippet { color: var(--text-dim); margin-top: 0.1rem; }

                /* Table Styles */
                .library-table-container {
                    padding: 0 !important;
                    overflow: hidden;
                }
                .premium-table {
                    width: 100%;
                    border-collapse: collapse;
                }
                .premium-table th {
                    text-align: left;
                    padding: 1.25rem;
                    background: rgba(255,255,255,0.02);
                    color: var(--text-muted);
                    font-size: 0.75rem;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                }
                .premium-table td {
                    padding: 1.25rem;
                    border-bottom: 1px solid rgba(255,255,255,0.03);
                    font-size: 0.9rem;
                    color: var(--text-dim);
                }
                .premium-table tr:hover {
                    background: rgba(124, 58, 237, 0.03);
                }
                .format-badge {
                    background: rgba(124, 58, 237, 0.1);
                    color: var(--accent-secondary);
                    padding: 0.2rem 0.5rem;
                    border-radius: 4px;
                    font-size: 0.7rem;
                    font-weight: 700;
                }
                .text-violet { color: var(--accent-secondary); font-weight: 600; }
                .text-right { text-align: right; }
                .btn-trash-mini {
                    background: transparent;
                    border: none;
                    cursor: pointer;
                    filter: grayscale(1);
                    transition: all 0.2s;
                    font-size: 1rem;
                }
                .btn-trash-mini:hover {
                    filter: grayscale(0);
                    transform: scale(1.2);
                }
            `}</style>
        </div>
    )
}
