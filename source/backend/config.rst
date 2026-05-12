==============
Config Module
==============

Overview
--------

This module handles all configuration and database initialisation for the Student Budget Tracker backend.
It is split across three files:

============== ================================================= =============================================
File           Location                                          Purpose
============== ================================================= =============================================
``index.js``   ``src/config/index.js``                           Central config object loaded from environment variables
``mongoDb.js`` ``src/config/mongoDb.js``                         MongoDB connection initialisation and access
``psql.js``    ``src/config/psql.js``                            PostgreSQL connection initialisation and table creation
============== ================================================= =============================================

All sensitive values (API keys, database URIs, passwords) are loaded from a ``.env`` file
using ``dotenv`` and are never hardcoded in the source code.

---------

index.js — Central Configuration
----------------------------------

This file loads all environment variables and exports them as a single ``config`` object
used throughout the application. Any file that needs a configuration value should import
from this file rather than reading ``process.env`` directly.

**Import:**

.. code-block:: javascript

   import config from '../config/index.js';

Configuration Fields
^^^^^^^^^^^^^^^^^^^^

Server
""""""

===================== ====================== ============= =========================================
Field                 Environment Variable   Default       Description
===================== ====================== ============= =========================================
``port``              ``PORT``               ``3000``      The port the server listens on
``nodeEnv``           ``NODE_ENV``           ``development`` The current environment
===================== ====================== ============= =========================================

Database
""""""""

===================== ====================== ============= =========================================
Field                 Environment Variable   Default       Description
===================== ====================== ============= =========================================
``mongoUri``          ``MONGO_URI``          None          MongoDB connection string
``postgresUri``       ``POSTGRES_URI``       None          PostgreSQL (Neon) connection string
===================== ====================== ============= =========================================

JWT (Authentication)
""""""""""""""""""""

========================= ========================= ============= =========================================
Field                     Environment Variable      Default       Description
========================= ========================= ============= =========================================
``jwtSecret``             ``JWT_SECRET``            ``change_this_secret`` Secret key for signing tokens
``jwtExpire``             ``JWT_EXPIRE``            ``15m``       Access token expiry duration
``jwtRefreshExpire``      ``JWT_REFRESH_EXPIRE``    ``7d``        Refresh token expiry duration
========================= ========================= ============= =========================================

.. warning::

   The default ``jwtSecret`` value of ``change_this_secret`` must be overridden in production
   via the ``JWT_SECRET`` environment variable. Leaving it as the default is a security risk.

API Keys
""""""""

===================== ====================== ============= =========================================
Field                 Environment Variable   Default       Description
===================== ====================== ============= =========================================
``aiApiKey``          ``AI_API_KEY``         None          API key for AI/ML service
``priceApiKey``       ``PRICE_API_KEY``      None          API key for price data service
``mapsApiKey``        ``MAPS_API_KEY``       None          API key for maps service
===================== ====================== ============= =========================================

Notifications
"""""""""""""

===================== ====================== ============= =========================================
Field                 Environment Variable   Default       Description
===================== ====================== ============= =========================================
``fcmServerKey``      ``FCM_SERVER_KEY``     None          Firebase Cloud Messaging key for push notifications
``emailService``      ``EMAIL_SERVICE``      ``gmail``     Email provider
``emailUser``         ``EMAIL_USER``         ``SFT``       Email sender address
``emailPassword``     ``EMAIL_PASSWORD``     None          Email account password
``smsApiKey``         ``SMS_API_KEY``        None          API key for SMS service
===================== ====================== ============= =========================================

Rate Limiting
"""""""""""""

========================== ====================== ============= =========================================
Field                      Environment Variable   Default       Description
========================== ====================== ============= =========================================
``rateLimitWindowMs``      N/A                    ``900000``    Time window for rate limiting (15 minutes in ms)
``rateLimitMaxRequests``   N/A                    ``100``       Max requests allowed per window per IP
========================== ====================== ============= =========================================

