Middleware
==========

Overview
--------

In the SETAP Finance backend, middleware refers to functions that run between receiving a request and sending a response. Each request travels via the appropriate middleware before arriving to the controller.

Middleware improves security, validation, error handling, and request processing throughout the backend application.


The middleware files are stored in:

.. code-block:: text

   src/middleware

How Middleware Works
--------------------

Middleware sits between the route and the controller.Middleware functions in Express.js have access to the request and response objects as well as the next() function, which transfers control to the subsequent middleware or controller in the request chain.

.. code-block:: text

   Incoming Request
        |
        v
   Middleware 1  (e.g. rate limiter)
        |
        v
   Middleware 2  (e.g. auth check)
        |
        v
   Middleware 3  (e.g. input validation)
        |
        v
   Controller function
        |
        v
   Response sent to client (JSON response)

If a middleware detects a problem (e.g. invalid token, too many requests), it stops the chain and sends an error response immediately without reaching the controller.

Middleware Files
---------------

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - File
     - Purpose
   * - ``auth.js``
     - Verifies the user's JWT access token on protected routes.
   * - ``advancedauth.js``
     - Handles advanced authentication checks such as role-based access control.
   * - ``errorHandler.js``
     - Catches and formats any error that the application encounters.
   * - ``rateLimiter.js``
     - Limits the number of requests a client can make in a given time window to potect against abuse and brute-force attacks.
   * - ``validateRequest.js``
     - Validates incoming request data before it reaches controllers.
   * - ``validation.js``
     - Runs input validation rules and returns errors if the request data is invalid.

auth.js
-------

**File:** ``src/middleware/auth.js``

This middleware protects private routes by verifying the JWT access token attached to the request. The request is denied before it gets to the controller if the token is invalid or absent.

It works as follows:

- Reads the ``Authorization`` header from the request.
- Extracts the Bearer token.
- Verifies the token using the ``JWT_SECRET`` environment variable.
- If valid, attaches the decoded user data to ``req.user`` and calls ``next()``.
- If invalid or missing, returns a ``401 Unauthorized`` response.

.. code-block:: javascript

   // Example of how auth middleware is applied to a route
   import { protect } from '../middleware/auth.js';

   router.get('/profile', protect, getUserProfile);

advancedauth.js
---------------

**File:** ``src/middleware/advancedauth.js``

This middleware extends the base authentication to support more advanced access control. It checks whether the authenticated user has the required permissions to access a specific resource.

This is used for routes that should only be accessible by certain user roles or the resource owner.

errorHandler.js
---------------

**File:** ``src/middleware/errorHandler.js``

This middleware is registered at the end of the Express middleware chain and catches any errors thrown by controllers or other middleware. It ensures all errors are returned in a consistent JSON format.

A typical error response looks like:

.. code-block:: json

   {
     "success": false,
     "message": "Something went wrong",
     "status": 500
   }

This prevents unhandled errors from crashing the server and ensures the client always receives a structured response.

rateLimiter.js
--------------

**File:** ``src/middleware/rateLimiter.js``

This middleware limits the number of requests a single client can make within a set time window. It is applied to sensitive routes such as login and signup to prevent brute-force attacks.

If a client exceeds the limit, they receive a ``429 Too Many Requests`` response.

.. code-block:: text

   Example: max 10 requests per 15 minutes per IP address on auth routes.

validateRequest.js
------------------

**File:** ``src/middleware/validateRequest.js``

This middleware checks that all required fields are present in the request body before passing it to the controller. If any required fields are missing, it returns a ``400 Bad Request`` response with details of what is missing.

This prevents controllers from receiving incomplete data and reduces the need for repetitive checks inside controller functions.

validation.js
-------------

**File:** ``src/middleware/validation.js``

This middleware runs validation rules against the request data using a validation library. It checks field types, formats, lengths, and other constraints.

For example:

- Email fields must be valid email addresses.
- Passwords must meet minimum length requirements.
- Amount fields must be positive numbers.

If validation fails, a ``422 Unprocessable Entity`` response is returned with a list of validation errors.

.. code-block:: json

   {
     "success": false,
     "errors": [
       { "field": "email", "message": "Must be a valid email address" },
       { "field": "password", "message": "Must be at least 8 characters" }
     ]
   }

Summary
-------

The SETAP Finance backend architecture relies heavily on middleware. It manages rate limits, error management, authentication, and validation in a consistent and reusable manner. The backend is kept tidy, safe, and manageable by keeping these issues apart from the controllers.