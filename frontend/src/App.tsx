import { BrowserRouter, Route, Routes } from 'react-router-dom';

import { DashboardPage } from './pages/DashboardPage';
import { GeoJsonDemoPage } from './pages/GeoJsonDemoPage';
import { MapPage } from './pages/MapPage';
import { ProjectDetailPage } from './pages/ProjectDetailPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
        <Route path="/map" element={<MapPage />} />
        <Route path="/geojson-demo" element={<GeoJsonDemoPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
