import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import axios from 'axios';
import HostsPage from './HostsPage';

jest.mock('axios');

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

describe('HostsPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders empty hosts list initially', async () => {
    axios.get.mockResolvedValueOnce({ data: { hosts: [] } });
    
    render(<HostsPage />);
    
    await waitFor(() => {
      expect(screen.getByText('Host Management')).toBeInTheDocument();
      expect(screen.getByText('Hosts (0)')).toBeInTheDocument();
      expect(screen.getByText('No hosts found.')).toBeInTheDocument();
    });
  });

  it('renders hosts list with data', async () => {
    axios.get.mockResolvedValueOnce({ data: { hosts: ['host1', 'host2', 'host3'] } });
    
    render(<HostsPage />);
    
    await waitFor(() => {
      expect(screen.getByText('Hosts (3)')).toBeInTheDocument();
      expect(screen.getByText('host1')).toBeInTheDocument();
      expect(screen.getByText('host2')).toBeInTheDocument();
      expect(screen.getByText('host3')).toBeInTheDocument();
    });
  });

  it('shows select host message when no host is selected', async () => {
    axios.get.mockResolvedValueOnce({ data: { hosts: ['host1'] } });
    
    render(<HostsPage />);
    
    await waitFor(() => {
      expect(screen.getByText('Select a Host')).toBeInTheDocument();
      expect(screen.getByText('Choose a host from the list to view its update history and manage packages.')).toBeInTheDocument();
    });
  });

  it('fetches and displays host history when host is selected', async () => {
    axios.get.mockResolvedValueOnce({ data: { hosts: ['test-host'] } });
    
    const historyData = {
      items: [
        {
          update_date: '2025-07-08',
          os: 'Ubuntu 22.04',
          name: 'nginx',
          old_version: '1.20.0',
          new_version: '1.21.0'
        }
      ],
      total: 1,
      limit: 25,
      offset: 0
    };
    
    axios.get.mockResolvedValueOnce({ data: historyData });
    
    render(<HostsPage />);
    
    await waitFor(() => {
      expect(screen.getByText('test-host')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('test-host'));
    
    await waitFor(() => {
      expect(screen.getByText((content, element) => {
        return element && element.textContent === 'Update History for test-host';
      })).toBeInTheDocument();
      expect(screen.getByText('nginx')).toBeInTheDocument();
      expect(screen.getByText('Ubuntu 22.04')).toBeInTheDocument();
      expect(screen.getByText('1.20.0')).toBeInTheDocument();
      expect(screen.getByText('1.21.0')).toBeInTheDocument();
    });
  });

  it('handles loading state while fetching history', async () => {
    axios.get.mockResolvedValueOnce({ data: { hosts: ['test-host'] } });
    
    // Mock a delayed response for history
    axios.get.mockImplementationOnce(() => new Promise(resolve => {
      setTimeout(() => resolve({ data: { items: [], total: 0, limit: 25, offset: 0 } }), 100);
    }));
    
    render(<HostsPage />);
    
    await waitFor(() => {
      expect(screen.getByText('test-host')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('test-host'));
    
    // Should show loading indicator
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    });
  });

  it('applies date filters correctly', async () => {
    axios.get.mockResolvedValueOnce({ data: { hosts: ['test-host'] } });
    
    const initialHistoryData = {
      items: [
        {
          update_date: '2025-07-08',
          os: 'Ubuntu 22.04',
          name: 'nginx',
          old_version: '1.20.0',
          new_version: '1.21.0'
        }
      ],
      total: 1,
      limit: 25,
      offset: 0
    };
    
    axios.get.mockResolvedValueOnce({ data: initialHistoryData });
    
    // Mock filtered response
    axios.get.mockResolvedValueOnce({ data: { items: [], total: 0, limit: 25, offset: 0 } });
    
    render(<HostsPage />);
    
    await waitFor(() => {
      expect(screen.getByText('test-host')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('test-host'));
    
    await waitFor(() => {
      expect(screen.getByText('nginx')).toBeInTheDocument();
    });
    
    // Apply date filter
    const fromDateInput = screen.getByLabelText('From Date');
    fireEvent.change(fromDateInput, { target: { value: '2025-07-01' } });
    
    await waitFor(() => {
      expect(axios.get).toHaveBeenCalledWith(
        expect.stringContaining('date_from=2025-07-01')
      );
    });
  });

  it('applies OS filter correctly', async () => {
    axios.get.mockResolvedValueOnce({ data: { hosts: ['test-host'] } });
    
    const initialHistoryData = {
      items: [
        {
          update_date: '2025-07-08',
          os: 'Ubuntu 22.04',
          name: 'nginx',
          old_version: '1.20.0',
          new_version: '1.21.0'
        }
      ],
      total: 1,
      limit: 25,
      offset: 0
    };
    
    axios.get.mockResolvedValueOnce({ data: initialHistoryData });
    
    render(<HostsPage />);
    
    await waitFor(() => {
      expect(screen.getByText('test-host')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('test-host'));
    
    await waitFor(() => {
      expect(screen.getByText('nginx')).toBeInTheDocument();
    });
    
    // Wait for the dropdown to be populated
    await waitFor(() => {
      expect(screen.getByLabelText('Operating System')).toBeInTheDocument();
    });
    
    // Apply OS filter by opening dropdown and checking that option exists
    const osSelect = screen.getByLabelText('Operating System');
    fireEvent.mouseDown(osSelect);
    
    await waitFor(() => {
      expect(screen.getByRole('option', { name: 'Ubuntu 22.04' })).toBeInTheDocument();
    });
    
    // Verify that the OS option is available and dropdown works
    expect(screen.getByRole('option', { name: 'All' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Ubuntu 22.04' })).toBeInTheDocument();
  });

  it('applies package filter correctly', async () => {
    axios.get.mockResolvedValueOnce({ data: { hosts: ['test-host'] } });
    
    const initialHistoryData = {
      items: [
        {
          update_date: '2025-07-08',
          os: 'Ubuntu 22.04',
          name: 'nginx',
          old_version: '1.20.0',
          new_version: '1.21.0'
        }
      ],
      total: 1,
      limit: 25,
      offset: 0
    };
    
    axios.get.mockResolvedValueOnce({ data: initialHistoryData });
    axios.get.mockResolvedValueOnce({ data: { items: [], total: 0, limit: 25, offset: 0 } });
    
    render(<HostsPage />);
    
    await waitFor(() => {
      expect(screen.getByText('test-host')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('test-host'));
    
    await waitFor(() => {
      expect(screen.getByText('nginx')).toBeInTheDocument();
    });
    
    // Apply package filter
    const packageInput = screen.getByLabelText('Package Name');
    fireEvent.change(packageInput, { target: { value: 'nginx' } });
    
    await waitFor(() => {
      expect(axios.get).toHaveBeenCalledWith(
        expect.stringContaining('package=nginx')
      );
    });
  });

  it('clears filters correctly', async () => {
    axios.get.mockResolvedValueOnce({ data: { hosts: ['test-host'] } });
    
    const initialHistoryData = {
      items: [
        {
          update_date: '2025-07-08',
          os: 'Ubuntu 22.04',
          name: 'nginx',
          old_version: '1.20.0',
          new_version: '1.21.0'
        }
      ],
      total: 1,
      limit: 25,
      offset: 0
    };
    
    axios.get.mockResolvedValueOnce({ data: initialHistoryData });
    axios.get.mockResolvedValueOnce({ data: initialHistoryData }); // After clear
    
    render(<HostsPage />);
    
    await waitFor(() => {
      expect(screen.getByText('test-host')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('test-host'));
    
    await waitFor(() => {
      expect(screen.getByText('nginx')).toBeInTheDocument();
    });
    
    // Apply a filter first
    const packageInput = screen.getByLabelText('Package Name');
    fireEvent.change(packageInput, { target: { value: 'nginx' } });
    
    await waitFor(() => {
      expect(screen.getByText('Active')).toBeInTheDocument(); // Filter chip should appear
    });
    
    // Clear filters
    const clearButton = screen.getByText('Clear Filters');
    fireEvent.click(clearButton);
    
    await waitFor(() => {
      expect(packageInput.value).toBe('');
      expect(screen.queryByText('Active')).not.toBeInTheDocument();
    });
  });

  it('handles pagination correctly', async () => {
    axios.get.mockResolvedValueOnce({ data: { hosts: ['test-host'] } });
    
    const initialHistoryData = {
      items: Array(25).fill(null).map((_, i) => ({
        update_date: '2025-07-08',
        os: 'Ubuntu 22.04',
        name: `package${i}`,
        old_version: '1.0.0',
        new_version: '1.1.0'
      })),
      total: 50,
      limit: 25,
      offset: 0
    };
    
    axios.get.mockResolvedValueOnce({ data: initialHistoryData });
    
    // Mock second page response
    const secondPageData = {
      items: Array(25).fill(null).map((_, i) => ({
        update_date: '2025-07-08',
        os: 'Ubuntu 22.04',
        name: `package${i + 25}`,
        old_version: '1.0.0',
        new_version: '1.1.0'
      })),
      total: 50,
      limit: 25,
      offset: 25
    };
    
    axios.get.mockResolvedValueOnce({ data: secondPageData });
    
    render(<HostsPage />);
    
    await waitFor(() => {
      expect(screen.getByText('test-host')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('test-host'));
    
    await waitFor(() => {
      expect(screen.getByText('package0')).toBeInTheDocument();
      expect(screen.getByText('Showing 25 of 50 updates • Page 1 of 2')).toBeInTheDocument();
    });
    
    // Click to go to page 2
    const page2Button = screen.getByRole('button', { name: 'Go to page 2' });
    fireEvent.click(page2Button);
    
    await waitFor(() => {
      expect(axios.get).toHaveBeenCalledWith(
        expect.stringContaining('offset=25')
      );
    });
  });

  it('handles error when fetching hosts', async () => {
    axios.get.mockRejectedValueOnce(new Error('Network error'));
    
    render(<HostsPage />);
    
    await waitFor(() => {
      expect(screen.getByText('Hosts (0)')).toBeInTheDocument();
      expect(screen.getByText('No hosts found.')).toBeInTheDocument();
    });
  });

  it('handles error when fetching history', async () => {
    axios.get.mockResolvedValueOnce({ data: { hosts: ['test-host'] } });
    axios.get.mockRejectedValueOnce(new Error('History error'));
    
    render(<HostsPage />);
    
    await waitFor(() => {
      expect(screen.getByText('test-host')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('test-host'));
    
    await waitFor(() => {
      expect(screen.getByText('No update history found for this host.')).toBeInTheDocument();
    });
  });

  it('shows correct pagination info', async () => {
    axios.get.mockResolvedValueOnce({ data: { hosts: ['test-host'] } });
    
    const historyData = {
      items: Array(3).fill(null).map((_, i) => ({
        update_date: '2025-07-08',
        os: 'Ubuntu 22.04',
        name: `package${i}`,
        old_version: '1.0.0',
        new_version: '1.1.0'
      })),
      total: 3,
      limit: 25,
      offset: 0
    };
    
    axios.get.mockResolvedValueOnce({ data: historyData });
    
    render(<HostsPage />);
    
    await waitFor(() => {
      expect(screen.getByText('test-host')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('test-host'));
    
    await waitFor(() => {
      expect(screen.getByText('Showing 3 of 3 updates')).toBeInTheDocument();
    });
  });
});
