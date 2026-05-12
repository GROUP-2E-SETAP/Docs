Routes and Controllers
======================

Overview
--------

This module defines the controllers and routes for the SETAP Finance backend. The backend is constructed with **Express.js** and employs a RESTful API approach. Every route has a version under ``/api/v1/``.

The API endpoints for a feature area are specified in each route file. The business logic that processes the request and returns a response is contained in each controller file. This maintains the backend's organisation and makes it easier to expand and maintain.

The main route files are stored in:

.. code-block:: text

   src/routes/v1

The main controller files are stored in:

.. code-block:: text

   src/controllers



How Routes and Controllers Work Together
-----------------------------------------

Each route file maps HTTP methods and URL paths to a specific controller function. The controller then handles the request — validating input, interacting with the database via a service layer, and returning a JSON response.

The general flow is:

.. code-block:: text

   Frontend request
        |
        v
   Route file  (defines endpoint + applies auth middleware)
        |
        v
   Controller function  (validates input, calls service, builds response)
        |
        v
   Service or database  (PostgreSQL or MongoDB)
        |
        v
   JSON response

Benefits of Separating Routes and Controllers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Route files are kept readable and brief.
- It keeps business logic and endpoint definitions separate.
- It makes the project easier to test
- It makes it easier for several developers to work on various functionalities.
- It makes the backend easier to expand in the future



HTTP Methods
------------

The backend API uses standard HTTP methods.

.. list-table::
   :header-rows: 1
   :widths: 15 85

   * - Method
     - Purpose
   * - GET
     - Retrieves data from the backend.
   * - POST
     - Creates new data.
   * - PUT
     - Updates existing data.
   * - DELETE
     - Deletes existing data.



Code Examples
-------------

Example Route
~~~~~~~~~~~~~

.. code-block:: javascript

   import express from 'express';
   import { getBudgets, createBudget } from '../../controllers/budgetController.js';

   const router = express.Router();

   router.get('/', getBudgets);
   router.post('/', createBudget);

   export default router;

In this example:

- ``router.get('/')`` handles a GET request.
- ``router.post('/')`` handles a POST request.
- ``getBudgets`` and ``createBudget`` are controller functions imported from the controller file.
- The route file does not contain any business logic itself.

Example Controller
~~~~~~~~~~~~~~~~~~

.. code-block:: javascript

   exports.getBudgets = async (req, res, next) => {
     try {
       const budgets = await budgetService.getUserBudgets(req.user.id);
       res.status(200).json({
         success: true,
         data: budgets
       });
     } catch (error) {
       next(error);
     }
   };

This controller function retrieves the user's budgets and returns them as a JSON response. If an error occurs, it is passed to the error handling middleware using ``next(error)``.



Authentication Routes
---------------------

**Route file:** ``src/routes/v1/authRoutes.js``

**Controller file:** ``src/controllers/authController.js``

The authentication system uses **JWT (JSON Web Tokens)** with short-lived access tokens (15 minutes) and longer-lived refresh tokens (7 days). Rate limiting is applied to authentication routes to prevent brute-force attacks. Passwords are hashed using **bcrypt**. These routes control who can access the backend system and are the foundation of the application's security.

.. list-table::
   :header-rows: 1
   :widths: 10 40 50

   * - Method
     - Endpoint
     - Description
   * - POST
     - ``/api/v1/auth/signup``
     - Registers a new user. Validates input, hashes the password, creates a user record, and sends a verification email.
   * - POST
     - ``/api/v1/auth/login``
     - Authenticates a user with email and password. Returns an access token and a refresh token on success.
   * - POST
     - ``/api/v1/auth/logout``
     - Logs out the user by blacklisting their current token so it can no longer be used.
   * - POST
     - ``/api/v1/auth/refresh-token``
     - Issues a new access token using a valid refresh token, without requiring the user to log in again.
   * - POST
     - ``/api/v1/auth/forgot-password``
     - Accepts an email address and sends a password reset link if the account exists.
   * - POST
     - ``/api/v1/auth/reset-password``
     - Accepts a reset token and a new password, updates the user's credentials.
   * - GET
     - ``/api/v1/auth/verify-email``
     - Verifies a user's email address using a token sent during registration.



Users
-----

**Route file:** ``src/routes/v1/userRoutes.js``

**Controller file:** ``src/controllers/userControllers.js``

User routes manage account-related actions including retrieving user details, updating user information, and deleting a user account. All routes in this section require the user to be authenticated, meaning a valid JWT must be provided with the request.

.. list-table::
   :header-rows: 1
   :widths: 10 40 50

   * - Method
     - Endpoint
     - Description
   * - GET
     - ``/api/v1/users/profile``
     - Returns the authenticated user's profile information.
   * - PUT
     - ``/api/v1/users/profile``
     - Updates the authenticated user's profile details.
   * - DELETE
     - ``/api/v1/users``
     - Deletes the authenticated user's account and all associated data.



