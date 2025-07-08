import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter, useLocation } from 'react-router-dom';
import Navigation from './Navigation';

// Mock react-router-dom
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useLocation: jest.fn(),
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

const TestWrapper = ({ children }) => (
  <BrowserRouter>
    {children}
  </BrowserRouter>
);

describe('Navigation', () => {
  const mockToggleTheme = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    useLocation.mockReturnValue({ pathname: '/statistics' });
  });

  it('renders navigation with correct title', () => {
    render(
      <TestWrapper>
        <Navigation mode="light" toggleTheme={mockToggleTheme} />
      </TestWrapper>
    );

    expect(screen.getByText('FleetPulse — Linux Fleet Package Dashboard')).toBeInTheDocument();
  });

  it('renders navigation tabs', () => {
    render(
      <TestWrapper>
        <Navigation mode="light" toggleTheme={mockToggleTheme} />
      </TestWrapper>
    );

    expect(screen.getByText('Statistics')).toBeInTheDocument();
    expect(screen.getByText('Hosts')).toBeInTheDocument();
  });

  it('shows correct active tab for statistics page', () => {
    useLocation.mockReturnValue({ pathname: '/statistics' });
    
    render(
      <TestWrapper>
        <Navigation mode="light" toggleTheme={mockToggleTheme} />
      </TestWrapper>
    );

    const statisticsTab = screen.getByText('Statistics').closest('button');
    const hostsTab = screen.getByText('Hosts').closest('button');

    expect(statisticsTab).toHaveClass('Mui-selected');
    expect(hostsTab).not.toHaveClass('Mui-selected');
  });

  it('shows correct active tab for hosts page', () => {
    useLocation.mockReturnValue({ pathname: '/hosts' });
    
    render(
      <TestWrapper>
        <Navigation mode="light" toggleTheme={mockToggleTheme} />
      </TestWrapper>
    );

    const statisticsTab = screen.getByText('Statistics').closest('button');
    const hostsTab = screen.getByText('Hosts').closest('button');

    expect(statisticsTab).not.toHaveClass('Mui-selected');
    expect(hostsTab).toHaveClass('Mui-selected');
  });

  it('navigates to statistics page when statistics tab is clicked', () => {
    useLocation.mockReturnValue({ pathname: '/hosts' });
    
    render(
      <TestWrapper>
        <Navigation mode="light" toggleTheme={mockToggleTheme} />
      </TestWrapper>
    );

    const statisticsTab = screen.getByText('Statistics').closest('button');
    fireEvent.click(statisticsTab);

    expect(mockNavigate).toHaveBeenCalledWith('/statistics');
  });

  it('navigates to hosts page when hosts tab is clicked', () => {
    useLocation.mockReturnValue({ pathname: '/statistics' });
    
    render(
      <TestWrapper>
        <Navigation mode="light" toggleTheme={mockToggleTheme} />
      </TestWrapper>
    );

    const hostsTab = screen.getByText('Hosts').closest('button');
    fireEvent.click(hostsTab);

    expect(mockNavigate).toHaveBeenCalledWith('/hosts');
  });

  it('renders theme toggle in light mode', () => {
    render(
      <TestWrapper>
        <Navigation mode="light" toggleTheme={mockToggleTheme} />
      </TestWrapper>
    );

    const themeToggle = screen.getByRole('checkbox');
    expect(themeToggle).not.toBeChecked();
  });

  it('renders theme toggle in dark mode', () => {
    render(
      <TestWrapper>
        <Navigation mode="dark" toggleTheme={mockToggleTheme} />
      </TestWrapper>
    );

    const themeToggle = screen.getByRole('checkbox');
    expect(themeToggle).toBeChecked();
  });

  it('calls toggleTheme when theme toggle is clicked', () => {
    render(
      <TestWrapper>
        <Navigation mode="light" toggleTheme={mockToggleTheme} />
      </TestWrapper>
    );

    const themeToggle = screen.getByRole('checkbox');
    fireEvent.click(themeToggle);

    expect(mockToggleTheme).toHaveBeenCalledTimes(1);
  });

  it('renders correct icons for tabs', () => {
    render(
      <TestWrapper>
        <Navigation mode="light" toggleTheme={mockToggleTheme} />
      </TestWrapper>
    );

    // Check that icon elements are present (icons are rendered as SVG elements)
    const statisticsTab = screen.getByText('Statistics').closest('button');
    const hostsTab = screen.getByText('Hosts').closest('button');

    expect(statisticsTab.querySelector('svg')).toBeInTheDocument();
    expect(hostsTab.querySelector('svg')).toBeInTheDocument();
  });

  it('renders storage icon in app bar', () => {
    render(
      <TestWrapper>
        <Navigation mode="light" toggleTheme={mockToggleTheme} />
      </TestWrapper>
    );

    const appBar = screen.getByRole('banner');
    expect(appBar.querySelector('svg')).toBeInTheDocument();
  });

  it('renders theme icons correctly', () => {
    const { rerender } = render(
      <TestWrapper>
        <Navigation mode="light" toggleTheme={mockToggleTheme} />
      </TestWrapper>
    );

    // In light mode, should show sun icon
    expect(screen.getByTestId('Brightness7Icon')).toBeInTheDocument();

    // Switch to dark mode
    rerender(
      <TestWrapper>
        <Navigation mode="dark" toggleTheme={mockToggleTheme} />
      </TestWrapper>
    );

    // In dark mode, should show moon icon
    expect(screen.getByTestId('Brightness4Icon')).toBeInTheDocument();
  });

  it('handles unknown route correctly', () => {
    useLocation.mockReturnValue({ pathname: '/unknown' });
    
    render(
      <TestWrapper>
        <Navigation mode="light" toggleTheme={mockToggleTheme} />
      </TestWrapper>
    );

    // Should still render without errors
    expect(screen.getByText('Statistics')).toBeInTheDocument();
    expect(screen.getByText('Hosts')).toBeInTheDocument();
  });

  it('maintains theme toggle state correctly', () => {
    const { rerender } = render(
      <TestWrapper>
        <Navigation mode="light" toggleTheme={mockToggleTheme} />
      </TestWrapper>
    );

    const themeToggle = screen.getByRole('checkbox');
    expect(themeToggle).not.toBeChecked();

    // Simulate theme change
    rerender(
      <TestWrapper>
        <Navigation mode="dark" toggleTheme={mockToggleTheme} />
      </TestWrapper>
    );

    expect(themeToggle).toBeChecked();
  });
});
