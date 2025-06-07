import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import axios from 'axios';
import App from './App';

jest.mock('axios');

describe('App', () => {
  beforeEach(() => {
    jest.clearAllMocks();
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
});
