Authentication
==============

Handles all user identity operations — registration, login, logout, token
management, password reset, and email verification. Auth is the most security-critical
feature in the application, and as such it is the only feature with rate limiting,
JWT token rotation, token blacklisting, and Joi validation applied at the route level.

.. note::
   Access tokens are short-lived (``15m`` by default). Refresh tokens last ``7d``
   and are rotated on every use — the old one is revoked and a new one is issued.

.. note::
   All password reset and forgot-password endpoints always return ``200``
   regardless of whether the email exists, to prevent email enumeration attacks.

-----------------------------

Models
------

Auth uses five database tables defined in PostgreSQL.

**users**

.. code-block:: sql

   CREATE TABLE IF NOT EXISTS users (
     id                 SERIAL PRIMARY KEY,
     email              VARCHAR(255) UNIQUE NOT NULL,
     password           VARCHAR(255) NOT NULL,
     name               VARCHAR(100),
     phone              VARCHAR(20),
     avatar             VARCHAR(500),
     currency           VARCHAR(3)   DEFAULT 'USD',
     language           VARCHAR(10)  DEFAULT 'en',
     is_verified        BOOLEAN      DEFAULT FALSE,
     role               VARCHAR(20)  DEFAULT 'user' CHECK (role IN ('user', 'admin')),
     gamification_level INTEGER      DEFAULT 1,
     gamification_points INTEGER     DEFAULT 0,
     created_at         TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
     updated_at         TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
   );


**email_verification_tokens**

.. code-block:: sql

   CREATE TABLE IF NOT EXISTS email_verification_tokens (
     id         SERIAL PRIMARY KEY,
     user_id    INTEGER REFERENCES users(id) ON DELETE CASCADE,
     token      VARCHAR(255) UNIQUE NOT NULL,
     expires_at TIMESTAMP NOT NULL,
     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );

Token is a 32-byte hex string generated with ``crypto.randomBytes(32)``.
Expires 24 hours after creation. Deleted from the table once used.

**password_reset_tokens**

.. code-block:: sql

   CREATE TABLE IF NOT EXISTS password_reset_tokens (
     id         SERIAL PRIMARY KEY,
     user_id    INTEGER REFERENCES users(id) ON DELETE CASCADE,
     token      VARCHAR(255) UNIQUE NOT NULL,
     expires_at TIMESTAMP NOT NULL,
     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );

Token expires after 1 hour. Any existing reset tokens for the user are
deleted before a new one is inserted, so only one active reset token exists
per user at a time.

**refresh_tokens**

.. code-block:: sql

   CREATE TABLE IF NOT EXISTS refresh_tokens (
     id         SERIAL PRIMARY KEY,
     user_id    INTEGER REFERENCES users(id) ON DELETE CASCADE,
     token      TEXT UNIQUE NOT NULL,
     expires_at TIMESTAMP NOT NULL,
     revoked    BOOLEAN   DEFAULT FALSE,
     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );

Refresh tokens are stored in the database and rotated on each use.
On logout, the token is marked ``revoked = true`` rather than deleted,
preserving an audit trail.

**token_blacklist**

.. code-block:: sql

   CREATE TABLE IF NOT EXISTS token_blacklist (
     id         SERIAL PRIMARY KEY,
     token      TEXT UNIQUE NOT NULL,
     expires_at TIMESTAMP NOT NULL,
     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );

Access tokens are added here on logout. The ``expires_at`` mirrors the
token's own expiry so the blacklist can be cleaned up once entries expire.

---------------------------

Routes (``routes/v1/authRoutes.js``)
-------------------------------------

Auth routes apply two middleware layers before the controller, making them more robust than any other route in
the application.

.. code-block:: javascript

   router.post('/signup',          registerLimiter, validateRequest(signupSchema, 'body'),        authController.signup);
   router.post('/login',           loginLimiter,    validateRequest(loginSchema, 'body'),          authController.login);
   router.post('/logout',          authenticate,                                                   authController.logout);
   router.post('/forgot-password', passwordResetLimiter, validateRequest(forgotPasswordSchema, 'body'), authController.forgotPassword);
   router.get('/verify-email/:token',                                                              authController.verifyEmail);
   router.get('/me',               authenticate,                                                   authController.getCurrentUser);
   router.put('/change-password',  authenticate,                                                   authController.changePassword);

