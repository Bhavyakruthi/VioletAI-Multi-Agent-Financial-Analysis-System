import { useState, useEffect } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';

export default function Navbar() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const [theme, setTheme] = useState(() => localStorage.getItem('violet-theme') || 'dark');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('violet-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    const themes = ['dark', 'light', 'oled'];
    const nextIndex = (themes.indexOf(theme) + 1) % themes.length;
    setTheme(themes[nextIndex]);
  };

  const handleSignOut = async () => {
    const { error } = await signOut();
    if (error) {
      toast.error(error.message);
    } else {
      toast.success('Signed out');
      navigate('/login');
    }
  };

  const navItems = [
    { path: '/dashboard', label: 'Dashboard' },
    { path: '/analysis', label: 'Analysis' },
    { path: '/compare', label: 'Compare' },
    { path: '/documents', label: 'Documents' },
    { path: '/chat', label: 'Chat' },
    { path: '/reports', label: 'Reports' },
    { path: '/schedules', label: 'Automation' },
  ];

  return (
    <nav className="premium-navbar">
      <div className="nav-container">
        <Link to="/" className="nav-logo">
          <motion.span
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="logo-text"
          >
            VIOLET<span className="logo-accent">AI</span>
          </motion.span>
        </Link>

        <div className="nav-links">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`nav-link ${location.pathname === item.path ? 'active' : ''}`}
            >
              {item.label}
              {location.pathname === item.path && (
                <motion.div
                  layoutId="nav-underline"
                  className="nav-underline"
                />
              )}
            </Link>
          ))}
          <button onClick={toggleTheme} className="theme-toggle-btn" title="Toggle Theme">
            {theme === 'dark' ? '🌖' : theme === 'light' ? '☀️' : '🌑'}
          </button>
        </div>

        <div className="nav-user">
          <div className="user-badge">
            <span className="user-initial">{user?.email?.[0].toUpperCase()}</span>
            <span className="user-email">{user?.email?.split('@')[0]}</span>
          </div>
          <button onClick={handleSignOut} className="nav-signout">
            Sign Out
          </button>
        </div>
      </div>

      <style>{`
        .premium-navbar {
          height: 70px;
          background: var(--nav-bg);
          backdrop-filter: blur(25px);
          -webkit-backdrop-filter: blur(25px);
          border-bottom: 1px solid var(--nav-border);
          position: sticky;
          top: 0;
          z-index: 1000;
          display: flex;
          align-items: center;
        }

        .nav-container {
          max-width: 1400px;
          margin: 0 auto;
          width: 100%;
          padding: 0 2rem;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .nav-logo {
          text-decoration: none;
        }

        .logo-text {
          font-family: 'Outfit', sans-serif;
          font-size: 1.5rem;
          font-weight: 700;
          letter-spacing: 0.1rem;
          color: var(--text-main);
        }

        .logo-accent {
          color: var(--accent-primary);
        }

        .nav-links {
          display: flex;
          gap: 2.5rem;
          position: relative;
        }

        .nav-link {
          text-decoration: none;
          color: var(--text-dim);
          font-weight: 500;
          font-size: 0.95rem;
          transition: var(--transition-smooth);
          position: relative;
          padding: 0.5rem 0;
        }

        .nav-link:hover {
          color: var(--text-main);
        }

        .nav-link.active {
          color: var(--text-main);
        }

        .nav-underline {
          position: absolute;
          bottom: -2px;
          left: 0;
          right: 0;
          height: 2px;
          background: var(--accent-primary);
          box-shadow: 0 0 10px var(--accent-glow);
        }

        .nav-user {
          display: flex;
          align-items: center;
          gap: 1.5rem;
        }

        .user-badge {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 0.5rem 1rem;
          background: rgba(124, 58, 237, 0.1);
          border: 1px solid rgba(124, 58, 237, 0.2);
          border-radius: 999px;
        }

        .user-initial {
          width: 24px;
          height: 24px;
          background: var(--accent-primary);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 0.75rem;
          font-weight: 700;
          color: white;
        }

        .user-email {
          color: var(--text-main);
          font-size: 0.875rem;
          font-weight: 500;
        }

        .nav-signout {
          background: transparent;
          border: 1px solid var(--nav-border);
          color: var(--text-dim);
          padding: 0.4rem 1rem;
          border-radius: 8px;
          cursor: pointer;
          font-weight: 600;
          font-size: 0.85rem;
          transition: all 0.3s ease;
        }

        .nav-signout:hover {
          border-color: #ef4444;
          color: #ef4444;
          background: rgba(239, 68, 68, 0.05);
        }

        .theme-toggle-btn {
            background: none;
            border: 1px solid var(--nav-border);
            border-radius: 8px;
            color: var(--text-main);
            padding: 0.4rem 0.8rem;
            cursor: pointer;
            font-size: 1rem;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .theme-toggle-btn:hover {
            background: rgba(124, 58, 237, 0.1);
            border-color: var(--accent-primary);
            transform: rotate(15deg);
        }
      `}</style>
    </nav>
  );
}
