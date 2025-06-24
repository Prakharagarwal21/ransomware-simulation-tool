# Ransomware Simulation Tool

## Overview

This project simulates a **ransomware attack in a virtual hospital network** to analyze malware behavior and develop a real-time, automated detection system. It is designed as an educational and research tool for cybersecurity in healthcare environments.

---

## Virtual Environment Setup

We created a secure, isolated virtual network using **VMware Workstation**, consisting of:

- **Doctor VM (Windows 10)** – Primary infection point  
- **Nurse VM (Windows 10)** – Demonstrates lateral ransomware spread  
- **Ubuntu Server** – Hosts dummy Electronic Health Records (EHRs)  

**Network Isolation:**  
All VMs are connected through a host-only network to ensure isolation from the internet.  
**Connectivity:** Verified using `ping` (ICMP) commands between machines.

---

## Ransomware Simulation Script

### Features:
- **Written in Python**
- **Encrypts `.txt`, `.csv`, `.docx` files**
- **Uses AES (CTR mode) and RSA**
- **Tkinter-based GUI and command-line support**
- **Password-protected encryption**
- **Supports UNC paths for network share encryption**
- **Generates ransom notes**

### Example Commands:
```bash
python Ransomware.py "\\\\192.168.10.3\\hospitaldata" e 123456 for encryption
ipconfig 
ping 192.168.10.3
```

### FOLDER STRUCTURE
├── Ransomware.py
├── malware_signatures.txt
└── README.md
