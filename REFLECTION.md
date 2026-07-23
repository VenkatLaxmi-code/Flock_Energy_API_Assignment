# Reflection

## What assumptions did you make?

I assumed that the Urja Meter Ops portal would continue exposing the same internal endpoints and that a valid authenticated session would provide access to the required meter information. I also assumed that the portal was intended to be used in a read-only manner, as specified in the assignment, and therefore did not attempt to modify any data.

---

## Which part was the most difficult, and how did you get unstuck?

The authentication flow was the most challenging part of the assignment. Initially, simply sending the login credentials resulted in authentication failures. By inspecting the browser's developer tools and comparing network requests, I discovered that the portal expected additional browser-specific headers, including `Origin`, `Referer`, and `x-sveltekit-action`. After reproducing those requests with HTTPX and handling the session cookie correctly, authentication succeeded and the remaining endpoints became accessible.

---

## If you had another day, what would you improve?

Given more time, I would add automated unit and integration tests, implement automatic session renewal, improve retry and timeout handling, add structured logging, introduce response caching, and package the application with Docker for easier deployment. I would also improve the API documentation with more examples and validation.

---

## What mistake did you make while solving this?

Initially, I assumed that submitting only the login credentials would be sufficient for authentication. This led me to spend time investigating failed login requests before realizing that the portal relied on additional browser-generated headers and session behaviour. This experience reinforced the importance of carefully inspecting actual network traffic instead of making assumptions.

---

## If you were reviewing your own submission, what would you criticise?

Although the API wrapper is functional and well-structured, it could benefit from a more comprehensive testing strategy and improved resilience to future changes in the portal. Since the implementation depends on the portal's internal behaviour, changes to its authentication flow or endpoints may require updates. I would also like to improve error reporting and monitoring to make the service more production-ready.
