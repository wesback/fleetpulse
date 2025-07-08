import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
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

// Mock matchMedia for useMediaQuery
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Test wrapper with theme provider
const TestWrapper = ({ children }) => (
  <BrowserRouter>
    {children}
  </BrowserRouter>
);

describe('StatisticsPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state initially', () => {
    axios.get.mockImplementation(() => new Promise(() => {})); // Never resolves
    
    render(
      <TestWrapper>
        <StatisticsPage />
      </TestWrapper>
    );
    
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('renders error state when API fails', async () => {
    axios.get.mockRejectedValueOnce(new Error('API Error'));
    
    render(
      <TestWrapper>
        <StatisticsPage />
      </TestWrapper>
    );
    
    await waitFor(() => {
      expect(screen.getByText('Failed to load statistics')).toBeInTheDocument();
    });
  });

  it('renders empty statistics correctly', async () => {
    const mockData = {
      total_hosts: 0,
      total_updates: 0,
      recent_updates: 0,
      top_packages: [],
      updates_by_os: [],
      updates_timeline: [],
      host_activity: []
    };

    axios.get.mockResolvedValueOnce({ data: mockData });
    
    render(
      <TestWrapper>
        <StatisticsPage />
      </TestWrapper>
    );
    
    await waitFor(() => {
      expect(screen.getByText('Fleet Statistics')).toBeInTheDocument();
      expect(screen.getByText('Total Hosts')).toBeInTheDocument();
      expect(screen.getByText('0')).toBeInTheDocument(); // Should show 0 for total hosts
    });
  });

  it('renders statistics with data correctly', async () => {
    const mockData = {
      total_hosts: 5,
      total_updates: 150,
      recent_updates: 45,
      top_packages: [
        { name: 'nginx', count: 25 },
        { name: 'apache2', count: 20 }
      ],
      updates_by_os: [
        { os: 'Ubuntu 22.04', count: 80 },
        { os: 'CentOS 8', count: 70 }
      ],
      updates_timeline: [
        { date: '2025-07-01', count: 10 },
        { date: '2025-07-02', count: 15 }
      ],
      host_activity: [
        { hostname: 'web-server-1', count: 30, last_update: '2025-07-08' },
        { hostname: 'db-server-1', count: 25, last_update: '2025-07-07' }
      ]
    };

    axios.get.mockResolvedValueOnce({ data: mockData });
    
    render(
      <TestWrapper>
        <StatisticsPage />
      </TestWrapper>
    );
    
    await waitFor(() => {
      // Check summary cards
      expect(screen.getByText('Total Hosts')).toBeInTheDocument();
      expect(screen.getByText('5')).toBeInTheDocument();
      expect(screen.getByText('Total Updates')).toBeInTheDocument();
      expect(screen.getByText('150')).toBeInTheDocument();
      expect(screen.getByText('Recent Updates')).toBeInTheDocument();
      expect(screen.getByText('45')).toBeInTheDocument();
      
      // Check charts are rendered
      expect(screen.getByTestId('line-chart')).toBeInTheDocument();
      expect(screen.getByTestId('doughnut-chart')).toBeInTheDocument();
      expect(screen.getAllByTestId('bar-chart')).toHaveLength(2); // Two bar charts
      
      // Check chart titles
      expect(screen.getByText('Updates Timeline (Last 30 Days)')).toBeInTheDocument();
      expect(screen.getByText('Updates by Operating System')).toBeInTheDocument();
      expect(screen.getByText('Most Updated Packages')).toBeInTheDocument();
      expect(screen.getByText('Most Active Hosts')).toBeInTheDocument();
    });
  });

  it('calls statistics API on mount', async () => {
    const mockData = {
      total_hosts: 0,
      total_updates: 0,
      recent_updates: 0,
      top_packages: [],
      updates_by_os: [],
      updates_timeline: [],
      host_activity: []
    };

    axios.get.mockResolvedValueOnce({ data: mockData });
    
    render(
      <TestWrapper>
        <StatisticsPage />
      </TestWrapper>
    );
    
    await waitFor(() => {
      expect(axios.get).toHaveBeenCalledWith('/api/statistics');
    });
  });

  it('calculates activity percentage correctly', async () => {
    const mockData = {
      total_hosts: 4,
      total_updates: 100,
      recent_updates: 30,
      top_packages: [],
      updates_by_os: [],
      updates_timeline: [],
      host_activity: []
    };

    axios.get.mockResolvedValueOnce({ data: mockData });
    
    render(
      <TestWrapper>
        <StatisticsPage />
      </TestWrapper>
    );
    
    await waitFor(() => {
      expect(screen.getByText('Active Percentage')).toBeInTheDocument();
      expect(screen.getByText('30%')).toBeInTheDocument(); // 30/100 * 100 = 30%
    });
  });

  it('handles zero division in activity percentage', async () => {
    const mockData = {
      total_hosts: 0,
      total_updates: 0,
      recent_updates: 0,
      top_packages: [],
      updates_by_os: [],
      updates_timeline: [],
      host_activity: []
    };

    axios.get.mockResolvedValueOnce({ data: mockData });
    
    render(
      <TestWrapper>
        <StatisticsPage />
      </TestWrapper>
    );
    
    await waitFor(() => {
      expect(screen.getByText('Active Percentage')).toBeInTheDocument();
      expect(screen.getByText('0%')).toBeInTheDocument(); // Should handle division by zero
    });
  });

  it('handles API error with custom message', async () => {
    const errorResponse = {
      response: {
        data: {
          detail: 'Custom error message'
        }
      }
    };

    axios.get.mockRejectedValueOnce(errorResponse);
    
    render(
      <TestWrapper>
        <StatisticsPage />
      </TestWrapper>
    );
    
    await waitFor(() => {
      expect(screen.getByText('Custom error message')).toBeInTheDocument();
    });
  });

  it('formats large numbers correctly', async () => {
    const mockData = {
      total_hosts: 1,
      total_updates: 1500,
      recent_updates: 1200,
      top_packages: [],
      updates_by_os: [],
      updates_timeline: [],
      host_activity: []
    };

    axios.get.mockResolvedValueOnce({ data: mockData });
    
    render(
      <TestWrapper>
        <StatisticsPage />
      </TestWrapper>
    );
    
    await waitFor(() => {
      expect(screen.getByText('1,500')).toBeInTheDocument(); // Total updates formatted
      expect(screen.getByText('1,200')).toBeInTheDocument(); // Recent updates formatted
    });
  });
});
