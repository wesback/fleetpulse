import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Box,
  FormControlLabel,
  Switch,
  Tab,
  Tabs,
} from '@mui/material';
import StorageIcon from '@mui/icons-material/Storage';
import BarChartIcon from '@mui/icons-material/BarChart';
import DnsIcon from '@mui/icons-material/Dns';
import TodayIcon from '@mui/icons-material/Today';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';

/**
 * Navigation component with app bar and tabs
 */
const Navigation = ({ mode, toggleTheme }) => {
  const location = useLocation();
  const navigate = useNavigate();
  
  // Map root path to statistics path for tab selection
  const currentPath = location.pathname === '/' ? '/statistics' : location.pathname;
  
  // Ensure the tab value is always one of the valid tab values
  const tabValue = ['/statistics', '/today-updates', '/hosts'].includes(currentPath) ? currentPath : '/statistics';
  
  const handleTabChange = (event, newValue) => {
    navigate(newValue);
  };
  
  return (
    <AppBar position="static" sx={{ marginBottom: 4 }}>
      <Toolbar>
        <StorageIcon sx={{ marginRight: 2 }} />
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          FleetPulse &mdash; Linux Fleet Package Dashboard
        </Typography>
        
        <Box sx={{ mr: 2 }}>
          <Tabs 
            value={tabValue} 
            onChange={handleTabChange}
            textColor="inherit"
            indicatorColor="secondary"
            sx={{
              '& .MuiTab-root': {
                color: 'rgba(255, 255, 255, 0.7)',
                '&.Mui-selected': {
                  color: 'white',
                },
              },
            }}
          >
            <Tab 
              value="/statistics" 
              label="Statistics" 
              icon={<BarChartIcon />}
              iconPosition="start"
            />
            <Tab 
              value="/today-updates" 
              label="Today's Updates" 
              icon={<TodayIcon />}
              iconPosition="start"
            />
            <Tab 
              value="/hosts" 
              label="Hosts" 
              icon={<DnsIcon />}
              iconPosition="start"
            />
          </Tabs>
        </Box>
        
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
  );
};

export default Navigation;
