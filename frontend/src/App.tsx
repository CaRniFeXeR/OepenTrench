import { BrowserRouter, Route, Routes } from 'react-router-dom';

import { DashboardPage } from './pages/DashboardPage';
import { MapPage } from './pages/MapPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/map" element={<MapPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
