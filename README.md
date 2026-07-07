# 🔍 Same File Detector

![Python](https://img.shields.io/badge/Python-3.x-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![OCR](https://img.shields.io/badge/OCR-Tesseract-orange)
![Docker](https://img.shields.io/badge/Docker-Supported-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

## AI-Powered Document Similarity & Duplicate File Detection System

Same File Detector is an intelligent document comparison platform that detects duplicate and similar files using OCR, text extraction, and fuzzy similarity matching.

Users can upload **BASE files** and **COMPARE files**, and the system analyzes their content to classify documents as:

* ✅ EXACT
* ⚠️ SIMILAR
* ❌ DIFFERENT

The system supports multiple document formats including:

* PDF
* DOCX
* XLSX
* PPTX
* TXT
* CSV
* JSON
* Images

---

# 📸 Application Preview

## 🔐 Authentication

### Sign In

![Sign In](assets/sign_in.jpg)

### Create Account

![Create Account](assets/create_account.jpg)

### Email Verification (OTP)

![Verify Email](assets/verify_email.jpg)

### Reset Password

![Reset Password](assets/reset_password.jpg)

---

# 👤 User Interface

### Empty User Dashboard

![User Dashboard](assets/user_dashboard_empty.jpg)

### Select Files For Comparison

![Files Selected](assets/user_files_selected.jpg)

### Comparison Results

![Comparison Results](assets/comparison_results.jpg)

---

# 👨‍💼 Admin Panel

### Admin Dashboard

![Admin Dashboard](assets/admin_dashboard.jpg)

### User Management - Light Theme

![User Management Light](assets/admin_user_management_light.jpg)

### User Management - Dark Theme

![User Management Dark](assets/admin_user_management_dark.jpg)

---

# 📚 API Documentation

Built-in Swagger documentation powered by FastAPI.

### Swagger Overview

![Swagger Overview](assets/api_docs_overview.jpg)

### Authentication, Admin & Compare APIs

![Swagger Auth Admin Compare](assets/api_docs_auth_admin_compare.jpg)

### Admin Compare UI APIs

![Swagger Admin Compare UI](assets/api_docs_admin_compare_ui.jpg)

### API Schemas

![API Schemas](assets/api_docs_schemas.jpg)

### Extended Schemas

![Extended Schemas](assets/api_docs_schemas_extended.jpg)

---

# 🚀 Features

## 📂 Intelligent File Comparison

* Upload BASE and COMPARE document sets
* Detect duplicate documents
* Calculate similarity percentage
* Generate comparison results
* Maintain comparison history

---

## 🤖 AI-Based Document Processing

* OCR extraction from images and scanned PDFs
* Text extraction from multiple formats
* Fuzzy text similarity matching
* Document content analysis
* Automated classification system

---

## 🔐 Authentication & Security

* JWT authentication
* Secure password hashing with bcrypt
* Email OTP verification
* Password reset workflow
* Role-based access control
* Security headers middleware
* Request validation
* Rate limiting

---

## 👨‍💼 Admin Features

* Admin dashboard
* User management
* Account activation/suspension
* User monitoring
* Secure admin-only endpoints

---

# 🏗️ System Architecture

```text
Same_file_detector/

│
├── backend/
│   └── app/
│       ├── api/
│       │   └── Authentication, Admin, Compare APIs
│       │
│       ├── core/
│       │   └── Security, Config, JWT, OTP
│       │
│       ├── models/
│       │   └── Database Models
│       │
│       ├── services/
│       │   ├── OCR Processing
│       │   ├── File Extraction
│       │   └── Similarity Engine
│       │
│       ├── repositories/
│       │   └── Database Operations
│       │
│       └── main.py
│
├── frontend/
│   ├── templates/
│   ├── static/css/
│   └── static/js/
│
├── assets/
│   └── Application Screenshots
│
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

# 🛠️ Technology Stack

## Backend

* Python
* FastAPI
* SQLAlchemy
* Pydantic
* JWT Authentication
* bcrypt

## Document Processing

* PyMuPDF
* Tesseract OCR
* Pillow
* RapidFuzz

## Frontend

* Jinja2 Templates
* JavaScript
* HTML5
* CSS3

## Deployment

* Docker
* Docker Compose
* PostgreSQL / SQLite

---

# ⚙️ Installation Guide

## Clone Repository

```bash
git clone https://github.com/HuzaifaAIDev/Same_file_detector.git

cd Same_file_detector
```

---

# Backend Setup

Go to backend:

```bash
cd backend
```

Create virtual environment:

```bash
python -m venv venv
```

Activate environment:

### Windows

```bash
venv\Scripts\activate
```

Install requirements:

```bash
pip install -r requirements-dev.txt
```

Create environment file:

```bash
copy .env.example .env
```

Run application:

```bash
python main.py
```

Application:

```
http://localhost:20285
```

---

# 🧪 Running Tests

```bash
pytest -q
```

---

# 🐳 Docker Deployment

Build and run:

```bash
docker compose up --build
```

The application will start with:

* FastAPI backend
* Database service
* Production configuration

---

# 📖 API Documentation

Swagger UI:

```
http://localhost:20285/api/docs
```

Redoc:

```
http://localhost:20285/api/redoc
```

---

# 🔌 API Endpoints

| Method | Endpoint                       | Description           |
| ------ | ------------------------------ | --------------------- |
| POST   | `/api/v1/auth/register`        | Register user         |
| POST   | `/api/v1/auth/login`           | User login            |
| POST   | `/api/v1/auth/change-password` | Change password       |
| POST   | `/api/v1/auth/reset-password`  | Reset password        |
| POST   | `/api/v1/compare`              | Compare files         |
| GET    | `/api/v1/compare/history`      | Comparison history    |
| GET    | `/api/v1/health`               | Health check          |
| GET    | `/api/v1/admin/users`          | Admin user management |

---

# 🔒 Security Implementation

The system includes:

* Security headers middleware
* JWT token authentication
* Password hashing
* OTP verification
* Input validation
* Upload size restrictions
* Safe file handling
* Rate limiting protection

---

# 📁 Supported File Formats

| Format | Supported |
| ------ | --------- |
| PDF    | ✅         |
| DOCX   | ✅         |
| XLSX   | ✅         |
| PPTX   | ✅         |
| TXT    | ✅         |
| CSV    | ✅         |
| JSON   | ✅         |
| Images | ✅ OCR     |

---

# 🔮 Future Improvements

* AI semantic embeddings
* Large-scale document processing
* Cloud deployment
* Advanced analytics dashboard
* More document formats
* ML-based similarity prediction

---

# 👨‍💻 Author

**HuzaifaAIDev**

GitHub:

https://github.com/HuzaifaAIDev

---

# 📄 License

This project is licensed under the MIT License.
