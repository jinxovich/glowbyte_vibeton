import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Calendar from './pages/Calendar';
import History from './pages/History';
import Metrics from './pages/Metrics';
import Train from './pages/Train';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/calendar" element={<Calendar />} />
          <Route path="/history" element={<History />} />
          <Route path="/metrics" element={<Metrics />} />
          <Route path="/train" element={<Train />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
