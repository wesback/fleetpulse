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
  Pagination,
} from '@mui/material';
import StorageIcon from '@mui/icons-material/Storage';
import DnsIcon from '@mui/icons-material/Dns';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import FilterListIcon from '@mui/icons-material/FilterList';
import ClearIcon from '@mui/icons-material/Clear';



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
  
  // Pagination state
  const [pagination, setPagination] = useState({
    page: 1,           // 1-based page number for Material-UI
    pageSize: 25,      // Items per page
    total: 0           // Total number of items
  });
  
  // Available OS options for dropdown (populated from data)
  const [availableOSes, setAvailableOSes] = useState([]);



  useEffect(() => {
    axios.get(`${API_BASE}/hosts`)
      .then(res => {
        const hostsData = Array.isArray(res.data.hosts) ? res.data.hosts : [];
        setHosts(hostsData);
      })
      .catch((err) => {
        console.error('Error fetching hosts:', err);
        setHosts([]); // Defensive: always set to array
      });
  }, []);

  const fetchHistory = (host, currentFilters = filters, currentPage = 1) => {
    setLoading(true);
    setSelectedHost(host);
    
    // Calculate offset based on page and pageSize
    const offset = (currentPage - 1) * pagination.pageSize;
    
    // Build query parameters
    const params = new URLSearchParams();
    if (currentFilters.dateFrom) params.append('date_from', currentFilters.dateFrom);
    if (currentFilters.dateTo) params.append('date_to', currentFilters.dateTo);
    if (currentFilters.os) params.append('os', currentFilters.os);
    if (currentFilters.package) params.append('package', currentFilters.package);
    
    // Add pagination parameters
    params.append('limit', pagination.pageSize.toString());
    params.append('offset', offset.toString());
    
    const queryString = params.toString();
    const url = `${API_BASE}/history/${host}?${queryString}`;
    
    axios.get(url)
      .then(res => {
        const data = res.data;
        setHistory(data.items || []);
        setPagination(prev => ({
          ...prev,
          page: currentPage,
          total: data.total || 0
        }));
        
        // Extract unique OS values for dropdown from current page
        const osSet = new Set((data.items || []).map(item => item.os));
        setAvailableOSes(Array.from(osSet).sort());
      })
      .catch(err => {
        console.error('Error fetching history:', err);
        setHistory([]);
        setAvailableOSes([]);
        setPagination(prev => ({
          ...prev,
          page: currentPage,
          total: 0
        }));
      })
      .finally(() => setLoading(false));
  };
  
  const handleFilterChange = (filterName, value) => {
    const newFilters = { ...filters, [filterName]: value };
    setFilters(newFilters);
    
    // Reset to page 1 when filters change
    setPagination(prev => ({ ...prev, page: 1 }));
    
    // If a host is selected, re-fetch with new filters
    if (selectedHost) {
      fetchHistory(selectedHost, newFilters, 1);
    }
  };
  
  const clearFilters = () => {
    const emptyFilters = {
      dateFrom: '',
      dateTo: '',
      os: '',
      package: ''
    };
    setFilters(emptyFilters);
    
    // Reset to page 1 when clearing filters
    setPagination(prev => ({ ...prev, page: 1 }));
    
    // If a host is selected, re-fetch without filters
    if (selectedHost) {
      fetchHistory(selectedHost, emptyFilters, 1);
    }
  };
  
  const handlePageChange = (event, page) => {
    setPagination(prev => ({ ...prev, page }));
    if (selectedHost) {
      fetchHistory(selectedHost, filters, page);
    }
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
                    setPagination(prev => ({ ...prev, page: 1 }));
                    fetchHistory(host, emptyFilters, 1);
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
                            Showing {history.length} of {pagination.total} update{pagination.total !== 1 ? 's' : ''}
                            {hasActiveFilters && ' (filtered)'}
                            {pagination.total > pagination.pageSize && ` • Page ${pagination.page} of ${Math.ceil(pagination.total / pagination.pageSize)}`}
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
                        
                        {/* Pagination Controls */}
                        {pagination.total > pagination.pageSize && (
                          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                            <Pagination
                              count={Math.ceil(pagination.total / pagination.pageSize)}
                              page={pagination.page}
                              onChange={handlePageChange}
                              color="primary"
                              showFirstButton
                              showLastButton
                              size="small"
                            />
                          </Box>
                        )}
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
