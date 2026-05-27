import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Orders from './pages/Orders';
import DesignCanvas from './pages/DesignCanvas';
import PrintQueue from './pages/PrintQueue';
import CutQueue from './pages/CutQueue';
import Customers from './pages/Customers';
import Materials from './pages/Materials';
import Reports from './pages/Reports';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="orders" element={<Orders />} />
          <Route path="design" element={<DesignCanvas />} />
          <Route path="print-queue" element={<PrintQueue />} />
          <Route path="cut-queue" element={<CutQueue />} />
          <Route path="customers" element={<Customers />} />
          <Route path="materials" element={<Materials />} />
          <Route path="reports" element={<Reports />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
