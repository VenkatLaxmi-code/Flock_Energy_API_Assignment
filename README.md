# Flock Energy API Wrapper

A clean REST API built with **FastAPI** that provides programmatic access to the legacy **Urja Meter Ops** portal.

This project was developed as part of the **Flock Energy Engineering Take-Home Assignment**.

---

# Overview

The Urja Meter Ops portal is designed for human users and does not expose a public API. This project reverse-engineers the portal's network requests and authentication flow to expose a clean REST API that can be consumed by other applications.

The wrapper authenticates with the portal, manages sessions, retrieves meter information, and returns structured JSON responses.

---

# Features

- Authentication with the Urja Meter Ops portal
- Automatic session management
- List available meters
- Fetch meter details
- Fetch meter consumption history
- Interactive Swagger documentation
- OpenAPI specification

---

# Tech Stack

- Python 3.11
- FastAPI
- HTTPX
- Pydantic
- Uvicorn

---

# Project Structure

```
flock-energy-api
│
├── app
│   ├── client.py
│   ├── config.py
│   ├── main.py
│   ├── models.py
│   └── __init__.py
│
├── requirements.txt
├── README.md
├── PROTOCOL.md
├── REFLECTION.md
└── .gitignore
```

---

# Installation

Clone the repository

```bash
git clone <repository-url>
```

Move into the project

```bash
cd flock-energy-api
```

Create a virtual environment

```bash
python -m venv venv
```

Activate it

Windows

```bash
venv\Scripts\activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

# Configuration

Create a `.env` file.

```env
URJA_BASE_URL=https://urja-ops.flockenergy.tech
URJA_EMAIL=operator@urja.local
URJA_PASSWORD=urja-ops-2026
```

---

# Running

```bash
python -m uvicorn app.main:app --reload
```

Server

```
http://127.0.0.1:8000
```

Swagger UI

```
http://127.0.0.1:8000/docs
```

OpenAPI JSON

```
http://127.0.0.1:8000/openapi.json
```

---

# API Endpoints

## Login

```
POST /api/v1/auth/login
```

Authenticates with the Urja Meter Ops portal.

---

## Get All Meters

```
GET /api/v1/meters
```

Returns all available meters.

---

## Get Meter Details

```
GET /api/v1/meters/{meter_id}
```

Returns detailed information for a meter.

---

## Get Consumption

```
GET /api/v1/meters/{meter_id}/consumption
```

Returns consumption history for a meter.

---

# Example Request

```http
GET /api/v1/meters/J100000
```

Example Response

```json
{
  "meter_id": "J100000",
  "name": "...",
  "location": "...",
  "latitude": "...",
  "longitude": "..."
}
```

---

# Design Decisions

- FastAPI was selected for its automatic OpenAPI generation and clean API development experience.
- HTTPX AsyncClient was used to communicate with the legacy portal asynchronously.
- Authentication is encapsulated within a reusable client class.
- Responses are converted into structured Pydantic models before being returned.

---

# Assumptions

- Portal credentials remain valid.
- The portal's internal routes remain unchanged.
- A valid session cookie is returned after successful login.
- The portal is treated as read-only.

---

# Trade-offs

- No persistent storage was used because all data originates from the portal.
- Authentication is performed through the portal rather than maintaining local user accounts.
- The wrapper focuses on exposing the most useful meter operations instead of mirroring every portal feature.

---

# Future Improvements

- Automatic session renewal
- Retry logic with exponential backoff
- Response caching
- Unit tests
- Integration tests
- Structured logging
- Docker support
- Rate limiting
- Bulk export endpoints

---

# Additional Documentation

- PROTOCOL.md
- REFLECTION.md

---

# OpenAPI

The generated OpenAPI specification is available as:

```
openapi.json
```

or via

```
/openapi.json
```