Machine Learning
""""""""""""""""

===================== ====================== ============= =========================================
Field                 Environment Variable   Default       Description
===================== ====================== ============= =========================================
``ML_URI``            ``ML_MODEL_URI``       None          URI for the external ML model service
===================== ====================== ============= =========================================

Example .env File
^^^^^^^^^^^^^^^^^

.. code-block:: text

   PORT=3000
   NODE_ENV=development
   MONGO_URI=mongodb+srv://user:password@cluster.mongodb.net/
   POSTGRES_URI=postgresql://user:password@host/dbname
   JWT_SECRET=your_secret_here
   JWT_EXPIRE=15m
   JWT_REFRESH_EXPIRE=7d
   AI_API_KEY=your_ai_key
   EMAIL_SERVICE=gmail
   EMAIL_USER=your@email.com
   EMAIL_PASSWORD=your_email_password

---------

mongoDb.js — MongoDB Initialisation
-------------------------------------

This file manages the connection to MongoDB using the native ``mongodb`` driver.
It exports two functions: one to initialise the connection, and one to retrieve
the database instance for use in controllers.

**Import:**

.. code-block:: javascript

   import { initMongoDb, getNoSql } from '../config/mongoDb.js';

Functions
^^^^^^^^^

initMongoDb
"""""""""""

Connects to MongoDB using the URI from the config and sets up the ``SFT``
(Student Finance Tracker) database. It also ensures the ``notifications``
collection exists, creating it if it does not.

This function should be called once when the server starts up.

**Parameters:** None

**Returns:** ``void``. Logs a success message to the console on connection.

**Example:**

.. code-block:: javascript

   import { initMongoDb } from '../config/mongoDb.js';

   await initMongoDb();
   // Console: "Successfully connected to MongoDB"

---------

getNoSql
""""""""

Returns the active MongoDB database instance. This is used throughout the
application (e.g. in controllers) to access collections.

**Parameters:** None

**Returns:** The active MongoDB ``Db`` instance.

**Throws:** An error if ``initMongoDb`` has not been called first.

**Example:**

.. code-block:: javascript

   import { getNoSql } from '../config/mongoDb.js';

   const db = getNoSql();
   const notifications = await db.collection('notifications').find({}).toArray();

---------

psql.js — PostgreSQL Initialisation
-------------------------------------

This file manages the connection to PostgreSQL using the Neon serverless driver.
It exports the ``sql`` tagged template literal for executing queries, and an
``initPSQL`` function that creates all required tables on startup if they do not
already exist.

**Import:**

.. code-block:: javascript

   import { sql, initPSQL } from '../config/psql.js';

Exports
^^^^^^^

sql
"""

A tagged template literal function from the Neon serverless driver used to
execute parameterised SQL queries safely throughout the application.

**Example:**

.. code-block:: javascript

   const users = await sql`SELECT * FROM users WHERE id = ${userId}`;

---------

initPSQL
""""""""

Creates all required PostgreSQL tables if they do not already exist.
This function should be called once when the server starts up, before
handling any requests.

**Parameters:** None

**Returns:** ``void``. Logs an error to the console if initialisation fails.

The following tables are created by this function:

==================== ==========================================================================
Table                Description
==================== ==========================================================================
``users``            Stores user accounts, preferences, and gamification data
``email_verification_tokens`` Stores tokens used to verify user email addresses
``password_reset_tokens``     Stores tokens used to reset forgotten passwords
``refresh_tokens``   Stores JWT refresh tokens for session management
``token_blacklist``  Stores invalidated tokens (e.g. after logout)
``categories``       Stores income and expense categories per user
``transactions``     Stores all financial transactions made by users
``budgets``          Stores per-user budget limits per category and period
``goals``            Stores user savings goals with targets and deadlines
==================== ==========================================================================

**Example:**

.. code-block:: javascript

   import { initPSQL } from '../config/psql.js';

   await initPSQL();
   // All tables created if they don't already exist

---------

Startup Order
-------------

Both database initialisers must be called before the server starts handling requests.
The recommended startup order is:

.. code-block:: javascript

   import { initMongoDb } from './config/mongoDb.js';
   import { initPSQL } from './config/psql.js';

   await initMongoDb();
   await initPSQL();
   app.listen(config.port);

---------

Dependencies
------------

============================== ========= ==========================================
Dependency                     Version   Purpose
============================== ========= ==========================================
dotenv                         >= 16     Loads environment variables from ``.env``
mongodb                        >= 7.1    Native MongoDB driver
@neondatabase/serverless        >= 0.9    Neon PostgreSQL serverless driver
============================== ========= ==========================================
