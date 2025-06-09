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
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button,
  Chip,
  Stack,
} from '@mui/material';
import StorageIcon from '@mui/icons-material/Storage';
import DnsIcon from '@mui/icons-material/Dns';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import FilterListIcon from '@mui/icons-material/FilterList';
import ClearIcon from '@mui/icons-material/Clear';

// Import telemetry
import {
  initializeTelemetry,
  trackUserFlow,
  trackApiCall,
  trackComponentRender,
  trackError,
  isTelemetryEnabled,
  getTelemetryStatus,
} from './telemetry';

const API_BASE = '/api';

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
  
  // Filter state
  const [filters, setFilters] = useState({
    dateFrom: '',
    dateTo: '',
    os: '',
    package: ''
  });
  
  // Available OS options for dropdown (populated from data)
  const [availableOSes, setAvailableOSes] = useState([]);

  // Initialize telemetry on app startup
  useEffect(() => {
    try {
      initializeTelemetry();
      console.log('Telemetry initialized for FleetPulse frontend');
    } catch (error) {
      console.error('Failed to initialize telemetry:', error);
    }
  }, []);

  useEffect(() => {
    const span = trackUserFlow('app_initialization', 'fetch_hosts', {
      'hosts.count': 0,
    });
    
    axios.get(`${API_BASE}/hosts`)
      .then(res => {
        const hostsData = Array.isArray(res.data.hosts) ? res.data.hosts : [];
        setHosts(hostsData);
        span.setAttributes({
          'hosts.count': hostsData.length,
          'operation.success': true,
        });
        span.end();
      })
      .catch((err) => {
        console.error('Error fetching hosts:', err);
        setHosts([]); // Defensive: always set to array
        trackError(err, {
          'operation': 'fetch_hosts',
          'api.endpoint': `${API_BASE}/hosts`,
        });
        span.setAttributes({
          'operation.success': false,
          'error.message': err.message,
        });
        span.end();
      });
  }, []);

  const fetchHistory = (host, currentFilters = filters) => {
    const span = trackUserFlow('host_selection', 'fetch_history', {
      'host.name': host,
      'filters.applied': Object.values(currentFilters).some(v => v),
    });
    
    setLoading(true);
    setSelectedHost(host);
    
    // Build query parameters
    const params = new URLSearchParams();
    if (currentFilters.dateFrom) params.append('date_from', currentFilters.dateFrom);
    if (currentFilters.dateTo) params.append('date_to', currentFilters.dateTo);
    if (currentFilters.os) params.append('os', currentFilters.os);
    if (currentFilters.package) params.append('package', currentFilters.package);
    
    const queryString = params.toString();
    const url = `${API_BASE}/history/${host}${queryString ? `?${queryString}` : ''}`;
    
    const apiSpan = trackApiCall('GET', url, {
      'host.name': host,
      'query.params': queryString,
    });
    
    axios.get(url)
      .then(res => {
        setHistory(res.data);
        // Extract unique OS values for dropdown
        const osSet = new Set(res.data.map(item => item.os));
        setAvailableOSes(Array.from(osSet).sort());
        
        span.setAttributes({
          'operation.success': true,
          'history.count': res.data.length,
          'os.count': osSet.size,
        });
        apiSpan.setAttributes({
          'operation.success': true,
          'response.count': res.data.length,
        });
        span.end();
        apiSpan.end();
      })
      .catch(err => {
        console.error('Error fetching history:', err);
        setHistory([]);
        setAvailableOSes([]);
        
        trackError(err, {
          'operation': 'fetch_history',
          'host.name': host,
          'api.endpoint': url,
        });
        
        span.setAttributes({
          'operation.success': false,
          'error.message': err.message,
        });
        apiSpan.setAttributes({
          'operation.success': false,
          'error.message': err.message,
        });
        span.end();
        apiSpan.end();
      })
      .finally(() => setLoading(false));
  };
  
  const handleFilterChange = (filterName, value) => {
    const span = trackUserFlow('filtering', 'change_filter', {
      'filter.name': filterName,
      'filter.value': value,
      'has_selected_host': Boolean(selectedHost),
    });
    
    const newFilters = { ...filters, [filterName]: value };
    setFilters(newFilters);
    
    // If a host is selected, re-fetch with new filters
    if (selectedHost) {
      fetchHistory(selectedHost, newFilters);
    }
    
    span.end();
  };
  
  const clearFilters = () => {
    const span = trackUserFlow('filtering', 'clear_filters', {
      'has_selected_host': Boolean(selectedHost),
      'active_filters_count': Object.values(filters).filter(v => v).length,
    });
    
    const emptyFilters = {
      dateFrom: '',
      dateTo: '',
      os: '',
      package: ''
    };
    setFilters(emptyFilters);
    
    // If a host is selected, re-fetch without filters
    if (selectedHost) {
      fetchHistory(selectedHost, emptyFilters);
    }
    
    span.end();
  };
  
  const hasActiveFilters = filters.dateFrom || filters.dateTo || filters.os || filters.package;

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
                  onClick={() => {
                    // Clear filters when switching hosts
                    const emptyFilters = {
                      dateFrom: '',
                      dateTo: '',
                      os: '',
                      package: ''
                    };
                    setFilters(emptyFilters);
                    fetchHistory(host, emptyFilters);
                  }}
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
                
                {/* Filter Controls */}
                <Paper elevation={1} sx={{ p: 2, mb: 2, backgroundColor: 'background.default' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <FilterListIcon sx={{ mr: 1 }} />
                    <Typography variant="h6">Filters</Typography>
                    {hasActiveFilters && (
                      <Chip 
                        label="Active" 
                        color="primary" 
                        size="small" 
                        sx={{ ml: 1 }}
                      />
                    )}
                  </Box>
                  
                  <Stack spacing={2}>
                    <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
                      <TextField
                        label="From Date"
                        type="date"
                        value={filters.dateFrom}
                        onChange={(e) => handleFilterChange('dateFrom', e.target.value)}
                        InputLabelProps={{ shrink: true }}
                        size="small"
                        sx={{ minWidth: 150 }}
                      />
                      
                      <TextField
                        label="To Date"
                        type="date"
                        value={filters.dateTo}
                        onChange={(e) => handleFilterChange('dateTo', e.target.value)}
                        InputLabelProps={{ shrink: true }}
                        size="small"
                        sx={{ minWidth: 150 }}
                      />
                      
                      <FormControl size="small" sx={{ minWidth: 200 }}>
                        <InputLabel>Operating System</InputLabel>
                        <Select
                          value={filters.os}
                          label="Operating System"
                          onChange={(e) => handleFilterChange('os', e.target.value)}
                        >
                          <MenuItem value="">
                            <em>All</em>
                          </MenuItem>
                          {availableOSes.map((os) => (
                            <MenuItem key={os} value={os}>
                              {os}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                      
                      <TextField
                        label="Package Name"
                        value={filters.package}
                        onChange={(e) => handleFilterChange('package', e.target.value)}
                        size="small"
                        placeholder="Search packages..."
                        sx={{ minWidth: 200 }}
                      />
                    </Stack>
                    
                    <Box>
                      <Button
                        variant="outlined"
                        startIcon={<ClearIcon />}
                        onClick={clearFilters}
                        disabled={!hasActiveFilters}
                        size="small"
                      >
                        Clear Filters
                      </Button>
                    </Box>
                  </Stack>
                </Paper>
                
                {loading ? (
                  <CircularProgress />
                ) : (
                  <>
                    {history.length === 0 ? (
                      <Typography variant="body2">
                        {hasActiveFilters 
                          ? "No update history found matching the current filters."
                          : "No update history found for this host."
                        }
                      </Typography>
                    ) : (
                      <>
                        <Box sx={{ mb: 1 }}>
                          <Typography variant="body2" color="text.secondary">
                            Showing {history.length} update{history.length !== 1 ? 's' : ''}
                            {hasActiveFilters && ' (filtered)'}
                          </Typography>
                        </Box>
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
                      </>
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
