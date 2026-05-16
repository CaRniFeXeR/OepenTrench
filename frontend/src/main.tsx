import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { createHashRouter, RouterProvider } from 'react-router-dom'
import './index.css'

import { DashboardPage } from './pages/DashboardPage'
import { GeoJsonDemoPage } from './pages/GeoJsonDemoPage'
import { MapPage } from './pages/MapPage'
import { OnlineLearningPage } from './pages/OnlineLearningPage'
import { ProjectDetailPage } from './pages/ProjectDetailPage'

const router = createHashRouter([
  { path: '/', element: <DashboardPage /> },
  { path: '/online-learning', element: <OnlineLearningPage /> },
  { path: '/projects/:projectId', element: <ProjectDetailPage /> },
  { path: '/map', element: <MapPage /> },
  { path: '/geojson-demo', element: <GeoJsonDemoPage /> },
])

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>,
)
