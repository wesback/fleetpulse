import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import axios from 'axios';
import App from './App';
import * as telemetry from './telemetry';

jest.mock('axios');

// Mock telemetry module completely to avoid OpenTelemetry dependency issues in tests
jest.mock('./telemetry');

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
    
    // Set up telemetry mocks
    const mockSpan = {
      setAttributes: jest.fn(),
      addEvent: jest.fn(),
      setStatus: jest.fn(),
      end: jest.fn(),
    };
    
    telemetry.initializeTelemetry.mockImplementation(() => {});
    telemetry.trackUserFlow.mockReturnValue(mockSpan);
    telemetry.trackApiCall.mockReturnValue(mockSpan);
    telemetry.trackComponentRender.mockReturnValue(mockSpan);
    telemetry.trackError.mockImplementation(() => {});
    telemetry.isTelemetryEnabled.mockReturnValue(false);
    telemetry.getTelemetryStatus.mockReturnValue({ enabled: false, initialized: false });
  });

  it('renders hosts list and handles empty state', async () => {
    axios.get.mockResolvedValueOnce({ data: { hosts: [] } });
    
    await act(async () => {
      render(<App />);
    });
    
    expect(await screen.findByText('No hosts yet.')).toBeInTheDocument();
  });

  it('renders hosts and allows selecting a host', async () => {
    axios.get.mockResolvedValueOnce({ data: { hosts: ['host1', 'host2'] } });
    
    await act(async () => {
      render(<App />);
    });
    
    expect(await screen.findByText('host1')).toBeInTheDocument();
    expect(screen.getByText('host2')).toBeInTheDocument();
  });

  it('shows update history for selected host', async () => {
    axios.get.mockResolvedValueOnce({ data: { hosts: ['host1'] } });
    axios.get.mockResolvedValueOnce({ data: [
      {
        update_date: '2025-06-07',
        os: 'Ubuntu',
        name: 'nginx',
        old_version: '1.18.0',
        new_version: '1.20.0',
      },
    ] });
    
    await act(async () => {
      render(<App />);
    });
    
    await act(async () => {
      fireEvent.click(await screen.findByText('host1'));
    });
    
    expect(await screen.findByText('Update History for')).toBeInTheDocument();
    expect(screen.getByText('nginx')).toBeInTheDocument();
    expect(screen.getByText('1.18.0')).toBeInTheDocument();
    expect(screen.getByText('1.20.0')).toBeInTheDocument();
  });

  it('shows message when no update history is found', async () => {
    axios.get.mockResolvedValueOnce({ data: { hosts: ['host1'] } });
    axios.get.mockResolvedValueOnce({ data: [] });
    
    await act(async () => {
      render(<App />);
    });
    
    await act(async () => {
      fireEvent.click(await screen.findByText('host1'));
    });
    
    expect(await screen.findByText('No update history found for this host.')).toBeInTheDocument();
  });

  it('shows loading indicator when fetching history', async () => {
    axios.get.mockResolvedValueOnce({ data: { hosts: ['host1'] } });
    let resolve;
    axios.get.mockReturnValueOnce(new Promise(r => { resolve = r; }));
    
    await act(async () => {
      render(<App />);
    });
    
    await act(async () => {
      fireEvent.click(await screen.findByText('host1'));
    });
    
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
    
    await act(async () => {
      resolve({ data: [] });
    });
    
    await waitFor(() => expect(screen.queryByRole('progressbar')).not.toBeInTheDocument());
  });

  it('renders dark mode toggle switch', async () => {
    axios.get.mockResolvedValueOnce({ data: { hosts: [] } });
    
    await act(async () => {
      render(<App />);
    });
    
    // Find the switch by its aria-label
    const darkModeSwitch = screen.getByLabelText('dark mode toggle');
    expect(darkModeSwitch).toBeInTheDocument();
  });

  it('toggles between light and dark mode', async () => {
    axios.get.mockResolvedValueOnce({ data: { hosts: [] } });
    
    await act(async () => {
      render(<App />);
    });
    
    const darkModeSwitch = screen.getByLabelText('dark mode toggle');
    
    // Initially should be light mode (switch unchecked)
    expect(darkModeSwitch).not.toBeChecked();
    
    // Click to toggle to dark mode
    await act(async () => {
      fireEvent.click(darkModeSwitch);
    });
    
    // Should now be checked (dark mode)
    expect(darkModeSwitch).toBeChecked();
    
    // Click again to toggle back to light mode
    await act(async () => {
      fireEvent.click(darkModeSwitch);
    });
    
    // Should be unchecked again (light mode)
    expect(darkModeSwitch).not.toBeChecked();
  });

  it('persists theme preference in localStorage', async () => {
    axios.get.mockResolvedValueOnce({ data: { hosts: [] } });
    
    await act(async () => {
      render(<App />);
    });
    
    const darkModeSwitch = screen.getByLabelText('dark mode toggle');
    
    // Toggle to dark mode
    await act(async () => {
      fireEvent.click(darkModeSwitch);
    });
    
    // Check that dark mode is stored in localStorage
    expect(localStorage.getItem('themeMode')).toBe('dark');
    
    // Toggle back to light mode
    await act(async () => {
      fireEvent.click(darkModeSwitch);
    });
    
    // Check that light mode is stored in localStorage
    expect(localStorage.getItem('themeMode')).toBe('light');
  });

  it('loads theme preference from localStorage', async () => {
    // Set dark mode in localStorage before rendering
    localStorage.setItem('themeMode', 'dark');
    
    axios.get.mockResolvedValueOnce({ data: { hosts: [] } });
    
    await act(async () => {
      render(<App />);
    });
    
    const darkModeSwitch = screen.getByLabelText('dark mode toggle');
    
    // Should be checked (dark mode) based on localStorage
    expect(darkModeSwitch).toBeChecked();
  });

  it('renders filter controls when host is selected', async () => {
    axios.get.mockResolvedValueOnce({ data: { hosts: ['host1'] } });
    axios.get.mockResolvedValueOnce({ data: [
      {
        update_date: '2025-06-07',
        os: 'Ubuntu',
        name: 'nginx',
        old_version: '1.18.0',
        new_version: '1.20.0',
      },
    ] });
    
    await act(async () => {
      render(<App />);
    });
    
    await act(async () => {
      fireEvent.click(await screen.findByText('host1'));
    });
    
    // Check for filter controls
    expect(await screen.findByText('Filters')).toBeInTheDocument();
    expect(screen.getByLabelText('From Date')).toBeInTheDocument();
    expect(screen.getByLabelText('To Date')).toBeInTheDocument();
    expect(screen.getAllByText('Operating System')[0]).toBeInTheDocument(); // Select first instance
    expect(screen.getByLabelText('Package Name')).toBeInTheDocument();
    expect(screen.getByText('Clear Filters')).toBeInTheDocument();
  });

  it('applies date filters when changed', async () => {
    axios.get.mockResolvedValueOnce({ data: { hosts: ['host1'] } });
    // First call for initial load
    axios.get.mockResolvedValueOnce({ data: [
      {
        update_date: '2025-06-07',
        os: 'Ubuntu',
        name: 'nginx',
        old_version: '1.18.0',
        new_version: '1.20.0',
      },
    ] });
    // Second call with date filter
    axios.get.mockResolvedValueOnce({ data: [] });
    
    await act(async () => {
      render(<App />);
    });
    
    await act(async () => {
      fireEvent.click(await screen.findByText('host1'));
    });
    
    // Wait for initial load
    await waitFor(() => expect(screen.getByText('nginx')).toBeInTheDocument());
    
    // Apply date filter
    const fromDateInput = screen.getByLabelText('From Date');
    await act(async () => {
      fireEvent.change(fromDateInput, { target: { value: '2025-06-08' } });
    });
    
    // Check that the API was called with the filter parameter
    await waitFor(() => {
      const lastCall = axios.get.mock.calls[axios.get.mock.calls.length - 1];
      expect(lastCall[0]).toContain('date_from=2025-06-08');
    });
  });

  it('applies package name filter when changed', async () => {
    axios.get.mockResolvedValueOnce({ data: { hosts: ['host1'] } });
    // First call for initial load
    axios.get.mockResolvedValueOnce({ data: [
      {
        update_date: '2025-06-07',
        os: 'Ubuntu',
        name: 'nginx',
        old_version: '1.18.0',
        new_version: '1.20.0',
      },
    ] });
    // Second call with package filter
    axios.get.mockResolvedValueOnce({ data: [] });
    
    await act(async () => {
      render(<App />);
    });
    
    await act(async () => {
      fireEvent.click(await screen.findByText('host1'));
    });
    
    // Wait for initial load
    await waitFor(() => expect(screen.getByText('nginx')).toBeInTheDocument());
    
    // Apply package filter
    const packageInput = screen.getByLabelText('Package Name');
    await act(async () => {
      fireEvent.change(packageInput, { target: { value: 'apache' } });
    });
    
    // Check that the API was called with the filter parameter
    await waitFor(() => {
      const lastCall = axios.get.mock.calls[axios.get.mock.calls.length - 1];
      expect(lastCall[0]).toContain('package=apache');
    });
  });

  it('clears all filters when clear button is clicked', async () => {
    axios.get.mockResolvedValueOnce({ data: { hosts: ['host1'] } });
    // First call for initial load
    axios.get.mockResolvedValueOnce({ data: [
      {
        update_date: '2025-06-07',
        os: 'Ubuntu',
        name: 'nginx',
        old_version: '1.18.0',
        new_version: '1.20.0',
      },
    ] });
    // Second call with package filter
    axios.get.mockResolvedValueOnce({ data: [] });
    // Third call after clearing filters
    axios.get.mockResolvedValueOnce({ data: [
      {
        update_date: '2025-06-07',
        os: 'Ubuntu',
        name: 'nginx',
        old_version: '1.18.0',
        new_version: '1.20.0',
      },
    ] });
    
    await act(async () => {
      render(<App />);
    });
    
    await act(async () => {
      fireEvent.click(await screen.findByText('host1'));
    });
    
    // Wait for initial load
    await waitFor(() => expect(screen.getByText('nginx')).toBeInTheDocument());
    
    // Apply package filter
    const packageInput = screen.getByLabelText('Package Name');
    await act(async () => {
      fireEvent.change(packageInput, { target: { value: 'apache' } });
    });
    
    // Clear filters
    const clearButton = screen.getByText('Clear Filters');
    await act(async () => {
      fireEvent.click(clearButton);
    });
    
    // Check that filters are cleared
    expect(packageInput.value).toBe('');
    
    // Check that the API was called without filter parameters
    await waitFor(() => {
      const lastCall = axios.get.mock.calls[axios.get.mock.calls.length - 1];
      expect(lastCall[0]).toBe('/api/history/host1');
    });
  });

  it('shows filtered message when filters are active', async () => {
    axios.get.mockResolvedValueOnce({ data: { hosts: ['host1'] } });
    // First call for initial load
    axios.get.mockResolvedValueOnce({ data: [
      {
        update_date: '2025-06-07',
        os: 'Ubuntu',
        name: 'nginx',
        old_version: '1.18.0',
        new_version: '1.20.0',
      },
    ] });
    // Second call with filter
    axios.get.mockResolvedValueOnce({ data: [
      {
        update_date: '2025-06-07',
        os: 'Ubuntu',
        name: 'nginx',
        old_version: '1.18.0',
        new_version: '1.20.0',
      },
    ] });
    
    await act(async () => {
      render(<App />);
    });
    
    await act(async () => {
      fireEvent.click(await screen.findByText('host1'));
    });
    
    // Wait for initial load
    await waitFor(() => expect(screen.getByText('nginx')).toBeInTheDocument());
    
    // Apply package filter
    const packageInput = screen.getByLabelText('Package Name');
    await act(async () => {
      fireEvent.change(packageInput, { target: { value: 'nginx' } });
    });
    
    // Check for active filter indicator and filtered results message
    await waitFor(() => {
      expect(screen.getByText('Active')).toBeInTheDocument();
      expect(screen.getByText('Showing 1 update (filtered)')).toBeInTheDocument();
    });
  });
});
