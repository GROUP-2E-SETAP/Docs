Validators
==========

Overview
--------

Before the controller processes incoming request data, validators in the SETAP Finance backend are in charge of ensuring that the data is accurate. They design and enforce rules on fields like emails, passwords, and device information using the **Joi** validation framework.

The request is instantly rejected with a ``400 Bad Request`` response and a list of particular issues if validation is unsuccessful. This guarantees that only legitimate data is processed and keeps controllers clean.

The validator files are stored in:

.. code-block:: text

   src/validators

Validation Library
------------------

The backend uses **Joi** for validation. Joi allows defining schemas that describe the expected shape and constraints of request data.

.. code-block:: javascript

   import Joi from 'joi';

   const schema = Joi.object({
     email: Joi.string().email().required(),
     password: Joi.string().min(8).required()
   });

   const { error } = schema.validate(req.body, { abortEarly: false });

Setting ``abortEarly: false`` means all validation errors are collected and returned at once, rather than stopping at the first error.

Validator Files
---------------

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - File
     - Purpose
   * - ``authvalidators.js``
     - Validates all authentication-related request data including registration, login, and password management.

authvalidators.js
-----------------

**File:** ``src/validators/authvalidators.js``

This file contains all validation functions related to authentication. Each function is used as middleware on the relevant route and checks the request body before it reaches the controller.

Password Requirements
~~~~~~~~~~~~~~~~~~~~~

A reusable password schema is defined using Joi. Passwords must:

- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character (``@$!%*?&#``)

.. code-block:: javascript

   const passwordSchema = Joi.string()
     .min(8)
     .pattern(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#])[A-Za-z\d@$!%*?&#]/)
     .required();

Validation Functions
~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Function
     - Description
   * - ``validateRegister``
     - Validates registration requests. Requires a valid email, a password meeting all requirements, and an optional name (2-100 characters).
   * - ``validateLogin``
     - Validates login requests. Requires a valid email and a password.
   * - ``validatePasswordReset``
     - Validates password reset requests. Requires a new password and a matching confirmation password.
   * - ``validateChangePassword``
     - Validates change password requests. Requires the current password, a new password, and a matching confirmation.
   * - ``validateForgotPassword``
     - Validates forgot password requests. Requires a valid email address.
   * - ``validateMobileLogin``
     - Validates mobile login requests. Requires email, password, and device information including device ID, name, and type (ios/android/web).
   * - ``validateDeviceInfo``
     - Validates device information attached to a request. Requires device ID, name, and type.

Error Response Format
~~~~~~~~~~~~~~~~~~~~~

When validation fails, the middleware returns a structured JSON response.

Exmaple:

.. code-block:: json

   {
     "success": false,
     "message": "Validation failed",
     "errors": [
       { "field": "email", "message": "Please provide a valid email address" },
       { "field": "password", "message": "Password must be at least 8 characters long" }
     ]
   }

Each error object contains the field name and a human-readable message describing what is wrong.

Summary
-------

Validators ensure that all incoming request data meets the required format and constraints before reaching the controller. By centralising validation logic in dedicated files and using Joi schemas, the backend enforces consistent rules across all endpoints and returns clear, structured error messages to the client.