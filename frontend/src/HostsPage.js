import React, { useEffect, useState } from 'react';
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
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button,
  Chip,
  Stack,
  Pagination,
} from '@mui/material';
import DnsIcon from '@mui/icons-material/Dns';
import FilterListIcon from '@mui/icons-material/FilterList';
import ClearIcon from '@mui/icons-material/Clear';

const API_BASE = '/api';

/**
 * Hosts page component for viewing host details and update history
 */
const HostsPage = () => {
  const [hosts, setHosts] = useState([]);
  const [selectedHost, setSelectedHost] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  
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
    fetchHosts();
  }, []);

  const fetchHosts = async () => {
    try {
      const response = await axios.get(`${API_BASE}/hosts`);
      const hostsData = Array.isArray(response.data.hosts) ? response.data.hosts : [];
      setHosts(hostsData);
    } catch (err) {
      console.error('Error fetching hosts:', err);
      setHosts([]); // Defensive: always set to array
    }
  };

  const fetchHistory = async (host, currentFilters = filters, currentPage = 1) => {
    setLoading(true);
    setSelectedHost(host);
    
    try {
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
      
      const response = await axios.get(url);
      const data = response.data;
      
      setHistory(data.items || []);
      setPagination(prev => ({
        ...prev,
        page: currentPage,
        total: data.total || 0
      }));
      
      // Extract unique OS values for dropdown from current page
      const osSet = new Set((data.items || []).map(item => item.os));
      setAvailableOSes(Array.from(osSet).sort());
    } catch (err) {
      console.error('Error fetching history:', err);
      setHistory([]);
      setAvailableOSes([]);
      setPagination(prev => ({
        ...prev,
        page: currentPage,
        total: 0
      }));
    } finally {
      setLoading(false);
    }
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
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Host Management
      </Typography>
      
      <Box sx={{ display: 'flex', gap: 4 }}>
        <Paper elevation={2} sx={{ width: 300, minHeight: 400, padding: 2 }}>
          <Typography variant="h6" gutterBottom>
            <DnsIcon sx={{ verticalAlign: 'middle', mr: 1 }} />
            Hosts ({hosts.length})
          </Typography>
          <List>
            {hosts.length === 0 && (
              <Typography variant="body2" color="text.secondary">
                No hosts found.
              </Typography>
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
                    os: '',
                    package: ''
                  };
                  setFilters(emptyFilters);
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
