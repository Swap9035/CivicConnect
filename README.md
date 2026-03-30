<![CDATA[<div align="center">

# 🏛️ CivicConnect

### AI-Powered Grievance Redressal Platform for Public Governance

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![React](https://img.shields.io/badge/React-19.x-61DAFB?logo=react)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.128-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-8.0-47A248?logo=mongodb)](https://www.mongodb.com/)
[![Mistral AI](https://img.shields.io/badge/Mistral_AI-NLP-FF7000)](https://mistral.ai/)

[**Live Demo Video**](https://drive.google.com/file/d/1ArKD4mOPePdYk0J_3rkWfVnKfTtnEtVC/view) · [**Presentation**](https://www.canva.com/design/DAG9bNV6rjE/wbwLyFcOsuLtx-y6SVkT7w/edit?utm_content=DAG9bNV6rjE&utm_campaign=designshare&utm_medium=link2&utm_source=sharebutton) · [**Report Bug**](https://github.com/Swap9035/CivicConnect/issues) · [**Request Feature**](https://github.com/Swap9035/CivicConnect/issues)

</div>

---

## 📋 Table of Contents

- [Problem Statement](#-problem-statement)
- [Project Overview](#-project-overview)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Setup & Installation](#-setup--installation)
- [Usage](#-usage)
- [Screenshots](#-screenshots)
- [Contributors](#-contributors)

---

## 🎯 Problem Statement

> **AI for Grievance Redressal in Public Governance**

Public governance bodies receive thousands of citizen grievances every day, covering issues such as civic infrastructure, sanitation, public safety, utilities, healthcare, education, and administrative delays.

These complaints are typically:

- 📝 **Unstructured** — free-text, voice notes, mixed languages
- 🔄 **Manually reviewed** and routed
- 🐢 **Slow to resolve** — leading to backlogs, citizen dissatisfaction, and lack of accountability

### Objective

Design and develop an AI-driven grievance redressal platform using **NLP** and **intelligent automation** that can:

- ✅ Automatically analyze and classify citizen complaints
- ✅ Prioritize grievances based on urgency, severity, and impact
- ✅ Route complaints to the appropriate department or authority
- ✅ Assist government bodies in resolving issues efficiently and transparently

---

## 🚀 Project Overview

**Team Byteblazers** presents a cutting-edge grievance management platform developed during the **Vibe Coding Hackathon**. This project leverages AI technologies to streamline grievance submission, analysis, and resolution processes.

### ✨ Key Features

| Feature | Description |
|---|---|
| 🤖 **AI Receptionist** | Multi-channel intake system using NLP to structure messy inputs (voice, text, images) into standard digital forms |
| 🔀 **Intelligent Routing** | AI Agents automatically analyze context and route tickets to the exact department and officer |
| ⚡ **Automated Prioritization** | Real-time severity scoring flags critical safety hazards for urgent action |
| 🔍 **Visual Verification** | Anti-Corruption layer uses Computer Vision to verify "Before vs. After" photos, preventing "ghost resolutions" |

---

## 🛠️ Tech Stack

<table>
<tr>
<td align="center"><b>Frontend</b></td>
<td>React 19, Vite, TailwindCSS, React Router, Lucide Icons</td>
</tr>
<tr>
<td align="center"><b>Backend</b></td>
<td>FastAPI, Python 3.9+, Uvicorn</td>
</tr>
<tr>
<td align="center"><b>Database</b></td>
<td>MongoDB (Motor async driver)</td>
</tr>
<tr>
<td align="center"><b>AI/ML</b></td>
<td>Mistral AI, LangChain, LangGraph, ChromaDB</td>
</tr>
<tr>
<td align="center"><b>Auth</b></td>
<td>JWT (JSON Web Tokens), bcrypt</td>
</tr>
</table>

---

## 🏗️ Architecture

```
CivicConnect/
├── src/                    # React Frontend
│   ├── components/         # Reusable UI components
│   ├── pages/              # Page components
│   ├── services/           # API service layer
│   ├── context/            # Auth & state context
│   └── utils/              # Utility functions
├── backend/
│   ├── main.py             # FastAPI entry point
│   └── services/
│       ├── user_service/           # Citizen auth & profile
│       ├── AIFormFilling/          # AI-powered grievance intake
│       ├── AIAnalysis/             # Grievance analysis & routing
│       ├── superuser_services/     # Admin management
│       ├── OfficerResolutionService/ # Ticket resolution
│       ├── clarification_service/  # Officer-citizen communication
│       └── feedback_service/       # Feedback & conflict management
└── public/                 # Static assets
```

---

## ⚙️ Setup & Installation

### Prerequisites

- **Node.js** v16 or higher
- **Python** v3.9 or higher
- **MongoDB** (local or Atlas)
- **Git**

### 1. Clone the Repository

```bash
git clone https://github.com/Swap9035/CivicConnect.git
cd CivicConnect
```

### 2. Backend Setup

```bash
cd backend
python -m venv myenv

# Activate virtual environment
source myenv/bin/activate      # Linux/Mac
myenv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env           # Linux/Mac
copy .env.example .env         # Windows
```

Edit `backend/.env` with your actual values:

```env
MONGO_URI=mongodb://localhost:27017/grievance_db
MISTRAL_API_KEY=your_mistral_api_key_here
JWT_SECRET_KEY=your-secret-key
```

Start the backend:
```bash
python main.py
```
> Backend runs at `http://localhost:8000`

### 3. Frontend Setup

```bash
cd ..    # Back to root directory
npm install
```

Create a `.env` file in the root:
```env
VITE_API_BASE_URL=http://localhost:8000
```

Start the frontend:
```bash
npm run dev
```
> Frontend runs at `http://localhost:5173`

---

## 📖 Usage

### 👤 Citizen Portal
- **Dashboard** — View current grievances, track status, access previous grievances
- **Submit Grievance** — Lodge new complaints via text, voice, or image with AI-assisted form filling
- **Clarifications** — Respond to officer clarification requests

### 👮 Officer Dashboard
- **Manage Tickets** — View assigned tickets, update status, resolve grievances
- **Resolve with Proof** — Upload resolution details and "After" photos
- **Request Clarification** — Ask citizens for additional information

### 🔧 Admin Dashboard
- **User Management** — Create/manage department admins and nodal officers
- **Conflict Resolution** — View and resolve inter-department conflicts
- **System Monitoring** — Track overall platform performance

### Default Admin Credentials
| Field | Value |
|---|---|
| Email | `superadmin@gov.in` |
| Password | `TempAdmin@123` |

---

## 📸 Screenshots

### Citizen Portal
![Current Grievance](https://github.com/user-attachments/assets/cc86d266-c91f-4b6e-a0cb-c6d224adbb09)

### Officer Dashboard
![Officer Dashboard](https://github.com/user-attachments/assets/676a9c07-96f7-4ffd-9471-61d6c674055b)

### Clarification Portal
![Clarification Portal](https://github.com/user-attachments/assets/0559eff2-127f-4192-a4f3-44af002c1ed3)

### Grievance Submission
![Grievance Submission](https://github.com/user-attachments/assets/ba54d6e3-9add-40a2-96cd-aacb7493fdf7)

### Feedback Form
![Feedback Form](https://github.com/user-attachments/assets/0c3a3f40-c84e-48ff-be7c-4dda158733da)

### Admin Portal
![Admin Portal](https://github.com/user-attachments/assets/ab3c0713-64ba-4ee0-bd7b-90b174d44be4)

---

## 👥 Contributors

<table>
<tr>
<td align="center">
<a href="https://github.com/Swap9035">
<img src="https://github.com/Swap9035.png" width="100px;" alt="Swap9035"/><br />
<sub><b>Swap9035</b></sub>
</a>
</td>
<td align="center">
<a href="https://github.com/Himanshu-code1">
<img src="https://github.com/Himanshu-code1.png" width="100px;" alt="Himanshu-code1"/><br />
<sub><b>Himanshu-code1</b></sub>
</a>
</td>
<td align="center">
<a href="https://github.com/khanaa4">
<img src="https://github.com/khanaa4.png" width="100px;" alt="khanaa4"/><br />
<sub><b>khanaa4</b></sub>
</a>
</td>
<td align="center">
<a href="https://github.com/Adityapandey6969">
<img src="https://github.com/Adityapandey6969.png" width="100px;" alt="Adityapandey6969"/><br />
<sub><b>Adityapandey6969</b></sub>
</a>
</td>
</tr>
</table>

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with ❤️ by Team Byteblazers**

*🏛️ Empowering citizens through transparent and efficient governance technology*

</div>
]]>
