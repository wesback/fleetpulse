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
  Fab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Card,
  CardContent,
  Alert,
  Collapse,
  Divider,
} from '@mui/material';
import StorageIcon from '@mui/icons-material/Storage';
import DnsIcon from '@mui/icons-material/Dns';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import FilterListIcon from '@mui/icons-material/FilterList';
import ClearIcon from '@mui/icons-material/Clear';
import ChatIcon from '@mui/icons-material/Chat';
import SendIcon from '@mui/icons-material/Send';
import CloseIcon from '@mui/icons-material/Close';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';

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

  // Chat state
  const [chatOpen, setChatOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);

  useEffect(() => {
    axios.get(`${API_BASE}/hosts`)
      .then(res => setHosts(Array.isArray(res.data.hosts) ? res.data.hosts : []))
      .catch((err) => {
        console.error('Error fetching hosts:', err);
        setHosts([]); // Defensive: always set to array
      });
  }, []);

  const fetchHistory = (host, currentFilters = filters) => {
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
    
    axios.get(url)
      .then(res => {
        setHistory(res.data);
        // Extract unique OS values for dropdown
        const osSet = new Set(res.data.map(item => item.os));
        setAvailableOSes(Array.from(osSet).sort());
      })
      .catch(err => {
        console.error('Error fetching history:', err);
        setHistory([]);
        setAvailableOSes([]);
      })
      .finally(() => setLoading(false));
  };
  
  const handleFilterChange = (filterName, value) => {
    const newFilters = { ...filters, [filterName]: value };
    setFilters(newFilters);
    
    // If a host is selected, re-fetch with new filters
    if (selectedHost) {
      fetchHistory(selectedHost, newFilters);
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
    
    // If a host is selected, re-fetch without filters
    if (selectedHost) {
      fetchHistory(selectedHost, emptyFilters);
    }
  };
  
  // Chat functions
  const sendChatMessage = async () => {
    if (!chatInput.trim()) return;
    
    const userMessage = { type: 'user', text: chatInput };
    setChatMessages(prev => [...prev, userMessage]);
    setChatLoading(true);
    
    try {
      const response = await axios.post(`${API_BASE}/chat`, {
        question: chatInput
      });
      
      const botMessage = {
        type: 'bot',
        text: response.data.answer,
        data: response.data.data,
        queryType: response.data.query_type
      };
      
      setChatMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Error sending chat message:', error);
      const errorMessage = {
        type: 'bot',
        text: 'Sorry, I encountered an error processing your question. Please try again.',
        queryType: 'error'
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setChatLoading(false);
      setChatInput('');
    }
  };
  
  const handleChatKeyPress = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendChatMessage();
    }
  };
  
  const clearChatHistory = () => {
    setChatMessages([]);
  };
  
  const hasActiveFilters = filters.dateFrom || filters.dateTo || filters.os || filters.package;

  // Chat component
  const ChatComponent = () => (
    <Dialog
      open={chatOpen}
      onClose={() => setChatOpen(false)}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: { height: '70vh', maxHeight: 600 }
      }}
    >
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <ChatIcon sx={{ mr: 1 }} />
          FleetPulse Chat Assistant
        </Box>
        <IconButton onClick={() => setChatOpen(false)} size="small">
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      
      <DialogContent sx={{ display: 'flex', flexDirection: 'column', p: 0 }}>
        {/* Chat messages area */}
        <Box sx={{ flexGrow: 1, p: 2, overflow: 'auto', bgcolor: mode === 'dark' ? 'grey.900' : 'grey.50' }}>
          {chatMessages.length === 0 && (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <ChatIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                Welcome to FleetPulse Chat!
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Ask me questions about your package updates. Try:
              </Typography>
              <Box sx={{ mt: 2, textAlign: 'left', maxWidth: 400, mx: 'auto' }}>
                {[
                  "Which hosts had Python packages updated last week?",
                  "What packages were updated on web-01?",
                  "Show me Ubuntu hosts",
                  "How many hosts do we have?"
                ].map((example, i) => (
                  <Button
                    key={i}
                    variant="outlined"
                    size="small"
                    sx={{ m: 0.5, fontSize: '0.75rem' }}
                    onClick={() => setChatInput(example)}
                  >
                    {example}
                  </Button>
                ))}
              </Box>
            </Box>
          )}
          
          {chatMessages.map((message, index) => (
            <Box key={index} sx={{ mb: 2 }}>
              {message.type === 'user' ? (
                <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 1 }}>
                  <Paper 
                    sx={{ 
                      p: 1.5, 
                      maxWidth: '80%',
                      bgcolor: 'primary.main',
                      color: 'primary.contrastText'
                    }}
                  >
                    <Typography variant="body2">{message.text}</Typography>
                  </Paper>
                </Box>
              ) : (
                <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 1 }}>
                  <Paper 
                    sx={{ 
                      p: 1.5, 
                      maxWidth: '80%',
                      bgcolor: mode === 'dark' ? 'grey.700' : 'white'
                    }}
                  >
                    <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                      {message.text}
                    </Typography>
                    
                    {/* Show structured data if available */}
                    {message.data && Array.isArray(message.data) && message.data.length > 0 && (
                      <Box sx={{ mt: 2 }}>
                        <Divider sx={{ mb: 1 }} />
                        <Typography variant="caption" color="text.secondary">
                          Results ({message.data.length}):
                        </Typography>
                        <Box sx={{ mt: 1, maxHeight: 150, overflow: 'auto' }}>
                          {message.data.slice(0, 10).map((item, i) => (
                            <Chip
                              key={i}
                              label={
                                item.hostname || 
                                (item.package && `${item.package}: ${item.old_version} → ${item.new_version}`) ||
                                JSON.stringify(item)
                              }
                              size="small"
                              sx={{ m: 0.25 }}
                            />
                          ))}
                          {message.data.length > 10 && (
                            <Typography variant="caption" sx={{ display: 'block', mt: 1 }}>
                              ... and {message.data.length - 10} more
                            </Typography>
                          )}
                        </Box>
                      </Box>
                    )}
                  </Paper>
                </Box>
              )}
            </Box>
          ))}
          
          {chatLoading && (
            <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 1 }}>
              <Paper sx={{ p: 1.5, bgcolor: mode === 'dark' ? 'grey.700' : 'white' }}>
                <CircularProgress size={16} sx={{ mr: 1 }} />
                <Typography variant="body2" component="span">
                  Thinking...
                </Typography>
              </Paper>
            </Box>
          )}
        </Box>
      </DialogContent>
      
      <DialogActions sx={{ p: 2, pt: 1 }}>
        <Box sx={{ display: 'flex', gap: 1, width: '100%' }}>
          <TextField
            fullWidth
            variant="outlined"
            placeholder="Ask about package updates..."
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            onKeyPress={handleChatKeyPress}
            disabled={chatLoading}
            size="small"
          />
          <Button
            variant="contained"
            onClick={sendChatMessage}
            disabled={!chatInput.trim() || chatLoading}
            sx={{ minWidth: 'auto', px: 2 }}
          >
            <SendIcon />
          </Button>
          {chatMessages.length > 0 && (
            <Button
              variant="outlined"
              onClick={clearChatHistory}
              size="small"
              sx={{ minWidth: 'auto', px: 2 }}
            >
              Clear
            </Button>
          )}
        </Box>
      </DialogActions>
    </Dialog>
  );

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

      {/* Floating Chat Button */}
      <Fab
        color="primary"
        aria-label="chat"
        sx={{
          position: 'fixed',
          bottom: 20,
          right: 20,
          zIndex: 1000
        }}
        onClick={() => setChatOpen(true)}
      >
        <ChatIcon />
      </Fab>

      {/* Chat Component */}
      <ChatComponent />
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
