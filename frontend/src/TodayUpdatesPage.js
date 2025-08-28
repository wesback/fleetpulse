import React, { useEffect, useState, useCallback, useRef } from 'react';
import axios from 'axios';
import {
  Container,
  Typography,
  Box,
  Paper,
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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Badge,
} from '@mui/material';
import TodayIcon from '@mui/icons-material/Today';
import FilterListIcon from '@mui/icons-material/FilterList';
import ClearIcon from '@mui/icons-material/Clear';

const API_BASE = '/api';

/**
 * Today's Updates page component for viewing all package updates from today
 */
const TodayUpdatesPage = () => {
  const isMountedRef = useRef(true);
  
  // Today's updates state
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

  useEffect(() => {
    isMountedRef.current = true;
    // Automatically fetch today's updates when component mounts
    fetchTodayUpdates(todayFilters, 1);
    
    return () => {
      isMountedRef.current = false;
    };
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

  const handleTodayFilterChange = (filterName, value) => {
    const newFilters = { ...todayFilters, [filterName]: value };
    setTodayFilters(newFilters);
    
    // Reset to page 1 when filters change
    setTodayPagination(prev => ({ ...prev, page: 1 }));
    
    // Re-fetch with new filters
    fetchTodayUpdates(newFilters, 1);
  };
  
  const clearTodayFilters = () => {
    const emptyFilters = {
      hostname: '',
      package: ''
    };
    setTodayFilters(emptyFilters);
    
    // Reset to page 1 when clearing filters
    setTodayPagination(prev => ({ ...prev, page: 1 }));
    
    // Re-fetch without filters
    fetchTodayUpdates(emptyFilters, 1);
  };
  
  const handleTodayPageChange = (event, page) => {
    setTodayPagination(prev => ({ ...prev, page }));
    fetchTodayUpdates(todayFilters, page);
  };

  const hasTodayActiveFilters = todayFilters.hostname || todayFilters.package;

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <TodayIcon sx={{ mr: 1, fontSize: 32 }} />
        <Typography variant="h4" component="h1" gutterBottom sx={{ mb: 0 }}>
          Today's Updates
        </Typography>
        {todayPagination.total > 0 && (
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

      <Paper elevation={2} sx={{ p: 2, mb: 3 }}>
        {/* Today's Updates Filter Controls */}
        <Box sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <FilterListIcon sx={{ mr: 1 }} />
            <Typography variant="h6">Filters</Typography>
            {hasTodayActiveFilters && (
              <Button
                startIcon={<ClearIcon />}
                onClick={clearTodayFilters}
                size="small"
                sx={{ ml: 2 }}
              >
                Clear Filters
              </Button>
            )}
          </Box>
          
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <TextField
              label="Hostname"
              value={todayFilters.hostname}
              onChange={(e) => handleTodayFilterChange('hostname', e.target.value)}
              size="small"
              sx={{ minWidth: 200 }}
            />
            <TextField
              label="Package Name"
              value={todayFilters.package}
              onChange={(e) => handleTodayFilterChange('package', e.target.value)}
              size="small"
              sx={{ minWidth: 200 }}
            />
          </Stack>
        </Box>

        {/* Today's Updates Content */}
        {todayUpdatesLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        ) : todayUpdates.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="body2" color="text.secondary">
              {hasTodayActiveFilters 
                ? "No updates found for today matching the current filters."
                : "No package updates occurred today."
              }
            </Typography>
          </Box>
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
      </Paper>
    </Container>
  );
};

export default TodayUpdatesPage;