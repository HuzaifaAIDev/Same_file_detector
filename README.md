![Same File Detector Banner](assets/banner.png)

# 🔍 Same File Detector

![Python](https://img.shields.io/badge/Python-3.x-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![OCR](https://img.shields.io/badge/OCR-Tesseract-orange)
![Docker](https://img.shields.io/badge/Docker-Supported-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)
![GitHub Stars](https://img.shields.io/github/stars/HuzaifaAIDev/Same_file_detector?style=social)

## AI-Powered Document Similarity & Duplicate File Detection System

**Same File Detector** is a document intelligence platform that detects duplicate and similar files using OCR, text extraction, and fuzzy similarity analysis.

The system allows users to upload:

* **BASE documents** (reference files)
* **COMPARE documents** (files to analyze)

and automatically classifies them as:

* ✅ **EXACT** — Documents are identical
* ⚠️ **SIMILAR** — Documents contain highly matching content
* ❌ **DIFFERENT** — Documents have low similarity

Built with **FastAPI, OCR processing, secure authentication, and a modern comparison engine**.

---

# ⭐ Support This Project

If you find this project useful, consider giving it a ⭐ star on GitHub.

Your star helps support the project and motivates future improvements.

👉 Star the repository:

https://github.com/HuzaifaAIDev/Same_file_detector

---

# 📸 Application Preview

## 🔐 Authentication

### Sign In

![Sign In](assets/sign_in.jpg)

### Create Account

![Create Account](assets/create_account.jpg)

### Email OTP Verification

![Verify Email](assets/verify_email.jpg)

### Password Reset

![Reset Password](assets/reset_password.jpg)

---

# 👤 User Dashboard

### User Dashboard

![User Dashboard](assets/user_dashboard_empty.jpg)

### Select Documents

![Files Selected](assets/user_files_selected.jpg)

### Similarity Results

![Comparison Results](assets/comparison_results.jpg)

---

# 👨‍💼 Admin Dashboard

### Admin Control Panel

![Admin Dashboard](assets/admin_dashboard.jpg)

### User Management (Light Theme)

![User Management Light](assets/admin_user_management_light.jpg)

### User Management (Dark Theme)

![User Management Dark](assets/admin_user_management_dark.jpg)

---

# 📚 API Documentation

FastAPI provides interactive API documentation through Swagger UI.

### Swagger Overview

![Swagger Overview](assets/api_docs_overview.jpg)

### Authentication & Admin APIs

![Swagger Auth](assets/api_docs_auth_admin_compare.jpg)

### Compare APIs

![Compare APIs](assets/api_docs_admin_compare_ui.jpg)

### API Schemas

![Schemas](assets/api_docs_schemas.jpg)

![Extended Schemas](assets/api_docs_schemas_extended.jpg)

---

# 🚀 Key Features

## 📂 Intelligent File Comparison

* Upload multiple BASE and COMPARE files
* Detect duplicate documents
* Calculate similarity percentage
* Generate comparison reports
* Maintain comparison history

---

## 🤖 Document Intelligence

* OCR extraction from images and scanned PDFs
* Text extraction from multiple formats
* Fuzzy text similarity matching
* Document content analysis
* Automatic classification

---

## 🔐 Authentication & Security

* JWT authentication
* bcrypt password hashing
* Email OTP verification
* Password reset workflow
* Role-based access control
* Security headers middleware
* Input validation
* Rate limiting protection

---

## 👨‍💼 Admin Features

* Admin dashboard
* User management
* Account activation/suspension
* User monitoring
* Protected admin APIs

---

# 🏗️ Architecture

```text
Same_file_detector/

├── backend/
│   └── app/
│       ├── api/              # Authentication, Admin, Compare APIs
│       ├── core/             # Config, JWT, Security, OTP
│       ├── models/           # Database models
│       ├── services/         # OCR, extraction, similarity engine
│       ├── repositories/     # Database operations
│       └── main.py
│
├── frontend/
│   ├── templates/            # Jinja2 templates
│   ├── static/css/           # Styling
│   └── static/js/            # Frontend logic
│
├── assets/                   # Screenshots and media
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

* Jinja2
* JavaScript
* HTML5
* CSS3

## Database & Deployment

* SQLite
* PostgreSQL
* Docker
* Docker Compose

---

# ⚙️ Installation

## Clone Repository

```bash
git clone https://github.com/HuzaifaAIDev/Same_file_detector.git

cd Same_file_detector
```

---

## Backend Setup

```bash
cd backend

python -m venv venv
```

Activate:

### Windows

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create environment:

```bash
copy .env.example .env
```

Run:

```bash
python main.py
```

Application:

```
http://localhost:20285
```

---

# 🧪 Testing

Run:

```bash
pytest -q
```

---

# 🐳 Docker Deployment

Run:

```bash
docker compose up --build
```

Docker starts:

* FastAPI backend
* Database service
* Production configuration

---

# 📖 API Documentation

Swagger:

```
http://localhost:20285/api/docs
```

Redoc:

```
http://localhost:20285/api/redoc
```

---

# 🔌 API Endpoints

| Method | Endpoint                       | Description       |
| ------ | ------------------------------ | ----------------- |
| POST   | `/api/v1/auth/register`        | Register user     |
| POST   | `/api/v1/auth/login`           | Login             |
| POST   | `/api/v1/auth/change-password` | Change password   |
| POST   | `/api/v1/auth/reset-password`  | Reset password    |
| POST   | `/api/v1/compare`              | Compare documents |
| GET    | `/api/v1/compare/history`      | View history      |
| GET    | `/api/v1/admin/users`          | Manage users      |
| GET    | `/api/v1/health`               | Health check      |

---

# 🔒 Security

Implemented security features:

* JWT authentication
* Password encryption
* OTP verification
* Secure headers
* File validation
* Upload restrictions
* Rate limiting
* Safe file handling

---

# 📁 Supported Formats

| Format | Support |
| ------ | ------- |
| PDF    | ✅       |
| DOCX   | ✅       |
| XLSX   | ✅       |
| PPTX   | ✅       |
| TXT    | ✅       |
| CSV    | ✅       |
| JSON   | ✅       |
| Images | ✅ OCR   |

---

# 🔮 Future Roadmap

Planned improvements:

* Semantic similarity using embeddings
* Large-scale document processing
* Advanced analytics dashboard
* Cloud deployment
* More document formats
* Improved AI-based ranking

---

# 👨‍💻 Author

## HuzaifaAIDev

GitHub:
https://github.com/HuzaifaAIDev

---

# ⭐ Contribute & Support

Found this project interesting?

You can help by:

* ⭐ Starring the repository
* Reporting issues
* Suggesting improvements
* Contributing new features

Every contribution helps improve the project.

---

# 📄 License

Licensed under the MIT License.
