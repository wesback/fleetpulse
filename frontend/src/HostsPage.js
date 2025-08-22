import React, { useEffect, useState, useCallback, useRef } from 'react';
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
  CircularProgress,
  TextField,
  Button,
  Chip,
  Stack,
  Pagination,
  Switch,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Badge,
} from '@mui/material';
import DnsIcon from '@mui/icons-material/Dns';
import FilterListIcon from '@mui/icons-material/FilterList';
import ClearIcon from '@mui/icons-material/Clear';
import TodayIcon from '@mui/icons-material/Today';

const API_BASE = '/api';

/**
 * Hosts page component for viewing host details and update history
 */
const HostsPage = () => {
  const [hosts, setHosts] = useState([]);
  const [selectedHost, setSelectedHost] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const isMountedRef = useRef(true);
  
  // Today's updates state
  const [showTodayUpdates, setShowTodayUpdates] = useState(false);
  const [todayUpdates, setTodayUpdates] = useState([]);
  const [todayUpdatesLoading, setTodayUpdatesLoading] = useState(false);
  const [todayFilters, setTodayFilters] = useState({
    hostname: '',
    package: ''
  });
  const [todayPagination, setTodayPagination] = useState({
    page: 1,
    pageSize: 25,
    total: 0
  });
  
  // Filter state
  const [filters, setFilters] = useState({
    dateFrom: '',
    dateTo: '',
    package: ''
  });
  
  // Pagination state
  const [pagination, setPagination] = useState({
    page: 1,           // 1-based page number for Material-UI
    pageSize: 25,      // Items per page
    total: 0           // Total number of items
  });
  
  // Available OS options for dropdown (no longer needed but keeping variable for safety)
  const [availableOSes, setAvailableOSes] = useState([]);

  useEffect(() => {
    isMountedRef.current = true;
    fetchHosts();
    
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  const fetchHosts = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE}/hosts`);
      const hostsData = Array.isArray(response.data.hosts) ? response.data.hosts : [];
      if (isMountedRef.current) {
        setHosts(hostsData);
      }
    } catch (err) {
      console.error('Error fetching hosts:', err);
      if (isMountedRef.current) {
        setHosts([]); // Defensive: always set to array
      }
    }
  }, []);

  const fetchTodayUpdates = useCallback(async (currentFilters = todayFilters, currentPage = 1) => {
    setTodayUpdatesLoading(true);
    
    try {
      // Calculate offset based on page and pageSize
      const offset = (currentPage - 1) * todayPagination.pageSize;
      
      // Build query parameters
      const params = new URLSearchParams();
      if (currentFilters.hostname) params.append('hostname', currentFilters.hostname);
      if (currentFilters.package) params.append('package', currentFilters.package);
      
      // Add pagination parameters
      params.append('limit', todayPagination.pageSize.toString());
      params.append('offset', offset.toString());
      
      const queryString = params.toString();
      const url = `${API_BASE}/today-updates?${queryString}`;
      
      const response = await axios.get(url);
      const data = response.data;
      
      if (isMountedRef.current) {
        setTodayUpdates(data.items || []);
        setTodayPagination(prev => ({
          ...prev,
          page: currentPage,
          total: data.total || 0
        }));
      }
    } catch (err) {
      console.error('Error fetching today\'s updates:', err);
      if (isMountedRef.current) {
        setTodayUpdates([]);
        setTodayPagination(prev => ({
          ...prev,
          page: currentPage,
          total: 0
        }));
      }
    } finally {
      if (isMountedRef.current) {
        setTodayUpdatesLoading(false);
      }
    }
  }, [todayFilters, todayPagination.pageSize]);

  const fetchHistory = useCallback(async (host, currentFilters = filters, currentPage = 1) => {
    setLoading(true);
    setSelectedHost(host);
    
    try {
      // Calculate offset based on page and pageSize
      const offset = (currentPage - 1) * pagination.pageSize;
      
      // Build query parameters
      const params = new URLSearchParams();
      if (currentFilters.dateFrom) params.append('date_from', currentFilters.dateFrom);
      if (currentFilters.dateTo) params.append('date_to', currentFilters.dateTo);
      if (currentFilters.package) params.append('package', currentFilters.package);
      
      // Add pagination parameters
      params.append('limit', pagination.pageSize.toString());
      params.append('offset', offset.toString());
      
      const queryString = params.toString();
      const url = `${API_BASE}/history/${host}?${queryString}`;
      
      const response = await axios.get(url);
      const data = response.data;
      
      if (isMountedRef.current) {
        setHistory(data.items || []);
        setPagination(prev => ({
          ...prev,
          page: currentPage,
          total: data.total || 0
        }));
        
        // Extract unique OS values for dropdown from current page - NO LONGER NEEDED
        // const osSet = new Set((data.items || []).map(item => item.os));
        // const currentOSes = Array.from(osSet);
        
        // Merge with existing OS options to preserve them across filter operations - NO LONGER NEEDED
        // setAvailableOSes(prev => {
        //   const combinedSet = new Set([...prev, ...currentOSes]);
        //   return Array.from(combinedSet).sort();
        // });
      }
    } catch (err) {
      console.error('Error fetching history:', err);
      if (isMountedRef.current) {
        setHistory([]);
        // Don't clear availableOSes on filter errors to preserve dropdown options - NO LONGER NEEDED
        setPagination(prev => ({
          ...prev,
          page: currentPage,
          total: 0
        }));
      }
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
      }
    }
  }, [filters, pagination.pageSize]);
  
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
  
  const handleTodayFilterChange = (filterName, value) => {
    const newFilters = { ...todayFilters, [filterName]: value };
    setTodayFilters(newFilters);
    
    // Reset to page 1 when filters change
    setTodayPagination(prev => ({ ...prev, page: 1 }));
    
    // Re-fetch with new filters if today updates are shown
    if (showTodayUpdates) {
      fetchTodayUpdates(newFilters, 1);
    }
  };
  
  const clearTodayFilters = () => {
    const emptyFilters = {
      hostname: '',
      package: ''
    };
    setTodayFilters(emptyFilters);
    
    // Reset to page 1 when clearing filters
    setTodayPagination(prev => ({ ...prev, page: 1 }));
    
    // Re-fetch without filters if today updates are shown
    if (showTodayUpdates) {
      fetchTodayUpdates(emptyFilters, 1);
    }
  };
  
  const handleTodayPageChange = (event, page) => {
    setTodayPagination(prev => ({ ...prev, page }));
    fetchTodayUpdates(todayFilters, page);
  };
  
  const handleTodayToggle = (event) => {
    const enabled = event.target.checked;
    setShowTodayUpdates(enabled);
    
    if (enabled) {
      // Fetch today's updates when enabled
      fetchTodayUpdates(todayFilters, 1);
    }
  };
  
  const hasActiveFilters = filters.dateFrom || filters.dateTo || filters.package;
  const hasTodayActiveFilters = todayFilters.hostname || todayFilters.package;

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Host Management
      </Typography>
      
      {/* Today's Updates Section */}
      <Paper elevation={2} sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <TodayIcon sx={{ mr: 1 }} />
          <Typography variant="h6">Today's Updates</Typography>
          <FormControlLabel
            control={
              <Switch
                checked={showTodayUpdates}
                onChange={handleTodayToggle}
                color="primary"
              />
            }
            label="Show Today's Updates"
            sx={{ ml: 2 }}
          />
          {showTodayUpdates && todayPagination.total > 0 && (
            <Badge 
              badgeContent={todayPagination.total} 
              color="primary" 
              sx={{ ml: 2 }}
            >
              <Chip 
                label="Updates" 
                size="small" 
                color="primary" 
                variant="outlined"
              />
            </Badge>
          )}
        </Box>
        
        {showTodayUpdates && (
          <>
            {/* Today's Updates Filter Controls */}
            <Paper elevation={1} sx={{ p: 2, mb: 2, backgroundColor: 'background.default' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <FilterListIcon sx={{ mr: 1 }} />
                <Typography variant="h6">Filters</Typography>
                {hasTodayActiveFilters && (
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
                  <FormControl size="small" sx={{ minWidth: 200 }}>
                    <InputLabel id="today-host-filter-label">Host</InputLabel>
                    <Select
                      labelId="today-host-filter-label"
                      id="today-host-filter"
                      value={todayFilters.hostname}
                      label="Host"
                      onChange={(e) => handleTodayFilterChange('hostname', e.target.value)}
                    >
                      <MenuItem value="">
                        <em>All Hosts</em>
                      </MenuItem>
                      {hosts.map((host) => (
                        <MenuItem key={host} value={host}>
                          {host}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                  
                  <TextField
                    label="Package Name"
                    value={todayFilters.package}
                    onChange={(e) => handleTodayFilterChange('package', e.target.value)}
                    size="small"
                    placeholder="Search packages..."
                    sx={{ minWidth: 200 }}
                  />
                </Stack>
                
                <Box>
                  <Button
                    variant="outlined"
                    startIcon={<ClearIcon />}
                    onClick={clearTodayFilters}
                    disabled={!hasTodayActiveFilters}
                    size="small"
                  >
                    Clear Filters
                  </Button>
                </Box>
              </Stack>
            </Paper>
            
            {/* Today's Updates Table */}
            {todayUpdatesLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <CircularProgress />
              </Box>
            ) : (
              <>
                {todayUpdates.length === 0 ? (
                  <Typography variant="body2" color="text.secondary">
                    {hasTodayActiveFilters 
                      ? "No updates found for today matching the current filters."
                      : "No package updates occurred today."
                    }
                  </Typography>
                ) : (
                  <>
                    <Box sx={{ mb: 1 }}>
                      <Typography variant="body2" color="text.secondary">
                        Showing {todayUpdates.length} of {todayPagination.total} update{todayPagination.total !== 1 ? 's' : ''} from today
                        {hasTodayActiveFilters && ' (filtered)'}
                        {todayPagination.total > todayPagination.pageSize && ` • Page ${todayPagination.page} of ${Math.ceil(todayPagination.total / todayPagination.pageSize)}`}
                      </Typography>
                    </Box>
                    
                    <TableContainer component={Paper} elevation={1}>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Host</TableCell>
                            <TableCell>Date</TableCell>
                            <TableCell>OS</TableCell>
                            <TableCell>Package</TableCell>
                            <TableCell>Old Version</TableCell>
                            <TableCell>New Version</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {todayUpdates.map((rec, i) => (
                            <TableRow key={i} hover>
                              <TableCell>{rec.hostname}</TableCell>
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
                    
                    {/* Today's Updates Pagination Controls */}
                    {todayPagination.total > todayPagination.pageSize && (
                      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                        <Pagination
                          count={Math.ceil(todayPagination.total / todayPagination.pageSize)}
                          page={todayPagination.page}
                          onChange={handleTodayPageChange}
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
          </>
        )}
      </Paper>
      
      <Box sx={{ display: 'flex', gap: 4 }}>
        <Paper elevation={2} sx={{ width: 300, minHeight: 400, padding: 2 }}>
          <Typography variant="h6" gutterBottom>
            <DnsIcon sx={{ verticalAlign: 'middle', mr: 1 }} />
            Hosts ({hosts.length})
          </Typography>
          <List>
            {hosts.length === 0 && (
              <Box sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  No hosts found
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                  Hosts will appear here after they submit update reports to the /report endpoint
                </Typography>
              </Box>
            )}
            {hosts.map(host => (
              <ListItemButton
                key={host}
                selected={selectedHost === host}
                onClick={() => {
                  // Clear filters when switching hosts
                  const emptyFilters = {
                    dateFrom: '',
                    dateTo: '',
                    package: ''
                  };
                  setFilters(emptyFilters);
                  setAvailableOSes([]); // Clear OS options when switching hosts - NO LONGER NEEDED BUT KEEPING FOR SAFETY
                  setPagination(prev => ({ ...prev, page: 1 }));
                  fetchHistory(host, emptyFilters, 1);
                }}
                sx={{ borderRadius: 1, mb: 0.5 }}
              >
                <ListItemText 
                  primary={host}
                  primaryTypographyProps={{ 
                    variant: 'body2',
                    sx: { wordBreak: 'break-all' }
                  }}
                />
              </ListItemButton>
            ))}
          </List>
        </Paper>
        
        <Box sx={{ flexGrow: 1 }}>
          {selectedHost && (
            <Paper elevation={2} sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Update History for <strong>{selectedHost}</strong>
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
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                  <CircularProgress />
                </Box>
              ) : (
                <>
                  {history.length === 0 ? (
                    <Typography variant="body2" color="text.secondary">
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
                      
                      <TableContainer component={Paper} elevation={1}>
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
                              <TableRow key={i} hover>
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
            <Paper elevation={2} sx={{ p: 4, textAlign: 'center' }}>
              <DnsIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                Select a Host
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Choose a host from the list to view its update history and manage packages.
              </Typography>
            </Paper>
          )}
        </Box>
      </Box>
    </Container>
  );
};

export default HostsPage;