Transactions
------------

**Route file:** ``src/routes/v1/transactionRoutes.js``

**Controller file:** ``src/controllers/transactionControllers.js``

Transaction routes manage income and expense records stored in **MongoDB**. They allow users to create, view, update, and delete transactions. These routes are central to the finance application because transactions provide the main financial data used across the system. Each transaction is indexed by ``user_id``, ``date``, ``type``, and ``category`` for efficient querying.

.. list-table::
   :header-rows: 1
   :widths: 10 40 50

   * - Method
     - Endpoint
     - Description
   * - GET
     - ``/api/v1/transactions``
     - Returns all transactions belonging to the authenticated user.
   * - POST
     - ``/api/v1/transactions``
     - Creates a new transaction. Accepts amount, type (income/expense), category, and date.
   * - GET
     - ``/api/v1/transactions/:id``
     - Returns a single transaction by its ID.
   * - PUT
     - ``/api/v1/transactions/:id``
     - Updates an existing transaction by its ID.
   * - DELETE
     - ``/api/v1/transactions/:id``
     - Deletes a transaction by its ID.
   * - GET
     - ``/api/v1/transactions/stats``
     - Returns aggregated statistics such as total income and total expenses for the user.



Categories
----------

**Route file:** ``src/routes/v1/categoryRoutes.js``

**Controller file:** ``src/controllers/categoryControllers.js``

Category routes manage the categories used to organise transactions. Categories help users group their income and expenses into meaningful sections such as food, rent, transport, or salary. Category data is stored in **PostgreSQL**.

.. list-table::
   :header-rows: 1
   :widths: 10 40 50

   * - Method
     - Endpoint
     - Description
   * - GET
     - ``/api/v1/categories``
     - Returns all categories for the authenticated user.
   * - POST
     - ``/api/v1/categories``
     - Creates a new category with a name and optional colour or icon.
   * - PUT
     - ``/api/v1/categories/:id``
     - Updates an existing category by its ID.
   * - DELETE
     - ``/api/v1/categories/:id``
     - Deletes a category by its ID.



Budgets
-------

**Route file:** ``src/routes/v1/budgetRoutes.js``

**Controller file:** ``src/controllers/budgetControllers.js``

Budget routes allow users to set spending limits per category and track spending against those limits. The controller checks whether spending has exceeded the budget and can trigger notifications accordingly. Budget data is stored in **PostgreSQL**.

.. list-table::
   :header-rows: 1
   :widths: 10 40 50

   * - Method
     - Endpoint
     - Description
   * - GET
     - ``/api/v1/budgets``
     - Returns all budgets for the authenticated user.
   * - POST
     - ``/api/v1/budgets``
     - Creates a new budget. Accepts a category, limit amount, and time period.
   * - PUT
     - ``/api/v1/budgets/:id``
     - Updates an existing budget by its ID.
   * - DELETE
     - ``/api/v1/budgets/:id``
     - Deletes a budget by its ID.



Goals
-----

**Route file:** ``src/routes/v1/goalsRoutes.js``

**Controller file:** ``src/controllers/goalsControllers.js``

Users can set and monitor goals for savings or other financial objectives using goal routes. The user's transaction history is used by the controller to monitor progress.

.. list-table::
   :header-rows: 1
   :widths: 10 40 50

   * - Method
     - Endpoint
     - Description
   * - GET
     - ``/api/v1/goals``
     - Returns all financial goals for the authenticated user.
   * - POST
     - ``/api/v1/goals``
     - Creates a new goal with a target amount and optional deadline.
   * - PUT
     - ``/api/v1/goals/:id``
     - Updates an existing goal by its ID.
   * - DELETE
     - ``/api/v1/goals/:id``
     - Deletes a goal by its ID.



Notifications
-------------

**Route file:** ``src/routes/v1/notificationRoutes.js``

**Controller file:** ``src/controllers/notificationControllers.js``

Notification routes manage alerts and messages shown to the user. These may include budget warnings, goal updates, or other system notifications. Notification data is stored in **PostgreSQL** and is triggered by backend events such as exceeding a budget or reaching a savings goal.

.. list-table::
   :header-rows: 1
   :widths: 10 40 50

   * - Method
     - Endpoint
     - Description
   * - GET
     - ``/api/v1/notifications``
     - Returns all notifications for the authenticated user.
   * - PUT
     - ``/api/v1/notifications/:id/read``
     - Marks a specific notification as read.
   * - DELETE
     - ``/api/v1/notifications/:id``
     - Deletes a specific notification.



Summary
-------

All backend requests are handled by controllers and routes working together. While controllers handle the request and provide the appropriate response, routes specify the accessible endpoints. As the program expands, this framework facilitates an easy-to-extend backend architecture that is neat, structured, and maintained.