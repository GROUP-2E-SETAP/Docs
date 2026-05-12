Utils
=====

Overview
--------

The utils folder contains reusable helper functions and utility classes used throughout the backend application. These utilities centralise common functionality so that code does not need to be repeated across controllers, services, and middleware.

These offer common functionality that is shared by controllers, services, and middleware and are not connected to any particular feature.

The utility files are stored in:

.. code-block:: text

   src/utils

Utility Files
-------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - File
     - Purpose
   * - ``apiError.js``
     - Provides a custom API error class for consistent backend error handling.
   * - ``constants.js``
     - Stores application-wide constants such as transaction types, notification types, and gamification values.
   * - ``dateHelpers.js``
     - Contains reusable helper functions for working with dates and time values.
   * - ``encryption.js``
     - Handles encryption and security-related helper functions.
   * - ``responseHandler.js``
     - Provides a standardised way to format API repsonses across the backend application.

apiError.js
------------

The ``apiError.js`` file defines a custom ``ApiError`` class that extends the built-in JavaScript ``Error`` class.

The error handling middleware can detect and appropriately format structural errors that are thrown throughout the backend.

Example:

.. code-block:: javascript

   throw new ApiError(401, 'Not authorized to access this route');

The ``ApiError`` class improves consistency because all backend errors follow the same structure and can be handled centrally by the error handling middleware.

constants.js
------------

The ``constants.js`` file stores reusable constants used throughout the backend application. Centralising constants improves maintainability because values only need to be updated in one location.

The file includes constants for:

- Transaction types
- Payment methods
- Recurring frequencies
- Budget periods
- Notification types
- Notification priorities
- User roles
- Gamification values
- Pagination settings

Example constants include:

.. code-block:: javascript

   TRANSACTION_TYPES: {
     INCOME: 'income',
     EXPENSE: 'expense'
   }

   USER_ROLES: {
     USER: 'user',
     ADMIN: 'admin'
   }

Using constants reduces hardcoded values throughout the backend and improves consistency.

dateHelpers.js
--------------

The ``dateHelpers.js`` file contains reusable helper functions for working with dates and timestamps.

The file includes functions for:

- Getting the start and end of a month
- Getting the start and end of a week
- Adding or subtracting months
- Adding days to a date
- Formatting dates
- Comparing dates

Example:

.. code-block:: javascript

   exports.formatDate = (date) => {
     return date.toISOString().split('T')[0];
   };

These helper functions simplify date calculations and reduce repeated date-processing code across the backend.

encryption.js
-------------

The ``encryption.js`` file contains helper functions related to encryption and security.

The utility uses Node.js ``crypto`` to:

- Encrypt data
- Decrypt data
- Hash data using SHA-256
- Generate secure random tokens

The file uses the ``aes-256-cbc`` encryption algorithm for symmetric encryption.

Example functionality includes:

.. code-block:: javascript

   exports.hash = (data) => {
     return crypto.createHash('sha256').update(data).digest('hex');
   };

This utility helps protect sensitive information and supports secure backend operations.

responseHandler.js
------------------

The ``responseHandler.js`` file provides a standardised way of returning API responses throughout the backend application.

The ``ResponseHandler`` class includes reusable methods for:

- Successful responses
- Resource creation responses
- Error responses
- Validation errors
- Authentication errors
- Pagination responses

This ensures that API responses follow a consistent JSON structure.

Example successful response:

.. code-block:: json

   {
     "success": true,
     "message": "Success",
     "data": {},
     "timestamp": "2026-05-12T16:00:00.000Z"
   }

Example error response:

.. code-block:: json

   {
     "success": false,
     "message": "An error occurred",
     "errors": [],
     "timestamp": "2026-05-12T16:00:00.000Z"
   }

The response handler improves consistency between endpoints and simplifies response formatting across controllers.

Benefits of Utility Files
-------------------------

Using utility files provides several benefits:

- Reduces repeated code
- Improves backend consistency
- Makes helper functions reusable
- Keeps controllers and services cleaner
- Simplifies maintenance and debugging

Summary
-------

The utils folder provides reusable backend helper functions and classes that support error handling, encryption, date management, configuration, and standardised API responses. Centralising these functions improves maintainability, consistency, and backend organisation.