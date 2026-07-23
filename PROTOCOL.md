# Urja Meter Ops Protocol

## Overview

The Urja Meter Ops portal is a web application used internally by electricity distribution utility operators to manage and inspect smart meter information.

The portal does not expose a public REST API. Instead, data is retrieved through authenticated requests made by the browser after a user logs in.

This project reverse-engineers that behaviour and exposes a clean REST API on top of the portal.

---

# Authentication

The portal requires users to authenticate before accessing any meter information.

Login credentials are submitted to:

```
POST /login
```

using form-encoded data.

Required fields:

```
email
password
```

During investigation, it was observed that successful authentication also required browser-like request headers including:

- Accept: application/json
- Origin
- Referer
- x-sveltekit-action: true

Without these headers, the server rejected requests with a 403 response.

---

# Session Management

After successful authentication, the server returns a secure session cookie.

```
__Secure-better-auth.session_token
```

This cookie is automatically stored by the HTTP client and attached to all subsequent requests.

The wrapper maintains a single authenticated session using an HTTPX AsyncClient instance.

---

# Available Data

The authenticated portal provides access to:

- Meter list
- Individual meter details
- Meter location
- Network information
- Recent consumption history

---

# Reverse Engineering Process

The portal was investigated using browser developer tools.

The following information was identified:

- Authentication endpoint
- Required request headers
- Session cookie behaviour
- JSON responses
- Resource URLs for meter information

Network requests made by the browser were reproduced using HTTPX to provide identical behaviour.

---

# API Wrapper Design

The wrapper performs the following sequence:

1. Authenticate with the portal.
2. Store the returned session cookie.
3. Reuse the authenticated session.
4. Request data from the portal.
5. Convert responses into structured JSON using Pydantic models.
6. Return clean REST responses through FastAPI.

---

# Observed Behaviour

Authentication succeeds by returning a JSON redirect response similar to:

```json
{
  "type": "redirect",
  "status": 303,
  "location": "/meters"
}
```

The presence of a valid session cookie indicates successful login.

---

# Limitations

- The wrapper depends on the current portal implementation.
- Changes to authentication or endpoint structure may require updates.
- The portal is treated as read-only.

---

# Possible Improvements

- Automatic session refresh
- Retry logic
- Response caching
- Background synchronization
- Improved error recovery
- Monitoring and logging
