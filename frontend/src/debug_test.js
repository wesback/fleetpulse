// Debug test for StatisticsPage component
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import axios from 'axios';
import StatisticsPage from './StatisticsPage';

jest.mock('axios');

// Mock Chart.js components
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

const TestWrapper = ({ children }) => {
  const theme = createTheme();
  return (
    <BrowserRouter>
      <ThemeProvider theme={theme}>
        {children}
      </ThemeProvider>
    </BrowserRouter>
  );
};

test('debug StatisticsPage rendering', async () => {
  const mockData = {
    total_hosts: 5,
    total_updates: 150,
    recent_updates: 45,
    top_packages: [
      { name: 'nginx', count: 25 }
    ],
    updates_by_os: [
      { os: 'Ubuntu 22.04', count: 80 }
    ],
    updates_timeline: [
      { date: '2025-07-01', count: 10 }
    ],
    host_activity: [
      { hostname: 'web-server-1', count: 30, last_update: '2025-07-08' }
    ]
  };

  axios.get.mockResolvedValueOnce({ data: mockData });
  
  const { container } = render(
    <TestWrapper>
      <StatisticsPage />
    </TestWrapper>
  );
  
  console.log('Component rendered, waiting for data...');
  
  await waitFor(() => {
    console.log('Looking for Fleet Statistics...');
    expect(screen.getByText('Fleet Statistics')).toBeInTheDocument();
  });
  
  console.log('Found Fleet Statistics, looking for Total Hosts...');
  console.log('Full HTML output:', container.innerHTML);
  
  // Try to find Total Hosts
  const totalHostsElement = screen.queryByText('Total Hosts');
  console.log('Total Hosts element:', totalHostsElement);
  
  if (!totalHostsElement) {
    console.log('Total Hosts not found! Checking what elements are present...');
    const allElements = container.querySelectorAll('*');
    allElements.forEach((el, index) => {
      if (el.textContent && el.textContent.trim()) {
        console.log(`Element ${index}:`, el.textContent.trim());
      }
    });
  }
});