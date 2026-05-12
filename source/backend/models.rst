==============
Models Module
==============

Overview
--------

This module defines the data models for the Student Budget Tracker backend.
The application uses two databases:

- **PostgreSQL** — the primary relational database, accessed via the ``sql`` tagged template from ``psql.js``
- **MongoDB** — a NoSQL store accessed via Mongoose, used for notifications and user data

The models folder contains three files:

===================== =============================================
File                  Purpose
===================== =============================================
``index.js``          PostgreSQL User class with static query methods
``user.js``           Mongoose schema and model for User documents
``Notifications.js``  Mongoose schema and model for Notification documents
===================== =============================================

---------

index.js — PostgreSQL User Model
----------------------------------

This file defines a ``User`` class that provides static methods for interacting
with the ``users`` table in PostgreSQL. It uses the ``sql`` tagged template literal
from the project's PostgreSQL config to execute parameterised queries safely.

User Class
^^^^^^^^^^

**Import:**

.. code-block:: javascript

   import { User } from '../models/index.js';

Methods
^^^^^^^

findById
""""""""

Finds a single user by their PostgreSQL ID.

**Parameters:**

- ``id`` *(integer)* — the ID of the user to look up

**Returns:** A single user object, or ``null`` if not found.

**Example:**

.. code-block:: javascript

   const user = await User.findById(1);
   console.log(user); // { id: 1, name: 'Alice', email: 'alice@example.com', ... }

---------

findByEmail
"""""""""""

Finds a single user by their email address.

**Parameters:**

- ``email`` *(string)* — the email address to look up

**Returns:** A single user object, or ``null`` if not found.

**Example:**

.. code-block:: javascript

   const user = await User.findByEmail('alice@example.com');

---------

create
""""""

Inserts a new user record into the ``users`` table.

**Parameters:**

- ``userData`` *(object)* — an object containing:

  - ``email`` *(string)* — the user's email address
  - ``password`` *(string)* — the user's hashed password
  - ``name`` *(string)* — the user's full name

**Returns:** The newly created user object.

**Example:**

.. code-block:: javascript

   const newUser = await User.create({
     email: 'bob@example.com',
     password: hashedPassword,
     name: 'Bob'
   });

---------

update
""""""

Updates an existing user record by their ID.

**Parameters:**

- ``id`` *(integer)* — the ID of the user to update
- ``updates`` *(object)* — key-value pairs of fields to update

**Returns:** The updated user object.

**Example:**

.. code-block:: javascript

   const updated = await User.update(1, { name: 'Alice Smith' });

---------

user.js — Mongoose User Schema
--------------------------------

This file defines the Mongoose schema and model for User documents stored in MongoDB.
It includes password hashing via ``bcryptjs`` before saving, and a method for
comparing passwords during login.

Schema Fields
^^^^^^^^^^^^^

===================== ============= ========= ==============================================
Field                 Type          Required  Notes
===================== ============= ========= ==============================================
``name``              String        Yes       Trimmed whitespace
``email``             String        Yes       Unique, lowercased, validated by regex
``password``          String        Yes       Min 6 characters, excluded from queries by default
``phone``             String        No        Trimmed whitespace
``avatar``            String        No        Defaults to ``null``
``currency``          String        No        Defaults to ``'USD'``
``language``          String        No        Defaults to ``'en'``
``isVerified``        Boolean       No        Defaults to ``false``
``role``              String        No        One of: ``'user'``, ``'admin'``. Defaults to ``'user'``
``gamificationLevel`` Number        No        Defaults to ``1``
``gamificationPoints`` Number       No        Defaults to ``0``
``createdAt``         Date          No        Auto-managed by timestamps
``updatedAt``         Date          No        Auto-managed by timestamps
===================== ============= ========= ==============================================

Middleware
^^^^^^^^^^

**Pre-save password hashing**

Before a user document is saved, if the password field has been modified,
it is automatically hashed using ``bcryptjs`` with a salt round of 10.
This means plain text passwords are never stored in the database.

Methods
^^^^^^^

comparePassword
"""""""""""""""

Compares a plain text candidate password against the stored hashed password.
Used during login to verify a user's credentials.

**Parameters:**

- ``candidatePassword`` *(string)* — the plain text password to check

**Returns:** ``true`` if the password matches, ``false`` otherwise.

**Example:**

.. code-block:: javascript

   const isMatch = await user.comparePassword('mypassword123');
   if (isMatch) {
     // login successful
   }

---------

Notifications.js — Mongoose Notification Schema
-------------------------------------------------

This file defines the Mongoose schema and model for Notification documents
stored in MongoDB. The ``user_id`` field links each notification back to a
user in the PostgreSQL ``users`` table.

Schema Fields
^^^^^^^^^^^^^

============ ========= ========= ==============================================
Field        Type      Required  Notes
============ ========= ========= ==============================================
``user_id``  Number    Yes       References the PostgreSQL ``users.id``
``type``     String    Yes       One of: ``budget_alert``, ``achievement``, ``reminder``, ``tip``, ``system``, ``transaction``
``title``    String    Yes       Short title of the notification
``message``  String    Yes       Full notification message body
``priority`` String    No        One of: ``low``, ``medium``, ``high``. Defaults to ``medium``
``is_read``  Boolean   No        Defaults to ``false``
``read_at``  Date      No        Defaults to ``null``, set when notification is read
``data``     Object    No        Optional extra data payload. Defaults to ``null``
============ ========= ========= ==============================================

**Notes:**

- Timestamps (``createdAt``, ``updatedAt``) are automatically managed by Mongoose via the ``{ timestamps: true }`` option.
- The ``user_id`` field is a plain Number (not a Mongoose ObjectId) to match the integer primary key used in PostgreSQL.

**Example:**

.. code-block:: javascript

   const notification = await Notification.create({
     user_id: 42,
     type: 'budget_alert',
     title: 'Budget Exceeded',
     message: 'You have exceeded your monthly food budget.',
     priority: 'high'
   });

---------

Dependencies
------------

============= ========= ==========================================
Dependency    Version   Purpose
============= ========= ==========================================
mongoose      >= 9.3    MongoDB object modelling
bcryptjs      >= 2.4    Password hashing and comparison
PostgreSQL    >= 13     Primary relational database
============= ========= ==========================================
