Utilities 
======================

Shared helper modules used across the application. None of these are
route-facing — they are imported directly by controllers, services, and middleware.

-----------------

ResponseHandler (``utils/responseHandler.js``)
-----------------------------------------------

A static class that standardises all API responses across the application.
Every controller uses this instead of calling ``res.status().json()`` directly,
ensuring consistent response shape with ``success``, ``message``, ``data``,
and ``timestamp`` on every response.

.. list-table::
   :header-rows: 1
   :widths: 30 10 60

   * - Method
     - Status
     - Description
   * - ``success(res, data, message)``
     - 200
     - Standard success response
   * - ``created(res, data, message)``
     - 201
     - Resource created successfully
   * - ``error(res, message, statusCode, errors)``
     - 500
     - Base error response — all others delegate to this
   * - ``badRequest(res, message, errors)``
     - 400
     - Missing or invalid fields
   * - ``unauthorized(res, message)``
     - 401
     - Missing or invalid auth token
   * - ``forbidden(res, message)``
     - 403
     - Valid token but insufficient permissions
   * - ``notFound(res, message)``
     - 404
     - Resource does not exist
   * - ``conflict(res, message)``
     - 409
     - Duplicate resource
   * - ``validationError(res, errors)``
     - 400
     - Joi or schema validation failure
   * - ``serverError(res, message)``
     - 500
     - Unhandled server error
   * - ``paginated(res, data, page, limit, total)``
     - 200
     - Paginated response including ``pagination`` metadata

----------------

ApiError (``utils/apiError.js``)
---------------------------------

A custom error class extending the native ``Error``. Sets ``statusCode`` and
flags the error as ``isOperational = true`` so the global error middleware
can distinguish expected errors from unexpected crashes.

.. code-block:: javascript

   export class ApiError extends Error {
     constructor(statusCode, message) {
       super(message);
       this.statusCode = statusCode;
       this.isOperational = true;
       Error.captureStackTrace(this, this.constructor);
     }
   }

----------------

Constants (``utils/constants.js``)
------------------------------------

Centralised constants for transaction types, payment methods, budget periods,
notification types, user roles, gamification points, and pagination defaults.
Defined with ``module.exports`` — note this uses CommonJS rather than ES module
syntax unlike the rest of the codebase.

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Constant
     - Values
   * - ``TRANSACTION_TYPES``
     - ``income``, ``expense``
   * - ``PAYMENT_METHODS``
     - ``cash``, ``card``, ``bank_transfer``, ``mobile_payment``, ``other``
   * - ``BUDGET_PERIODS`` / ``RECURRING_FREQUENCIES``
     - ``daily``, ``weekly``, ``monthly``, ``yearly``
   * - ``NOTIFICATION_TYPES``
     - ``budget_alert``, ``achievement``, ``reminder``, ``tip``, ``system``, ``transaction``
   * - ``NOTIFICATION_PRIORITIES``
     - ``low``, ``medium``, ``high``
   * - ``USER_ROLES``
     - ``user``, ``admin``
   * - Gamification
     - 5 points per transaction, 10 per budget, 50 per goal achieved, 100 per level
   * - Pagination
     - Default page ``1``, default limit ``20``, max limit ``100``

------------------

Date Helpers (``utils/dateHelpers.js``)
-----------------------------------------

Helper functions for common date operations. Uses CommonJS exports.

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Function
     - Description
   * - ``startOfMonth(date)``
     - Returns the first day of the month at midnight
   * - ``endOfMonth(date)``
     - Returns the last day of the month at 23:59:59.999
   * - ``startOfWeek(date)``
     - Returns the Monday of the week containing the given date
   * - ``endOfWeek(date)``
     - Returns the Sunday of the week at 23:59:59.999
   * - ``subMonths(date, months)``
     - Subtracts ``n`` months from a date
   * - ``addMonths(date, months)``
     - Adds ``n`` months to a date
   * - ``addDays(date, days)``
     - Adds ``n`` days to a date
   * - ``formatDate(date)``
     - Returns date as ``YYYY-MM-DD`` string
   * - ``isSameDay(date1, date2)``
     - Returns ``true`` if two dates fall on the same calendar day

---------------------------

Encryption (``utils/encryption.js``)
--------------------------------------

AES-256-CBC encryption and decryption helpers using Node's built-in ``crypto``
module. Also provides SHA-256 hashing and secure token generation.
Uses CommonJS exports.

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Function
     - Description
   * - ``encrypt(text)``
     - Encrypts a string and returns ``iv:encryptedHex``
   * - ``decrypt(text)``
     - Decrypts an ``iv:encryptedHex`` string back to plain text
   * - ``hash(data)``
     - Returns a SHA-256 hex digest of the input
   * - ``generateToken(length)``
     - Returns a cryptographically random hex string, defaults to 32 bytes
