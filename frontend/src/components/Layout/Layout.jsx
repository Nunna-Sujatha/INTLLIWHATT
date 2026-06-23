import Sidebar from './Sidebar';
import { useApp } from '../../context/AppContext';

const Layout = ({ children }) => {
    const { sidebarOpen } = useApp();

    return (
        <div className="min-h-screen">
            <Sidebar />
            <main className={`main-content ${!sidebarOpen ? 'collapsed' : ''}`}>
                {children}
            </main>
        </div>
    );
};

export default Layout;
