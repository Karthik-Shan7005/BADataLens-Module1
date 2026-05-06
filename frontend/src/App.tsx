import { Routes, Route, Navigate } from 'react-router-dom';
import Home from './pages/Home';
import ProjectView from './pages/ProjectView';
import './App.css';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/project/:id" element={<ProjectView />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