Validation Schemas
~~~~~~~~~~~~~~~~~~~

Joi schemas are defined in the routes file and passed to ``validateRequest``
middleware before requests reach the controller.

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Schema
     - Rules
   * - ``signupSchema``
     - ``email`` — valid email, required. ``password`` — min 6 chars, required. ``name`` — max 100 chars, optional
   * - ``loginSchema``
     - ``email`` — valid email, required. ``password`` — min 6 chars, required
   * - ``forgotPasswordSchema``
     - ``email`` — valid email, required

-------------------------------

Validators (``validators/authValidators.js``)
----------------------------------------------

A separate, stricter set of Joi validators also exists. These are defined as
Express middleware functions and enforce stronger password rules than the
route-level schemas.

.. note::
   These validators are **not currently used** in the routes file — the routes
   use the inline Joi schemas defined in ``authRoutes.js`` instead. They are
   available for use if stricter validation is needed in the future.

Requires at least 8 characters, one uppercase letter, one lowercase letter,
one number, and one special character from ``@$!%*?&#``. The route-level
schema only requires a minimum of 6 characters with no pattern enforcement.

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Validator
     - Purpose
   * - ``validateRegister``
     - Email, strong password, optional name (min 2 chars)
   * - ``validateLogin``
     - Email and password presence only — no strength check on login
   * - ``validatePasswordReset``
     - Strong new password + ``confirmPassword`` must match
   * - ``validateChangePassword``
     - ``currentPassword`` presence, strong new password, confirm match
   * - ``validateForgotPassword``
     - Valid email only
   * - ``validateMobileLogin``
     - Email, password, and a required ``deviceInfo`` object (deviceId, deviceName, deviceType)
   * - ``validateDeviceInfo``
     - ``deviceInfo`` object only — allows unknown fields via ``.unknown(true)``

------------------------

Controller (``controllers/authController.js``)
-----------------------------------------------

Delegates all logic to the service layer and uses ``next(error)`` for error
handling rather than ``ResponseHandler``, passing errors to Express's global
error middleware instead.

``signup``
~~~~~~~~~~~
Calls ``authService.register()``, then attempts to send a welcome email.
The email is wrapped in its own try/catch so a failed email does not prevent
the signup from succeeding. Returns ``201`` with ``accessToken``,
``refreshToken``, and user data.

.. code-block:: javascript

   async function signup(req, res, next) {
     try {
       const result = await authService.register(req.body);
       try {
         await sendWelcomeEmail(result.user.email, result.user.name);
       } catch (emailError) {
         console.error('Welcome email failed:', emailError.message);
       }
       return res.status(201).json({
         success: true,
         data: result.user,
         accessToken: result.accessToken,
         refreshToken: result.refreshToken
       });
     } catch (error) {
       next(error);
     }
   }

``login``
~~~~~~~~~~
Calls ``authService.login()`` and returns ``200`` with ``accessToken``,
``refreshToken``, and user data on success.

.. code-block:: javascript

   async function login(req, res, next) {
     try {
       const result = await authService.login(req.body);
       return res.status(200).json({
         success: true,
         data: result.user,
         accessToken: result.accessToken,
         refreshToken: result.refreshToken
       });
     } catch (error) {
       next(error);
     }
   }

``logout``
~~~~~~~~~~~
Extracts the access token from the ``Authorization`` header and the
``refreshToken`` from the request body. Blacklists the access token and
revokes the refresh token independently — either can be missing without
causing a failure.

.. code-block:: javascript

   async function logout(req, res, next) {
     try {
       const token = req.headers.authorization?.replace('Bearer ', '');
       const { refreshToken } = req.body;
       if (token) await authService.blacklistToken(token);
       if (refreshToken) await authService.revokeRefreshToken(refreshToken);
       return res.status(200).json({ success: true, message: 'Logged out successfully' });
     } catch (error) {
       next(error);
     }
   }

