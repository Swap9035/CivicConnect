# GFGBQ-Team-byteblazers

## 1️⃣ Problem Statement

### AI for Grievance Redressal in Public Governance

Public governance bodies receive thousands of citizen grievances every day, covering issues such as civic infrastructure, sanitation, public safety, utilities, healthcare, education, and administrative delays.

These complaints are typically:

- Unstructured (free-text, voice notes, mixed languages)
- Manually reviewed and routed
- Slow to resolve, leading to backlogs, citizen dissatisfaction, and lack of accountability

The absence of intelligent prioritization and analysis causes critical grievances to be delayed, while authorities struggle to gain actionable insights from large volumes of complaint data.

There is a pressing need for an AI-powered grievance redressal system that can intelligently understand, categorize, and prioritize citizen complaints to enable faster, fairer, and more transparent governance.

### Objective

Design and develop an AI-driven grievance redressal platform using Natural Language Processing (NLP) and intelligent automation that can:

- Automatically analyze and classify citizen complaints
- Prioritize grievances based on urgency, severity, and impact
- Route complaints to the appropriate department or authority
- Assist government bodies in resolving issues efficiently and transparently

## 2️⃣ Project Name

CivicConnect

## 3️⃣ Team Name

Byteblazers

## 4️⃣ 2-Minute Demonstration Video Link

[**Watch Demonstration Video**](https://drive.google.com/file/d/1ArKD4mOPePdYk0J_3rkWfVnKfTtnEtVC/view)
*(Note: Video contains cuts and is played at 2x speed to cover all features within 2 minutes)*

## 5️⃣ PPT Link

[**View Presentation (Canva)**](https://www.canva.com/design/DAG9bNV6rjE/wbwLyFcOsuLtx-y6SVkT7w/edit?utm_content=DAG9bNV6rjE&utm_campaign=designshare&utm_medium=link2&utm_source=sharebutton)

## ✅ Project Overview

Team Byteblazers presents a cutting-edge grievance management platform developed during the Vibe Coding Hackathon. This project leverages AI technologies to streamline grievance submission, analysis, and resolution processes. The platform is designed to enhance user experience for both citizens and officers, ensuring efficient and transparent grievance handling.

### Key Features

- **AI Receptionist**: A multi-channel intake system that uses NLP to instantly structure messy inputs (voice, text, images) into standard digital forms, eliminating manual data entry.
- **Intelligent Routing**: AI Agents automatically analyze context and route tickets to the exact department and officer instantly, ending the administrative "ping-pong" effect.
- **Automated Prioritization**: Real-time severity scoring ensures critical safety hazards (e.g., live wires) are flagged immediately for urgent action, separating them from routine issues.
- **Total Transparency**: An Anti-Corruption layer uses Computer Vision to verify "Before vs. After" photos, preventing "ghost resolutions" and restoring citizen trust.

## ✅ Setup & Installation Instructions

### Prerequisites

- Node.js (v16 or higher)
- Python (v3.9 or higher)
- Virtual Environment (venv)
- Git

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv myenv
   source myenv/bin/activate  # For Linux/Mac
   myenv\Scripts\activate   # For Windows
   ```
3. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up the environment variables:
   - Copy the `.env.example` file to `.env`:
     ```bash
     cp .env.example .env  # For Linux/Mac
     copy .env.example .env  # For Windows
     ```
   - Update the `.env` file with the required values.
5. Run the backend server:
   ```bash
   python main.py
   ```

### Frontend Setup

1. Navigate to the root directory:
   ```bash
   cd ..
   ```
2. Install the required Node.js packages:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```

## ✅ Usage Instructions

### Citizen Portal

1. **Dashboard**: Citizens can view their current grievances, track their status, and access previous grievances.
   - Navigate to the "Citizen Current" page to view ongoing grievances.
   - Use the "Citizen Previous" page to rate resolved grievances and provide feedback.
2. **Submit a Grievance**: Citizens can lodge new grievances through the "Citizen Portal" page.
   - Fill in the required details such as category, location, and description.
   - Optionally, upload supporting files or images.
   - Use the AI-powered form filling feature to ensure all necessary details are captured.
3. **Clarifications**: Respond to clarification requests from officers directly within the grievance details.

### Officer Dashboard

1. **Manage Tickets**: Officers can view assigned tickets, update their status, and resolve grievances.
   - Access the "Officer Dashboard" to see tickets categorized by status (e.g., Assigned, In Progress, Completed).
   - Use the "Resolve Ticket" feature to upload resolution details and photos.
2. **Clarifications**: Officers can request additional information from citizens and manage responses.

### Admin Dashboard

1. **User Management**: Admins can create, update, and manage users such as department admins and nodal officers.
   - Use the "Create User" modal to add new users.
   - Update user roles and jurisdictions as needed.
2. **Conflict Resolution**: Admins can view and resolve conflicts between departments.

### Contact & Helpdesk

1. Citizens can use the "Contact" page to send messages to the helpdesk for assistance.
2. The helpdesk will respond to queries and provide support as needed.

## ✅ Relevant Screenshots

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
