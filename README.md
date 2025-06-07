# FleetPulse

**FleetPulse** is a lightweight dashboard to monitor and audit Linux package updates across your fleet.  
It collects update reports (host, OS, date, packages upgraded, old/new versions) via a simple API and displays them in a modern, browser-friendly web UI.

---

## Features

- 🚀 **FastAPI backend** with SQLite database (or switchable to Postgres)
- ⚡ **React frontend** with Material UI for a modern look
- 📦 **Works with any OS**: Includes drop-in Ansible snippets for ArchLinux and Debian/Ubuntu
- 🐳 **Docker Compose**: One command to launch everything
- 🔒 **Prevents duplicate upgrade records per host/package/day**
- 👀 **Zero-config UI**: Open your browser and see updates at a glance

---

## Quickstart

1. **Clone the repo**

    ```bash
    git clone https://github.com/wesback/fleetpulse.git
    cd fleetpulse
    ```

2. **Set up Docker volumes (optional, for persistent storage)**

    ```bash
    mkdir -p /mnt/data/dockervolumes/fleetpulse
    ```

3. **Launch the stack**

    ```bash
    docker compose up --build -d
    ```

    - The **backend** runs on port **8000** (API)
    - The **frontend** runs on port **8080** (UI)

4. **Open the dashboard:**  
   Visit [http://YOUR-HOST-IP:8080](http://YOUR-HOST-IP:8080) from any browser on your LAN.

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
        "date": "{{ pacman_log_start.stdout[1:11] }}",
        "updated_packages": {{ updated_packages_json.stdout | default('[]') | from_json }}
      }
    status_code: 200
  when: updated_packages_json.stdout != "[]"
