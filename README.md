# FleetPulse

**FleetPulse** is a lightweight dashboard to monitor and audit Linux package updates across your fleet.  
It collects update reports (host, OS, date, packages upgraded, old/new versions) via a simple API and displays them in a modern, browser-friendly web UI.

Vibcoding for the win!

---

## Features

- 🚀 **FastAPI backend** with SQLite database
- ⚡ **React frontend** with Material UI for a modern look
- 💬 **Natural Language Chat**: Ask questions like "Which hosts had Python packages updated last week?"
- 📦 **Works with any OS**: Includes drop-in Ansible snippets for ArchLinux and Debian/Ubuntu
- 🐳 **Docker Compose**: One command to launch everything
- 👀 **Zero-config UI**: Open your browser and see updates at a glance

---

## Quickstart

1. **Clone the repo**

    ```bash
    git clone https://github.com/wesback/fleetpulse.git
    cd fleetpulse
    ```

2. **Configure data storage (optional)**

    By default, data is stored in `./data` directory. To customize the storage location:
    
    ```bash
    # Option 1: Set environment variable
    export FLEETPULSE_DATA_PATH=/your/preferred/path
    
    # Option 2: Copy and edit the environment file
    cp .env.example .env
    # Edit .env to set FLEETPULSE_DATA_PATH
    
    # Option 3: Create the directory and let Docker Compose use the default
    mkdir -p ./data
    ```

3. **Launch the stack**

    ```bash
    docker compose up --build -d
    ```

    - The **backend** runs on port **8000** (API)
    - The **frontend** runs on port **8080** (UI served by nginx)

