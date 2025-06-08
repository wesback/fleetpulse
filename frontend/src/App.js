import React, { useEffect, useState, createContext, useContext } from 'react';
import axios from 'axios';
import {
  Container,
  Typography,
  Box,
  Paper,
  List,
  ListItemButton,
  ListItemText,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  AppBar,
  Toolbar,
  CircularProgress,
  CssBaseline,
  Switch,
  FormControlLabel,
  useMediaQuery,
  ThemeProvider,
  createTheme,
} from '@mui/material';
import StorageIcon from '@mui/icons-material/Storage';
import DnsIcon from '@mui/icons-material/Dns';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';

const API_BASE = '';

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
  const [hosts, setHosts] = useState([]);
  const [selectedHost, setSelectedHost] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const { mode, toggleTheme } = useTheme();

  useEffect(() => {
    axios.get(`${API_BASE}/hosts`)
      .then(res => setHosts(Array.isArray(res.data.hosts) ? res.data.hosts : []))
      .catch(() => setHosts([])); // Defensive: always set to array
  }, []);

  const fetchHistory = (host) => {
    setLoading(true);
    setSelectedHost(host);
    axios.get(`${API_BASE}/history/${host}`)
      .then(res => setHistory(res.data))
      .finally(() => setLoading(false));
  };

  return (
    <>
      <CssBaseline />
      <AppBar position="static" sx={{ marginBottom: 4 }}>
        <Toolbar>
          <StorageIcon sx={{ marginRight: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            FleetPulse &mdash; Linux Fleet Package Dashboard
          </Typography>
          <FormControlLabel
            control={
              <Switch
                checked={mode === 'dark'}
                onChange={toggleTheme}
                color="default"
                inputProps={{ 'aria-label': 'dark mode toggle' }}
              />
            }
            label={
              <Box sx={{ display: 'flex', alignItems: 'center', color: 'inherit' }}>
                {mode === 'light' ? <Brightness7Icon /> : <Brightness4Icon />}
              </Box>
            }
            labelPlacement="start"
            sx={{ ml: 1, color: 'inherit' }}
          />
        </Toolbar>
      </AppBar>
      <Container maxWidth="md">
        <Box sx={{ display: 'flex', gap: 4 }}>
          <Paper elevation={2} sx={{ width: 250, minHeight: 400, padding: 2 }}>
            <Typography variant="h6" gutterBottom>
              <DnsIcon sx={{ verticalAlign: 'middle', mr: 1 }} />
              Hosts
            </Typography>
            <List>
              {hosts.length === 0 && (
                <Typography variant="body2">No hosts yet.</Typography>
              )}
              {hosts.map(host =>
                <ListItemButton
                  key={host}
                  selected={selectedHost === host}
                  onClick={() => fetchHistory(host)}
                >
                  <ListItemText primary={host} />
                </ListItemButton>
              )}
            </List>
          </Paper>
          <Box sx={{ flexGrow: 1 }}>
            {selectedHost && (
              <Paper elevation={2} sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Update History for <b>{selectedHost}</b>
                </Typography>
                {loading ? (
                  <CircularProgress />
                ) : (
                  <>
                    {history.length === 0 ? (
                      <Typography variant="body2">
                        No update history found for this host.
                      </Typography>
                    ) : (
                      <TableContainer component={Paper}>
                        <Table size="small">
                          <TableHead>
                            <TableRow>
                              <TableCell>Date</TableCell>
                              <TableCell>OS</TableCell>
                              <TableCell>Package</TableCell>
                              <TableCell>Old Version</TableCell>
                              <TableCell>New Version</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {history.map((rec, i) => (
                              <TableRow key={i}>
                                <TableCell>{rec.update_date}</TableCell>
                                <TableCell>{rec.os}</TableCell>
                                <TableCell>{rec.name}</TableCell>
                                <TableCell>{rec.old_version}</TableCell>
                                <TableCell>{rec.new_version}</TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </TableContainer>
                    )}
                  </>
                )}
              </Paper>
            )}
            {!selectedHost && (
              <Paper elevation={2} sx={{ p: 2 }}>
                <Typography variant="body1" color="text.secondary">
                  Select a host to view its update history.
                </Typography>
              </Paper>
            )}
          </Box>
        </Box>
      </Container>
    </>
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
