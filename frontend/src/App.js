import React, { createContext, useContext, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import {
  CssBaseline,
  useMediaQuery,
  ThemeProvider,
  createTheme,
} from '@mui/material';
import Navigation from './Navigation';
import StatisticsPage from './StatisticsPage';
import HostsPage from './HostsPage';
import TodayUpdatesPage from './TodayUpdatesPage';

// Theme Context
const ThemeContext = createContext();

// Custom hook to use theme context
const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

// Theme provider component
const CustomThemeProvider = ({ children }) => {
  // Safely handle useMediaQuery in test environment
  let prefersDarkMode = false;
  try {
    prefersDarkMode = useMediaQuery('(prefers-color-scheme: dark)');
  } catch (error) {
    // Fallback for test environment
    prefersDarkMode = false;
  }
  
  // Initialize theme mode from localStorage or system preference
  const [mode, setMode] = useState(() => {
    const savedMode = localStorage.getItem('themeMode');
    return savedMode || (prefersDarkMode ? 'dark' : 'light');
  });

  // Create Material-UI theme based on mode
  const theme = createTheme({
    palette: {
      mode,
      ...(mode === 'light'
        ? {
            // Light theme colors
            primary: {
              main: '#1976d2',
            },
          }
        : {
            // Dark theme colors
            primary: {
              main: '#90caf9',
            },
          }),
    },
  });

  // Toggle theme mode
  const toggleTheme = () => {
    const newMode = mode === 'light' ? 'dark' : 'light';
    setMode(newMode);
    localStorage.setItem('themeMode', newMode);
  };

  const value = {
    mode,
    toggleTheme,
    theme,
  };

  return (
    <ThemeContext.Provider value={value}>
      <ThemeProvider theme={theme}>
        {children}
      </ThemeProvider>
    </ThemeContext.Provider>
  );
};

function App() {
  const { mode, toggleTheme } = useTheme();

  return (
    <Router>
      <CssBaseline />
      <Navigation mode={mode} toggleTheme={toggleTheme} />
      <Routes>
        <Route path="/" element={<Navigate to="/statistics" replace />} />
        <Route path="/statistics" element={<StatisticsPage />} />
        <Route path="/today-updates" element={<TodayUpdatesPage />} />
        <Route path="/hosts" element={<HostsPage />} />
      </Routes>
    </Router>
  );
}

// Wrapped App component with theme provider
function AppWithTheme() {
  return (
    <CustomThemeProvider>
      <App />
    </CustomThemeProvider>
  );
}

export default AppWithTheme;
