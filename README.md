# 🏥 PathoScope – Hospital Infection Control & Surveillance System

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18.0+-blue)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)](https://fastapi.tiangolo.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue)](https://www.typescriptlang.org/)

---

## 🧬 Overview

**PathoScope** is a comprehensive, secure web application designed for hospital infection control teams to manage verified MDR (Multi-Drug Resistant) infection cases, issue TEK (Temporary Exposure Key) verification tokens, and analyze anonymized exposure data through real-time surveillance dashboards.

The system serves as a centralized console for authorized ICT (Infection Control Team) members, providing tools for infection case entry, TEK token generation and management, and analytics dashboards for monitoring infection patterns and system health.

---

## ✨ Key Features

### 🔐 Verification & Reporting Module (ICT Access-Controlled)
- **Infection Case Entry**: Input verified positive MDR test details with non-identifying patient/staff IDs
- **TEK Verification Token Generation**: Generate cryptographically secure, single-use tokens for confirmed cases
- **Multiple Delivery Methods**: Issue tokens via HIS system, secure SMS, or email gateway
- **TEK Management Dashboard**: Track uploaded TEKs, monitor pending/failed uploads, and manage expiration policies

### 📊 Surveillance & Analytics Dashboard (Aggregate, Non-Identifying Data)
- **Real-Time KPIs**: Monitor total risk alerts, TEK upload compliance rates, and active cases
- **Anonymized Cluster Visualization**: Temporal/spatial exposure maps with ward-level heatmapping
- **System Integrity Monitoring**: Real-time monitoring of verification and distribution servers
- **Comprehensive Audit Trails**: Track all verification token issuances and administrative actions

### 🛡️ Security & Compliance
- **Role-Based Access Control**: Three-tier permission system (ICT Admin, ICT Member, Viewer)
- **Healthcare Data Protection**: AES-256 encryption, secure token management, and HIPAA-aligned privacy safeguards
- **Multi-Factor Authentication**: TOTP-based MFA for administrative roles
- **Comprehensive Audit Logging**: Complete audit trail for compliance requirements

---

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React/Next.js │    │   FastAPI/Python│    │   PostgreSQL    │
│   Frontend      │◄──►│   Backend API   │◄──►│   Database      │
│                 │    │                 │    │                 │
│ - Dashboard     │    │ - Auth Service  │    │ - User Data     │
│ - Case Forms    │    │ - Case API      │    │ - Cases         │
│ - Analytics     │    │ - Token Service │    │ - Tokens        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Redis Cache   │
                    │   (Sessions)    │
                    └─────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### 🐳 Docker Setup (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd PathoScope
   ```

2. **Run the setup script**
   ```bash
   chmod +x scripts/setup.sh
   ./scripts/setup.sh
   ```

3. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/api/docs

### Default Login Credentials
- Email: `admin@pathoscope.hospital`
- Password: `Admin123!`

---

## 🛠️ Development Setup

### Backend (FastAPI)

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run the development server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend (Next.js)

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Set up environment variables**
   ```bash
   cp .env.local.example .env.local
   # Edit .env.local with your configuration
   ```

4. **Run the development server**
   ```bash
   npm run dev
   ```

---

## 📂 Project Structure

```
PathoScope/
├── frontend/                    # Next.js React application
│   ├── src/
│   │   ├── app/                # Next.js 13+ app router
│   │   ├── components/         # Reusable UI components
│   │   ├── contexts/           # React contexts (auth, etc.)
│   │   ├── services/           # API integration services
│   │   └── types/              # TypeScript type definitions
│   └── package.json
├── backend/                     # FastAPI Python application
│   ├── app/
│   │   ├── api/v1/            # API route handlers
│   │   ├── core/              # Core application logic
│   │   ├── models/            # Database models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic services
│   │   └── main.py           # FastAPI application entry
│   ├── requirements.txt
│   └── Dockerfile
├── shared/                      # Shared types and utilities
├── scripts/                     # Setup and utility scripts
│   ├── setup.sh               # Development environment setup
│   └── init-db.sql            # Database initialization
├── docker-compose.yml           # Docker development environment
└── README.md
```

---

## 🏥 User Roles & Permissions

### ICT Administrator
- Full system access
- User management
- System configuration
- Complete audit trail access

### ICT Member
- Create and verify infection cases
- Generate TEK verification tokens
- Access all surveillance dashboards
- View and acknowledge alerts

### Viewer
- Read-only access to verified data
- View surveillance dashboards
- Access compliance reports

---

## 🔒 Security Features

- **Authentication**: JWT-based stateless authentication with refresh tokens
- **Authorization**: Role-based access control (RBAC) with fine-grained permissions
- **Session Management**: Secure token-based sessions with automatic logout
- **Account Security**: Account lockout after failed attempts, MFA for admin roles
- **Data Protection**: AES-256 encryption, TLS 1.3 for all communications
- **Audit Logging**: Comprehensive logging of all system actions
- **HIPAA Alignment**: Privacy and security safeguards for healthcare data

---

## 📊 Key API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/logout` - User logout
- `GET /api/v1/auth/me` - Get current user profile
- `POST /api/v1/auth/change-password` - Change password

### Infection Cases
- `GET /api/v1/cases` - List infection cases
- `POST /api/v1/cases` - Create new infection case
- `PUT /api/v1/cases/{id}` - Update infection case
- `POST /api/v1/cases/{id}/verify` - Verify infection case

### Verification Tokens
- `GET /api/v1/tokens` - List verification tokens
- `POST /api/v1/tokens` - Generate verification token
- `POST /api/v1/tokens/{id}/revoke` - Revoke verification token
- `GET /api/v1/tokens/{id}/status` - Check token status

### Analytics & Dashboard
- `GET /api/v1/analytics/kpi` - Get KPI metrics
- `GET /api/v1/dashboard/overview` - Get dashboard overview
- `GET /api/v1/dashboard/system-health` - Get system health status

---

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

---

## 📈 Monitoring & Maintenance

### Health Checks
- Backend: `GET /health`
- System health monitoring via dashboard
- Automated service health checks

### Database
- Automatic backup scripts
- Data retention policies
- Performance monitoring

### Security
- Regular security audits
- Access log monitoring
- Automated security updates

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

Built with healthcare compliance standards in mind, designed to support infection control teams in their critical mission to prevent and control hospital-acquired infections.

Inspired by modern epidemiological surveillance systems and digital contact tracing frameworks adapted for healthcare environments.

---

## 📞 Support

For support and questions:
- Create an issue in the GitHub repository
- Consult the API documentation at `/api/docs`
- Review the audit logs for system diagnostics

---

**PathoScope** - Empowering infection control teams with intelligent surveillance and rapid response capabilities. 🦠