``forgotPassword``
~~~~~~~~~~~~~~~~~~~
Calls ``authService.initiatePasswordReset()``. Always returns ``200``
regardless of outcome — even if the service throws, the catch block
returns the same success response to prevent email enumeration.

.. code-block:: javascript

   async function forgotPassword(req, res, next) {
     try {
       const { email } = req.body;
       if (!email) return res.status(400).json({ success: false, message: 'Email is required' });
       await authService.initiatePasswordReset(email);
       return res.status(200).json({ success: true, message: 'Password reset email sent if account exists' });
     } catch (error) {
       return res.status(200).json({ success: true, message: 'Password reset email sent if account exists' });
     }
   }

``verifyEmail``
~~~~~~~~~~~~~~~~
Extracts ``token`` from ``req.params`` and delegates to
``authService.verifyEmail()``. Returns the verified user on success.

``getCurrentUser``
~~~~~~~~~~~~~~~~~~~
Returns ``req.user`` which is attached by the ``authenticate`` middleware.
Contains no logic of its own.

.. code-block:: javascript

   async function getCurrentUser(req, res, next) {
     try {
       return res.status(200).json({ success: true, data: req.user });
     } catch (error) {
       next(error);
     }
   }

``changePassword``
~~~~~~~~~~~~~~~~~~~
Extracts ``currentPassword`` and ``newPassword`` from ``req.body`` and
``userId`` from ``req.user`` (set by ``authenticate`` middleware). Returns
``400`` if either password field is missing.

.. code-block:: javascript

   async function changePassword(req, res, next) {
     try {
       const { currentPassword, newPassword } = req.body;
       const userId = req.user.id;
       if (!currentPassword || !newPassword) {
         return res.status(400).json({ success: false, message: 'Current password and new password are required' });
       }
       await authService.changePassword(userId, currentPassword, newPassword);
       return res.status(200).json({ success: true, message: 'Password changed successfully' });
     } catch (error) {
       next(error);
     }
   }

---------------------------

Service (``services/authService.js``)
---------------------------------------

Contains all business logic for authentication. Uses ``bcryptjs`` for password
hashing, ``jsonwebtoken`` for token signing, and ``crypto`` for generating
secure random tokens.

Token Configuration
~~~~~~~~~~~~~~~~~~~~

.. code-block:: javascript

   const JWT_SECRET         = process.env.JWT_SECRET         || 'change_this_secret';
   const JWT_REFRESH_SECRET = process.env.JWT_REFRESH_SECRET || 'change_this_refresh_secret';
   const JWT_EXPIRES        = process.env.JWT_EXPIRES        || '15m';
   const JWT_REFRESH_EXPIRES = process.env.JWT_REFRESH_EXPIRES || '7d';

.. note::
   Default secrets are hardcoded as fallbacks.

``register(payload)``
~~~~~~~~~~~~~~~~~~~~~~
Validates the payload with Joi, checks for duplicate email via
``User.findByEmail()``, hashes the password with bcrypt (10 salt rounds),
creates the user, signs both tokens, stores the refresh token, and generates
an email verification token valid for 24 hours.

.. code-block:: javascript

   async function register(payload) {
     const { error } = registerSchema.validate(payload, { abortEarly: false, stripUnknown: true });
     if (error) { /* throw 400 */ }

     const existing = await User.findByEmail(email);
     if (existing) { /* throw 409 */ }

     const hashed = await bcrypt.hash(password, 10);
     const user = await User.create({ email, password: hashed, name });

     const accessToken  = jwt.sign({ id: user.id, email: user.email }, JWT_SECRET, { expiresIn: JWT_EXPIRES });
     const refreshToken = jwt.sign({ id: user.id, type: 'refresh' }, JWT_REFRESH_SECRET, { expiresIn: JWT_REFRESH_EXPIRES });

     await storeRefreshToken(user.id, refreshToken);

     const verificationToken = crypto.randomBytes(32).toString('hex');
     await sql`INSERT INTO email_verification_tokens ...`;

     return { user, accessToken, refreshToken };
   }

``login(payload)``
~~~~~~~~~~~~~~~~~~~
Validates credentials, looks up the user by email, compares the password
with bcrypt, signs new tokens, and stores the refresh token. Returns
``401`` for both wrong password and non-existent email with the same
``'Invalid credentials'`` message to avoid leaking which field is wrong.

