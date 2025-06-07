import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import axios from 'axios';
import App from './App';

jest.mock('axios');

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

  it('renders hosts list and handles empty state', async () => {
    axios.get.mockResolvedValueOnce({ data: { hosts: [] } });
    render(<App />);
    expect(await screen.findByText('No hosts yet.')).toBeInTheDocument();
  });

  it('renders hosts and allows selecting a host', async () => {
    axios.get.mockResolvedValueOnce({ data: { hosts: ['host1', 'host2'] } });
    render(<App />);
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
    render(<App />);
    fireEvent.click(await screen.findByText('host1'));
    expect(await screen.findByText('Update History for')).toBeInTheDocument();
    expect(screen.getByText('nginx')).toBeInTheDocument();
    expect(screen.getByText('1.18.0')).toBeInTheDocument();
    expect(screen.getByText('1.20.0')).toBeInTheDocument();
  });

  it('shows message when no update history is found', async () => {
    axios.get.mockResolvedValueOnce({ data: { hosts: ['host1'] } });
    axios.get.mockResolvedValueOnce({ data: [] });
    render(<App />);
    fireEvent.click(await screen.findByText('host1'));
    expect(await screen.findByText('No update history found for this host.')).toBeInTheDocument();
  });

  it('shows loading indicator when fetching history', async () => {
    axios.get.mockResolvedValueOnce({ data: { hosts: ['host1'] } });
    let resolve;
    axios.get.mockReturnValueOnce(new Promise(r => { resolve = r; }));
    render(<App />);
    fireEvent.click(await screen.findByText('host1'));
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
    resolve({ data: [] });
    await waitFor(() => expect(screen.queryByRole('progressbar')).not.toBeInTheDocument());
  });

  it('renders dark mode toggle switch', async () => {
    axios.get.mockResolvedValueOnce({ data: { hosts: [] } });
    render(<App />);
    
    // Find the switch by its aria-label
    const darkModeSwitch = screen.getByLabelText('dark mode toggle');
    expect(darkModeSwitch).toBeInTheDocument();
  });

  it('toggles between light and dark mode', async () => {
    axios.get.mockResolvedValueOnce({ data: { hosts: [] } });
    render(<App />);
    
    const darkModeSwitch = screen.getByLabelText('dark mode toggle');
    
    // Initially should be light mode (switch unchecked)
    expect(darkModeSwitch).not.toBeChecked();
    
    // Click to toggle to dark mode
    fireEvent.click(darkModeSwitch);
    
    // Should now be checked (dark mode)
    expect(darkModeSwitch).toBeChecked();
    
    // Click again to toggle back to light mode
    fireEvent.click(darkModeSwitch);
    
    // Should be unchecked again (light mode)
    expect(darkModeSwitch).not.toBeChecked();
  });

  it('persists theme preference in localStorage', async () => {
    axios.get.mockResolvedValueOnce({ data: { hosts: [] } });
    render(<App />);
    
    const darkModeSwitch = screen.getByLabelText('dark mode toggle');
    
    // Toggle to dark mode
    fireEvent.click(darkModeSwitch);
    
    // Check that dark mode is stored in localStorage
    expect(localStorage.getItem('themeMode')).toBe('dark');
    
    // Toggle back to light mode
    fireEvent.click(darkModeSwitch);
    
    // Check that light mode is stored in localStorage
    expect(localStorage.getItem('themeMode')).toBe('light');
  });

  it('loads theme preference from localStorage', async () => {
    // Set dark mode in localStorage before rendering
    localStorage.setItem('themeMode', 'dark');
    
    axios.get.mockResolvedValueOnce({ data: { hosts: [] } });
    render(<App />);
    
    const darkModeSwitch = screen.getByLabelText('dark mode toggle');
    
    // Should be checked (dark mode) based on localStorage
    expect(darkModeSwitch).toBeChecked();
  });
});
