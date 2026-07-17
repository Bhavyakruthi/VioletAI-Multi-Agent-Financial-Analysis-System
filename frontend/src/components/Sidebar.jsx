// Sidebar/Navigation Component
// =============================

import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'

export default function Sidebar() {
    const { user, signOut } = useAuth()
    const navigate = useNavigate()

    const handleSignOut = async () => {
        const { error } = await signOut()
        if (error) {
            toast.error(error.message)
        } else {
            toast.success('Signed out')
            navigate('/login')
        }
    }

    const navItems = [
        { path: '/dashboard', icon: '📊', label: 'Dashboard' },
        { path: '/analysis', icon: '📈', label: 'Analysis' },
        { path: '/documents', icon: '📄', label: 'Documents' },
        { path: '/chat', icon: '💬', label: 'Chat' },
        { path: '/reports', icon: '📑', label: 'Reports' },
    ]

    return (
        <aside className="sidebar">
            <div className="sidebar-header">
                <h2>📊 AI Research</h2>
            </div>

            <nav className="sidebar-nav">
                {navItems.map(item => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                    >
                        <span className="nav-icon">{item.icon}</span>
                        <span className="nav-label">{item.label}</span>
                    </NavLink>
                ))}
            </nav>

            <div className="sidebar-footer">
                <div className="user-info">
                    <span className="user-avatar">👤</span>
                    <span className="user-email">{user?.email?.split('@')[0]}</span>
                </div>
                <button onClick={handleSignOut} className="btn-signout">
                    Sign Out
                </button>
            </div>
        </aside>
    )
}
