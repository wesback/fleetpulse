import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  useTheme,
} from '@mui/material';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
} from 'chart.js';
import { Bar, Line, Doughnut } from 'react-chartjs-2';
import axios from 'axios';
import 'chartjs-adapter-date-fns';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  TimeScale
);

const API_BASE = '/api';

/**
 * Statistics page component showing various analytics and charts
 */
const StatisticsPage = () => {
  const [statistics, setStatistics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const theme = useTheme();

  useEffect(() => {
    fetchStatistics();
  }, []);

  const fetchStatistics = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get(`${API_BASE}/statistics`);
      setStatistics(response.data);
    } catch (err) {
      console.error('Error fetching statistics:', err);
      setError(err.response?.data?.detail || 'Failed to load statistics');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      </Container>
    );
  }

  if (!statistics) {
    return null;
  }

  // Chart color schemes based on theme
  const chartColors = {
    primary: theme.palette.primary.main,
    secondary: theme.palette.secondary.main,
    success: theme.palette.success.main,
    warning: theme.palette.warning.main,
    error: theme.palette.error.main,
    info: theme.palette.info.main,
  };

  const backgroundColors = [
    chartColors.primary,
    chartColors.secondary,
    chartColors.success,
    chartColors.warning,
    chartColors.error,
    chartColors.info,
    '#FF6384',
    '#36A2EB',
    '#FFCE56',
    '#4BC0C0',
  ];

  // Timeline chart data
  const timelineData = {
    labels: statistics.updates_timeline.map(item => item.date),
    datasets: [
      {
        label: 'Package Updates',
        data: statistics.updates_timeline.map(item => item.count),
        borderColor: chartColors.primary,
        backgroundColor: chartColors.primary + '20',
        borderWidth: 2,
        fill: true,
        tension: 0.4,
      },
    ],
  };

  // Top packages chart data
  const topPackagesData = {
    labels: statistics.top_packages.map(pkg => pkg.name),
    datasets: [
      {
        label: 'Number of Updates',
        data: statistics.top_packages.map(pkg => pkg.count),
        backgroundColor: backgroundColors.slice(0, statistics.top_packages.length),
        borderColor: backgroundColors.slice(0, statistics.top_packages.length),
        borderWidth: 1,
      },
    ],
  };

  // OS distribution chart data
  const osDistributionData = {
    labels: statistics.updates_by_os.map(os => os.os),
    datasets: [
      {
        label: 'Updates by OS',
        data: statistics.updates_by_os.map(os => os.count),
        backgroundColor: backgroundColors.slice(0, statistics.updates_by_os.length),
        borderColor: backgroundColors.slice(0, statistics.updates_by_os.length),
        borderWidth: 2,
      },
    ],
  };

  // Host activity chart data
  const hostActivityData = {
    labels: statistics.host_activity.map(host => host.hostname),
    datasets: [
      {
        label: 'Total Updates',
        data: statistics.host_activity.map(host => host.count),
        backgroundColor: chartColors.info,
        borderColor: chartColors.info,
        borderWidth: 1,
      },
    ],
  };

  // Chart options
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          precision: 0,
        },
      },
    },
  };

  const timelineOptions = {
    ...chartOptions,
    scales: {
      x: {
        type: 'time',
        time: {
          unit: 'day',
        },
      },
      y: {
        beginAtZero: true,
        ticks: {
          precision: 0,
        },
      },
    },
  };

  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right',
      },
    },
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Fleet Statistics
      </Typography>
      
      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Hosts
              </Typography>
              <Typography variant="h4">
                {statistics.total_hosts}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Updates
              </Typography>
              <Typography variant="h4">
                {statistics.total_updates.toLocaleString()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Recent Updates
              </Typography>
              <Typography variant="h4">
                {statistics.recent_updates.toLocaleString()}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Last 30 days
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Active Percentage
              </Typography>
              <Typography variant="h4">
                {statistics.total_hosts > 0 
                  ? Math.round((statistics.recent_updates / statistics.total_updates) * 100) 
                  : 0}%
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Recent activity
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3}>
        {/* Updates Timeline */}
        <Grid size={{ xs: 12, lg: 8 }}>
          <Paper elevation={2} sx={{ p: 2, height: 400 }}>
            <Typography variant="h6" gutterBottom>
              Updates Timeline (Last 30 Days)
            </Typography>
            <Box sx={{ height: 300 }}>
              <Line data={timelineData} options={timelineOptions} />
            </Box>
          </Paper>
        </Grid>

        {/* OS Distribution */}
        <Grid size={{ xs: 12, lg: 4 }}>
          <Paper elevation={2} sx={{ p: 2, height: 400 }}>
            <Typography variant="h6" gutterBottom>
              Updates by Operating System
            </Typography>
            <Box sx={{ height: 300 }}>
              <Doughnut data={osDistributionData} options={doughnutOptions} />
            </Box>
          </Paper>
        </Grid>

        {/* Top Packages */}
        <Grid size={{ xs: 12, lg: 6 }}>
          <Paper elevation={2} sx={{ p: 2, height: 400 }}>
            <Typography variant="h6" gutterBottom>
              Most Updated Packages
            </Typography>
            <Box sx={{ height: 300 }}>
              <Bar data={topPackagesData} options={chartOptions} />
            </Box>
          </Paper>
        </Grid>

        {/* Host Activity */}
        <Grid size={{ xs: 12, lg: 6 }}>
          <Paper elevation={2} sx={{ p: 2, height: 400 }}>
            <Typography variant="h6" gutterBottom>
              Most Active Hosts
            </Typography>
            <Box sx={{ height: 300 }}>
              <Bar data={hostActivityData} options={chartOptions} />
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default StatisticsPage;
