import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import axios from 'axios';
import App from './App';

jest.mock('axios');

// Mock Chart.js components for StatisticsPage
jest.mock('react-chartjs-2', () => ({
  Bar: jest.fn(() => <div data-testid="bar-chart">Bar Chart</div>),
  Line: jest.fn(() => <div data-testid="line-chart">Line Chart</div>),
  Doughnut: jest.fn(() => <div data-testid="doughnut-chart">Doughnut Chart</div>),
}));

jest.mock('chart.js', () => ({
  Chart: {
    register: jest.fn(),
  },
  CategoryScale: jest.fn(),
  LinearScale: jest.fn(),
  BarElement: jest.fn(),
  LineElement: jest.fn(),
  PointElement: jest.fn(),
  ArcElement: jest.fn(),
  Title: jest.fn(),
  Tooltip: jest.fn(),
  Legend: jest.fn(),
  TimeScale: jest.fn(),
}));

// Mock matchMedia for useMediaQuery
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

describe('App', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  it('renders navigation and redirects to statistics page by default', async () => {
    // Mock statistics API call
    axios.get.mockResolvedValueOnce({ 
      data: { 
        total_hosts: 0,
        total_updates: 0,
        recent_updates: 0,
        top_packages: [],
        updates_by_os: [],
        updates_timeline: [],
        host_activity: []
      } 
    });
    
    render(<App />);
    
    expect(screen.getByText('FleetPulse — Linux Fleet Package Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Statistics')).toBeInTheDocument();
    expect(screen.getByText('Hosts')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByText('Fleet Statistics')).toBeInTheDocument();
    });
  });

  it('navigates to hosts page when hosts tab is clicked', async () => {
    // Mock statistics API call for initial load
    axios.get.mockResolvedValueOnce({ 
      data: { 
        total_hosts: 0,
        total_updates: 0,
        recent_updates: 0,
        top_packages: [],
        updates_by_os: [],
        updates_timeline: [],
        host_activity: []
      } 
    });
    
    // Mock hosts API call
    axios.get.mockResolvedValueOnce({ data: { hosts: [] } });
    
    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText('Fleet Statistics')).toBeInTheDocument();
    });
    
    const hostsTab = screen.getByText('Hosts').closest('button');
    fireEvent.click(hostsTab);
    
    await waitFor(() => {
      expect(screen.getByText('Host Management')).toBeInTheDocument();
    });
  });

  it('navigates back to statistics page when statistics tab is clicked', async () => {
    // Mock statistics API call
    axios.get.mockResolvedValueOnce({ 
      data: { 
        total_hosts: 0,
        total_updates: 0,
        recent_updates: 0,
        top_packages: [],
        updates_by_os: [],
        updates_timeline: [],
        host_activity: []
      } 
    });
    
    // Mock hosts API call
    axios.get.mockResolvedValueOnce({ data: { hosts: [] } });
    
    // Mock another statistics API call for navigation back
    axios.get.mockResolvedValueOnce({ 
      data: { 
        total_hosts: 0,
        total_updates: 0,
        recent_updates: 0,
        top_packages: [],
        updates_by_os: [],
        updates_timeline: [],
        host_activity: []
      } 
    });
    
    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText('Fleet Statistics')).toBeInTheDocument();
    });
    
    // Navigate to hosts
    const hostsTab = screen.getByText('Hosts').closest('button');
    fireEvent.click(hostsTab);
    
    await waitFor(() => {
      expect(screen.getByText('Host Management')).toBeInTheDocument();
    });
    
    // Navigate back to statistics
    const statisticsTab = screen.getByText('Statistics').closest('button');
    fireEvent.click(statisticsTab);
    
    await waitFor(() => {
      expect(screen.getByText('Fleet Statistics')).toBeInTheDocument();
    });
  });

  it('toggles theme correctly', async () => {
    // Mock statistics API call
    axios.get.mockResolvedValueOnce({ 
      data: { 
        total_hosts: 0,
        total_updates: 0,
        recent_updates: 0,
        top_packages: [],
        updates_by_os: [],
        updates_timeline: [],
        host_activity: []
      } 
    });
    
    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText('Fleet Statistics')).toBeInTheDocument();
    });
    
    const themeToggle = screen.getByRole('checkbox');
    
    // Should start in light mode
    expect(themeToggle).not.toBeChecked();
    
    // Toggle to dark mode
    fireEvent.click(themeToggle);
    expect(themeToggle).toBeChecked();
    
    // Toggle back to light mode
    fireEvent.click(themeToggle);
    expect(themeToggle).not.toBeChecked();
  });

  it('persists theme preference in localStorage', async () => {
    // Mock statistics API call
    axios.get.mockResolvedValueOnce({ 
      data: { 
        total_hosts: 0,
        total_updates: 0,
        recent_updates: 0,
        top_packages: [],
        updates_by_os: [],
        updates_timeline: [],
        host_activity: []
      } 
    });
    
    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText('Fleet Statistics')).toBeInTheDocument();
    });
    
    const themeToggle = screen.getByRole('checkbox');
    
    // Toggle to dark mode
    fireEvent.click(themeToggle);
    
    // Check localStorage
    expect(localStorage.getItem('themeMode')).toBe('dark');
    
    // Toggle back to light mode
    fireEvent.click(themeToggle);
    
    // Check localStorage
    expect(localStorage.getItem('themeMode')).toBe('light');
  });

  it('loads theme preference from localStorage on startup', () => {
    localStorage.setItem('themeMode', 'dark');
    
    // Mock statistics API call
    axios.get.mockResolvedValueOnce({ 
      data: { 
        total_hosts: 0,
        total_updates: 0,
        recent_updates: 0,
        top_packages: [],
        updates_by_os: [],
        updates_timeline: [],
        host_activity: []
      } 
    });
    
    render(<App />);
    
    const themeToggle = screen.getByRole('checkbox');
    expect(themeToggle).toBeChecked(); // Should start in dark mode
  });

  it('handles route changes correctly', async () => {
    // Mock statistics API call
    axios.get.mockResolvedValueOnce({ 
      data: { 
        total_hosts: 0,
        total_updates: 0,
        recent_updates: 0,
        top_packages: [],
        updates_by_os: [],
        updates_timeline: [],
        host_activity: []
      } 
    });
    
    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText('Fleet Statistics')).toBeInTheDocument();
    });
    
    // Verify statistics tab is active
    const statisticsTab = screen.getByText('Statistics').closest('button');
    expect(statisticsTab).toHaveClass('Mui-selected');
    
    // Mock hosts API call
    axios.get.mockResolvedValueOnce({ data: { hosts: [] } });
    
    // Navigate to hosts
    const hostsTab = screen.getByText('Hosts').closest('button');
    fireEvent.click(hostsTab);
    
    await waitFor(() => {
      expect(screen.getByText('Host Management')).toBeInTheDocument();
    });
    
    // Verify hosts tab is now active
    expect(hostsTab).toHaveClass('Mui-selected');
    expect(statisticsTab).not.toHaveClass('Mui-selected');
  });

  it('renders correct theme icons', async () => {
    // Mock statistics API call
    axios.get.mockResolvedValueOnce({ 
      data: { 
        total_hosts: 0,
        total_updates: 0,
        recent_updates: 0,
        top_packages: [],
        updates_by_os: [],
        updates_timeline: [],
        host_activity: []
      } 
    });
    
    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText('Fleet Statistics')).toBeInTheDocument();
    });
    
    // In light mode, should show sun icon
    expect(screen.getByTestId('Brightness7Icon')).toBeInTheDocument();
    
    // Toggle to dark mode
    const themeToggle = screen.getByRole('checkbox');
    fireEvent.click(themeToggle);
    
    // In dark mode, should show moon icon
    expect(screen.getByTestId('Brightness4Icon')).toBeInTheDocument();
  });
});
