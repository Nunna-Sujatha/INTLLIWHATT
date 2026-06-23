import { NavLink, useLocation } from 'react-router-dom';
import {
    LayoutDashboard,
    Zap,
    MessageSquare,
    Camera,
    ChevronLeft,
    ChevronRight,
    Menu,
    X,
    Lightbulb
} from 'lucide-react';
import { useApp } from '../../context/AppContext';

const navItems = [
    { path: '/', icon: LayoutDashboard, label: 'Home' },
    { path: '/prediction', icon: Zap, label: 'Bill Prediction' },
    { path: '/chatbot', icon: MessageSquare, label: 'AI Assistant' },
    { path: '/meter-reading', icon: Camera, label: 'Meter Reading' },
];

const Sidebar = () => {
    const { sidebarOpen, setSidebarOpen } = useApp();
    const location = useLocation();

    return (
        <>
            {/* Mobile overlay */}
            {sidebarOpen && (
                <div
                    className="sidebar-overlay md:hidden"
                    onClick={() => setSidebarOpen(false)}
                />
            )}

            {/* Mobile menu button */}
            <button
                className="mobile-menu-btn"
                onClick={() => setSidebarOpen(!sidebarOpen)}
                aria-label="Toggle menu"
            >
                {sidebarOpen ? <X size={22} /> : <Menu size={22} />}
            </button>

            {/* Sidebar */}
            <aside className={`sidebar ${sidebarOpen ? 'open' : 'collapsed'}`}>
                {/* Desktop Toggle Button */}
                <button
                    className="sidebar-toggle"
                    onClick={() => setSidebarOpen(!sidebarOpen)}
                    aria-label={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
                >
                    {sidebarOpen ? <ChevronLeft size={16} /> : <ChevronRight size={16} />}
                </button>

                {/* Logo */}
                <div className="sidebar-header">
                    <div className="sidebar-logo">
                        <div className="logo-icon">
                            <Lightbulb className="text-white" size={22} />
                        </div>
                        <div className="logo-text">
                            <h1 className="text-lg font-semibold text-white">
  IntelliWatt
</h1>
<p className="text-xs text-slate-400">
  AI-Powered Energy Intelligence
</p>

                        </div>
                    </div>
                </div>

                {/* Navigation */}
                <nav className="sidebar-nav">
                    <div className="nav-section-title">
                        <span>Menu</span>
                    </div>

                    <div className="nav-items">
                        {navItems.map((item) => {
                            const Icon = item.icon;
                            const isActive = location.pathname === item.path;

                            return (
                                <NavLink
                                    key={item.path}
                                    to={item.path}
                                    className={`nav-item ${isActive ? 'active' : ''}`}
                                    onClick={() => window.innerWidth < 768 && setSidebarOpen(false)}
                                    title={!sidebarOpen ? item.label : ''}
                                >
                                    <div className="nav-icon">
                                        <Icon size={20} />
                                    </div>
                                    <span className="nav-label">{item.label}</span>
                                    {isActive && <div className="nav-indicator" />}
                                </NavLink>
                            );
                        })}
                    </div>
                </nav>

                {/* Footer */}
                <div className="sidebar-footer">
                    <div className="footer-card">
                        <div className="footer-icon">
                            <Zap size={16} className="text-white" />
                        </div>
                        <div className="footer-text">
                            <p className="footer-title">Save Energy</p>
                            <p className="footer-subtitle">Tips Available</p>
                        </div>
                    </div>
                </div>
            </aside>
        </>
    );
};

export default Sidebar;