.. code-block:: javascript
   
  async function login(payload) {
    const { error } = loginSchema.validate(payload, { abortEarly: false, stripUnknown: true });
    if (error) {
      const details = error.details.map(d => ({ path: d.path.join('.'), message: d.message }));
      const err = new Error('Validation failed');
      err.status = 400;
      err.details = details;
      throw err;
    }
    const { email, password } = payload;
    const user = await User.findByEmail(email);
    if (!user) {
      const err = new Error('Invalid credentials');
      err.status = 401;
      throw err;
    }
    const valid = await bcrypt.compare(password, user.password || '');
    if (!valid) {
      const err = new Error('Invalid credentials');
      err.status = 401;
      throw err;
    }
    
    const accessToken = jwt.sign({ id: user.id, email: user.email, role: user.role }, JWT_SECRET, { expiresIn: JWT_EXPIRES });
    const refreshToken = jwt.sign({ id: user.id, type: 'refresh' }, JWT_REFRESH_SECRET, { expiresIn: JWT_REFRESH_EXPIRES });
    
    // Store refresh token in database
    await storeRefreshToken(user.id, refreshToken);
    
    // Note: last_login tracking removed - column doesn't exist in current schema
    
    return { 
      user: { id: user.id, email: user.email, name: user.name, role: user.role }, 
      accessToken,
      refreshToken
    };
  }

``refreshTokens(refreshToken)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Verifies the refresh token signature, checks the database to confirm it
is not revoked or expired, fetches the user, signs new tokens, and rotates
the refresh token — revoking the old one and storing the new one.

.. code-block:: javascript

   async function refreshTokens(refreshToken) {
     const decoded = jwt.verify(refreshToken, JWT_REFRESH_SECRET);
     const storedToken = await getRefreshToken(decoded.id, refreshToken);
     if (!storedToken) throw new Error('Refresh token not found or expired');

     const newAccessToken  = jwt.sign({ ... }, JWT_SECRET,  { expiresIn: JWT_EXPIRES });
     const newRefreshToken = jwt.sign({ ... }, JWT_REFRESH_SECRET, { expiresIn: JWT_REFRESH_EXPIRES });

     await replaceRefreshToken(decoded.id, refreshToken, newRefreshToken);
     return { accessToken: newAccessToken, refreshToken: newRefreshToken, user };
   }

``blacklistToken(token)``
~~~~~~~~~~~~~~~~~~~~~~~~~~
Decodes the token to get its expiry, then inserts it into ``token_blacklist``
with ``ON CONFLICT DO NOTHING`` to handle duplicate logout calls safely.

``revokeRefreshToken(token)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Sets ``revoked = true`` on the matching row in ``refresh_tokens``.

``initiatePasswordReset(email)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Looks up the user by email. If not found, returns silently — the controller
handles the always-200 response. If found, deletes any existing reset tokens
for that user and inserts a new one expiring in 1 hour.

``resetPassword(token, newPassword)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Validates the reset token against ``password_reset_tokens``. On success,
updates the password, marks the token as used, and revokes all refresh tokens
for that user as a security measure.


``verifyEmail(token)``
~~~~~~~~~~~~~~~~~~~~~~~
Validates the token against ``email_verification_tokens``, sets
``is_email_verified = true`` on the user, and deletes the used token.


``changePassword(userId, currentPassword, newPassword)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Fetches the user, verifies the current password with bcrypt, hashes the
new password, updates it, and revokes all existing refresh tokens to force
re-authentication on all devices.

.. code-block:: javascript

   async function changePassword(userId, currentPassword, newPassword) {
     const user = await User.findById(userId);
     const valid = await bcrypt.compare(currentPassword, user.password || '');
     if (!valid) { /* throw 401 */ }

     const hashedPassword = await bcrypt.hash(newPassword, 10);
     await sql`UPDATE users SET password = ${hashedPassword}, updated_at = NOW() WHERE id = ${userId}`;
     await sql`UPDATE refresh_tokens SET revoked = true WHERE user_id = ${userId}`;
   }
