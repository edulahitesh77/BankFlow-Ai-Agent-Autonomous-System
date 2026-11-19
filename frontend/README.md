# BankFlow AI – Frontend Portal

Modern, responsive web frontend for **BankFlow AI – Intelligent Multi-Agent Banking Service Automation System**.

Built with **React 18**, **Vite**, **Tailwind CSS**, and **React Router v6**.

---

## Dual Authentication Experience

The frontend provides two visually and functionally distinct portals:

### 1. Customer Banking Portal (Blue & White Modern Interface)
- **Customer Sign In**: `/customer/login`
- **Customer Registration**: `/customer/register`
- **Customer Dashboard**: `/customer/dashboard` (Protected: `CUSTOMER` role)
- **Design Aesthetic**: Clean retail banking UI with blue accents (`#2563EB`), white cards, Argon2id security badges, remember-me support, and synthetic account overviews.

### 2. Bank Staff Portal (Dark Navy & Emerald Green Interface)
- **Employee Sign In**: `/bank/login`
- **Bank Dashboard**: `/bank/dashboard` (Protected: `BANK_EMPLOYEE` role)
- **Design Aesthetic**: High-fidelity dark operations console (`#070D1E`) with emerald green accents (`#10B981`), employee ID authentication, multi-agent queue overview, and restricted internal access warnings.
- **Controlled Provisioning**: Public registration is disabled; employee credentials must be created via administrative provisioning or the development seed command.

---

## Setup & Execution

### Prerequisites
- Node.js (v18+)
- npm (v9+)

### Installation
```bash
npm install
```

### Start Development Server
```bash
npm run dev
```
The Vite development server will start on [http://localhost:5173](http://localhost:5173). Requests to `/api/*` are automatically proxied to the backend at `http://127.0.0.1:8000`.

### Production Build
```bash
npm run build
```
Generates production-ready static assets in `frontend/dist/`.

---

## Role-Based Route Protection
The `ProtectedRoute` component inspects the authenticated user's verified role returned by the FastAPI backend:
- Unauthenticated visitors are redirected to their respective login portal.
- Authenticated customers attempting to access `/bank/dashboard` receive an explicit `HTTP 403 Access Restricted` screen.
- Authenticated bank employees attempting to access `/customer/dashboard` receive an explicit `HTTP 403 Access Restricted` screen.
