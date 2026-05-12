Backend Setup
=============

This guide walks you through setting up the SFT backend for local development.

Prerequisites
-------------

Make sure you have the following installed:

- Node v24.12.0 or higher

Installation
------------

1. **Clone the repository**

   .. code-block:: bash

      git clone git@github.com:GROUP-2E-SETAP/Backend.git
      cd Backend

2. **Install required packages**

   .. code-block:: bash

      npm install

3. **Running development server**

   .. code-block:: bash

      npm run dev

4. **Running main server**

   .. code-block:: bash

      npm start

Environment Variables
---------------------

.. code-block:: bash

   # file: .env.example

   # Server Configuration
   NODE_ENV=development
   PORT=3000

   # For Neon or hosted PostgreSQL:
   POSTGRES_URI=postgresql://user:password@host.region.neon.tech/dbname?sslmode=require

   # For MongoDB Atlas:
   MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/setap_transactions?retryWrites=true&w=majority

   # JWT Secrets (Change these to random secure strings!)
   JWT_SECRET=your_super_secure_jwt_secret_change_this
   JWT_REFRESH_SECRET=your_super_secure_refresh_secret_change_this
   JWT_EXPIRES=15m
   JWT_REFRESH_EXPIRES=7d

   # Redis (for token blacklist and caching)
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_PASSWORD=

   # Email Service (for notifications)
   EMAIL_SERVICE=gmail
   EMAIL_USER=your-email@gmail.com
   EMAIL_PASSWORD=your-app-specific-password

   # External API Keys
   AI_API_KEY=your_openai_api_key

   # CORS Configuration
   CORS_ORIGIN=http://localhost:3000

   # Encryption
   ENCRYPTION_KEY=your_32_character_encryption_key

   # Rate Limiting
   RATE_LIMIT_WINDOW_MS=900000
   RATE_LIMIT_MAX_REQUESTS=100

Databases
---------

We use PostgreSQL with *Neon* and *MongoDB Atlas*.

Neon Setup
~~~~~~~~~~

Instructions at https://console.neon.tech/app/

MongoDB Setup
~~~~~~~~~~~~~

Instructions at https://www.mongodb.com/

API Reference
-------------

Base URL
~~~~~~~~

.. code-block:: text

   BASE_URL: http://localhost:3000/api/v1
