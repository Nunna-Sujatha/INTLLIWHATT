import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AppProvider } from './context/AppContext';
import Layout from './components/Layout/Layout';
import Homepage from './pages/Dashboard';
import Prediction from './pages/Prediction';
import Chatbot from './pages/Chatbot';
import MeterReading from './pages/MeterReading';

function App() {
  return (
    <AppProvider>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Homepage />} />
            <Route path="/prediction" element={<Prediction />} />
            <Route path="/chatbot" element={<Chatbot />} />
            <Route path="/meter-reading" element={<MeterReading />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </AppProvider>
  );
}

export default App;