4. **Open the dashboard:**  
   Visit [http://YOUR-HOST-IP:8080](http://YOUR-HOST-IP:8080) from any browser on your LAN.

---

## Using the Chat Interface

FleetPulse includes a natural language chat interface powered by intelligent query parsing. Click the **chat button** (💬) in the bottom-right corner to start asking questions about your package updates.

### Example Questions

- **"Which hosts had Python packages updated last week?"**
- **"What packages were updated on web-01?"**
- **"Show me Ubuntu hosts"**
- **"Which hosts haven't been updated in 30 days?"**
- **"How many hosts do we have?"**

### Supported Query Patterns

| Question Type | Example | What it does |
|---------------|---------|--------------|
| **Host Search** | "Which hosts had nginx updated last month?" | Finds hosts with specific package updates in a timeframe |
| **Package Lookup** | "What packages were updated on server-01?" | Shows all package updates for a specific host |
| **OS Filtering** | "Show me CentOS hosts" | Lists hosts running a specific operating system |
| **Stale Detection** | "Which hosts haven't been updated in 7 days?" | Identifies hosts that may need attention |
| **Fleet Status** | "How many Ubuntu hosts do we have?" | Provides counts and fleet statistics |

### Smart Features

- **Timeframe Detection**: Understands "last week", "past month", "7 days ago", etc.
- **Package Recognition**: Automatically detects common package names like Python, nginx, Docker
- **Hostname Extraction**: Finds hostnames in your questions (web-01, server-02, etc.)
- **Structured Results**: Displays both human-readable answers and clickable data chips
- **Error Handling**: Provides helpful suggestions when queries aren't understood

The chat interface integrates seamlessly with your existing FleetPulse data, making it easy to get insights without navigating through filters and tables.

---

## Deployment Configuration

FleetPulse is designed as a microservices architecture with separate frontend and backend containers for better scalability and maintainability.

### Architecture Overview

- **Frontend**: React application served by nginx on port 8080
- **Backend**: FastAPI application on port 8000
- **Communication**: Frontend proxies API calls to backend via nginx

### Backend Deployment Modes

The backend supports flexible deployment modes to match your specific use case:

### Backend Deployment Modes

#### **Uvicorn Mode (Default - Recommended)**
Single-process deployment optimized for simplicity and resource efficiency:

```bash
# Default in .env or docker-compose.yml
DEPLOYMENT_MODE=uvicorn
```

**Best for:**
- Single-container deployments
- Development environments  
- Low to medium traffic (< 100 concurrent users)
- Simplified setup and debugging
- Lower memory footprint

#### **Gunicorn Mode**
Multi-process deployment with enhanced fault tolerance:

```bash
# For high-traffic production deployments
DEPLOYMENT_MODE=gunicorn
GUNICORN_WORKERS=4  # Scale based on your needs
```

**Best for:**
- High-traffic production deployments (> 100 concurrent users)
- When you need process-level fault tolerance
- Multi-core CPU utilization requirements

### Service Configuration Examples

**Development:**
```bash
# docker-compose.yml or .env
DEPLOYMENT_MODE=uvicorn
FORCE_DB_RECREATE=true
```

**Production (simple):**
```bash
# docker-compose.yml or .env
DEPLOYMENT_MODE=uvicorn
FORCE_DB_RECREATE=false
```

**Production (high-traffic):**
```bash
# docker-compose.yml or .env
DEPLOYMENT_MODE=gunicorn
GUNICORN_WORKERS=4
FORCE_DB_RECREATE=false
```

### Docker Images

FleetPulse publishes separate Docker images for frontend and backend:

- **Backend**: `wesback/fleetpulse-backend:latest`
- **Frontend**: `wesback/fleetpulse-frontend:latest`

Use the provided `docker-compose.sample.yml` for production deployments with pre-built images.

**High-traffic production:**
```bash
DEPLOYMENT_MODE=gunicorn
GUNICORN_WORKERS=6
FORCE_DB_RECREATE=false
```

**Development:**
```bash
DEPLOYMENT_MODE=uvicorn
FORCE_DB_RECREATE=true  # Reset database on each startup
```

### Why We Default to Uvicorn

For FleetPulse's typical use case (fleet package update monitoring), the traffic patterns are:
- Periodic update reports from hosts
- Occasional dashboard access by administrators
- I/O-bound operations (database queries, static file serving)

Uvicorn provides excellent performance for this workload while being simpler to configure and debug.

---


For more details, see the `docker-compose.yml` and Dockerfiles in the repository.

---

## Reporting from Ansible

Add the relevant Ansible snippet to your playbooks and your updates will appear automatically in the FleetPulse dashboard!

### **ArchLinux Playbook Snippet**

```yaml
- name: Get pacman log timestamp before upgrade
  shell: date "+[%Y-%m-%dT%H:%M:%S"
  register: pacman_log_start
  changed_when: false

- name: Perform system upgrade
  pacman:
    upgrade: yes
    update_cache: yes
  register: upgrade_result

- name: Parse pacman.log for upgrades since playbook started
  shell: |
    awk -v start="{{ pacman_log_start.stdout }}" '
      $1 >= start && $3 == "upgraded" {
        match($0, /upgraded ([^ ]+) $begin:math:text$([^ ]+) -> ([^)]*)$end:math:text$/, a)
        if (a[1] && a[2] && a[3])
          print "{\"name\":\"" a[1] "\",\"old_version\":\"" a[2] "\",\"new_version\":\"" a[3] "\"}"
      }' /var/log/pacman.log | \
    paste -sd, - | sed 's/^/[/' | sed 's/$/]/'
  register: updated_packages_json
  changed_when: false

- name: POST upgraded packages to FleetPulse backend
  uri:
    url: "http://YOUR-BACKEND-IP:8000/report"
    method: POST
    headers:
      Content-Type: "application/json"
    body_format: json
    body: |
      {
        "hostname": "{{ inventory_hostname }}",
        "os": "archlinux",
        "update_date": "{{ pacman_log_start.stdout[1:11] }}",
        "updated_packages": {{ updated_packages_json.stdout | default('[]') | from_json }}
      }
    status_code: [200, 201]
  when: updated_packages_json.stdout != "[]"
```

---

## Running Tests

### Backend Tests

The backend tests use `pytest` and are located in `tests/backend/`.

1. (Recommended) Create and activate a Python virtual environment from the project root:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies (pytest is included in requirements.txt):
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Run the tests from the project root:
   ```bash
   pytest tests/backend/
   ```
   Or use the provided script (recommended - handles both backend and frontend):
   ```bash
   ./run_tests.sh
   ```

### Frontend Tests

The frontend tests use Jest and React Testing Library, located in `src/App.test.js`.

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```
2. Run the tests:
   ```bash
   npm test
   ```

**Note:** The `run_tests.sh` script automatically runs both backend and frontend tests for convenience.
