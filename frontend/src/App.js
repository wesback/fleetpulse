import React, { useEffect, useState } from 'react';
import axios from 'axios';
import {
  Container,
  Typography,
  Box,
  Paper,
  List,
  ListItemButton,
  ListItemText,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  AppBar,
  Toolbar,
  CircularProgress,
  CssBaseline,
} from '@mui/material';
import StorageIcon from '@mui/icons-material/Storage';
import DnsIcon from '@mui/icons-material/Dns';

const API_BASE = '';

function App() {
  const [hosts, setHosts] = useState([]);
  const [selectedHost, setSelectedHost] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    axios.get(`${API_BASE}/hosts`)
      .then(res => setHosts(res.data.hosts));
  }, []);

  const fetchHistory = (host) => {
    setLoading(true);
    setSelectedHost(host);
    axios.get(`${API_BASE}/history/${host}`)
      .then(res => setHistory(res.data))
      .finally(() => setLoading(false));
  };

  return (
    <>
      <CssBaseline />
      <AppBar position="static" sx={{ marginBottom: 4 }}>
        <Toolbar>
          <StorageIcon sx={{ marginRight: 2 }} />
          <Typography variant="h6" component="div">
            FleetPulse &mdash; Linux Fleet Package Dashboard
          </Typography>
        </Toolbar>
      </AppBar>
      <Container maxWidth="md">
        <Box sx={{ display: 'flex', gap: 4 }}>
          <Paper elevation={2} sx={{ width: 250, minHeight: 400, padding: 2 }}>
            <Typography variant="h6" gutterBottom>
              <DnsIcon sx={{ verticalAlign: 'middle', mr: 1 }} />
              Hosts
            </Typography>
            <List>
              {hosts.length === 0 && (
                <Typography variant="body2">No hosts yet.</Typography>
              )}
              {hosts.map(host =>
                <ListItemButton
                  key={host}
                  selected={selectedHost === host}
                  onClick={() => fetchHistory(host)}
                >
                  <ListItemText primary={host} />
                </ListItemButton>
              )}
            </List>
          </Paper>
          <Box sx={{ flexGrow: 1 }}>
            {selectedHost && (
              <Paper elevation={2} sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Update History for <b>{selectedHost}</b>
                </Typography>
                {loading ? (
                  <CircularProgress />
                ) : (
                  <>
                    {history.length === 0 ? (
                      <Typography variant="body2">
                        No update history found for this host.
                      </Typography>
                    ) : (
                      <TableContainer component={Paper}>
                        <Table size="small">
                          <TableHead>
                            <TableRow>
                              <TableCell>Date</TableCell>
                              <TableCell>OS</TableCell>
                              <TableCell>Package</TableCell>
                              <TableCell>Old Version</TableCell>
                              <TableCell>New Version</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {history.map((rec, i) => (
                              <TableRow key={i}>
                                <TableCell>{rec.update_date}</TableCell>
                                <TableCell>{rec.os}</TableCell>
                                <TableCell>{rec.name}</TableCell>
                                <TableCell>{rec.old_version}</TableCell>
                                <TableCell>{rec.new_version}</TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </TableContainer>
                    )}
                  </>
                )}
              </Paper>
            )}
            {!selectedHost && (
              <Paper elevation={2} sx={{ p: 2 }}>
                <Typography variant="body1" color="text.secondary">
                  Select a host to view its update history.
                </Typography>
              </Paper>
            )}
          </Box>
        </Box>
      </Container>
    </>
  );
}

export default App;
