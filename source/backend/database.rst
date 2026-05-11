================
Database Module
================

Overview
--------

This module handles all database interactions for the Student Budget Tracker backend.
It is split across two components:

- **schema.sql** — defines the full PostgreSQL relational structure (tables, indexes, constraints, triggers)
- **tranasactions.py** — a Python query layer providing programmatic access to transaction data

The primary database is **PostgreSQL**. The Python query functions use a ``psycopg2``-compatible
connection object passed in from the calling code.

---------

File Structure
--------------

=========================================== ================================= ==============================================
File                                        Location                          Purpose
=========================================== ================================= ==============================================
``schema.sql``                              ``src/database/schema.sql``       Defines all tables, indexes and triggers
``tranasactions.py``                        ``src/database/tranasactions.py`` Python functions for querying transactions
=========================================== ================================= ==============================================

---------

Database Schema (schema.sql)
-----------------------------

The schema defines the full relational structure of the application. Below is a breakdown
of each table, its columns, and key constraints.

transactions
^^^^^^^^^^^^

Stores all financial transactions made by users.

=================== ================ ==============================================
Column              Type             Notes
=================== ================ ==============================================
``id``              SERIAL           Primary key, auto-incremented
``user_id``         INTEGER          Foreign key to ``users(id)``, cascades on delete
``category_id``     INTEGER          Foreign key to ``categories(id)``, sets NULL on delete
``amount``          DECIMAL(12,2)    Must be greater than 0
``type``            VARCHAR(10)      One of: ``income``, ``expense``, ``savings``
``description``     TEXT             Optional free-text description
``transaction_date`` DATE            Defaults to current date
``created_at``      TIMESTAMP        Defaults to current timestamp
=================== ================ ==============================================

categories
^^^^^^^^^^

Stores spending and income categories that transactions are grouped under.
Each category has a type (``income`` or ``expense``) used in financial summary calculations.

budgets
^^^^^^^

Stores per-user budget limits, which can be tracked against actual spending
from the transactions table.

allowance
^^^^^^^^^

Stores recurring allowance records for a user.

================ ================ ==============================================
Column           Type             Notes
================ ================ ==============================================
``id``           SERIAL           Primary key
``user_id``      INTEGER          Foreign key to ``users(id)``, cascades on delete
``name``         VARCHAR(100)     Name of the allowance
``amount``       DECIMAL(12,2)    Must be greater than 0
``frequency``    VARCHAR(20)      One of: ``daily``, ``weekly``, ``monthly``, ``yearly``
``start_date``   DATE             Defaults to current date
``end_date``     DATE             Optional end date
``is_active``    BOOLEAN          Defaults to ``TRUE``
``notes``        TEXT             Optional notes
``created_at``   TIMESTAMP        Auto-managed timestamp
``updated_at``   TIMESTAMP        Auto-managed timestamp
================ ================ ==============================================

notifications
^^^^^^^^^^^^^

Stores user notification history and preferences. Works alongside the MongoDB
notifications collection — the SQL table holds relational references, while
MongoDB stores the full notification documents.

Indexes
^^^^^^^

The following indexes are defined to optimise query performance:

========================================= ============= ==================== ========================================
Index Name                                Table         Column(s)            Purpose
========================================= ============= ==================== ========================================
``idx_transactions_user_id``              transactions  user_id              Speed up lookups by user
``idx_transactions_category_id``          transactions  category_id          Speed up category joins
``idx_transactions_date``                 transactions  transaction_date     Speed up date range queries
``idx_allowance_user_id``                 allowances    user_id              Speed up allowance lookups by user
``idx_allowance_is_active``               allowances    user_id, is_active   Speed up filtering active allowances
========================================= ============= ==================== ========================================

Triggers
^^^^^^^^

A trigger function ``update_updated_at_column()`` automatically updates the ``updated_at``
timestamp on any table that uses it, ensuring records always reflect when they were last
modified without requiring the application layer to manage this manually.

---------

Transaction Query Layer (tranasactions.py)
------------------------------------------

This file contains four Python functions that interact with the ``transactions`` table
via a ``psycopg2`` database connection. All functions accept ``conn`` as their first
argument — an open database connection passed in from the calling code.

get_financial_summary
^^^^^^^^^^^^^^^^^^^^^

Returns a high-level financial summary for a given user, aggregating their total income,
total expenses, and net savings.

**Parameters:**

- ``conn`` — an open psycopg2 database connection
- ``user_id`` *(int)* — the ID of the user to summarise

**Returns:** A single row tuple containing:

- ``name`` — the user's name
- ``total_income`` — sum of all transaction amounts in ``income`` categories
- ``total_expenses`` — sum of all transaction amounts in ``expense`` categories
- ``savings`` — total_income minus total_expenses

**Notes:** Uses ``COALESCE`` to return ``0`` instead of ``NULL`` when a user has no income
or expense transactions. Uses ``FILTER`` clauses on ``SUM`` to separately aggregate
income and expenses from a single JOIN.

**Example:**

.. code-block:: python

   from src.database.tranasactions import get_financial_summary

   summary = get_financial_summary(conn, user_id=42)
   print(summary)
   # ('Alice', Decimal('1200.00'), Decimal('850.00'), Decimal('350.00'))

---------

get_all_transactions
^^^^^^^^^^^^^^^^^^^^

Retrieves all transactions for a given user, joined with their category name and type,
ordered from newest to oldest.

**Parameters:**

- ``conn`` — an open psycopg2 database connection
- ``user_id`` *(int)* — the ID of the user whose transactions to fetch

**Returns:** A list of tuples, each containing:

- ``id`` — transaction ID
- ``transaction_date`` — the date of the transaction
- ``category`` — the name of the associated category
- ``type`` — the category type (``income`` or ``expense``)
- ``amount`` — the monetary amount
- ``description`` — optional text description

**Notes:** Returns an empty list if the user has no transactions. Uses a ``LEFT JOIN``
so transactions with no category are still returned.

**Example:**

.. code-block:: python

   from src.database.tranasactions import get_all_transactions

   transactions = get_all_transactions(conn, user_id=42)
   for txn in transactions:
       print(txn)  # (id, date, category, type, amount, description)

---------

delete_transaction
^^^^^^^^^^^^^^^^^^

Deletes a single transaction by its ID, scoped to a specific user to prevent
unauthorised deletions.

**Parameters:**

- ``conn`` — an open psycopg2 database connection
- ``user_id`` *(int)* — the ID of the user who owns the transaction
- ``transaction_id`` *(int)* — the ID of the transaction to delete

**Returns:** ``None``. Commits the deletion to the database.

**Notes:** The ``WHERE`` clause includes both ``id`` and ``user_id``, meaning a user
cannot delete another user's transaction even if they know the transaction ID.

**Example:**

.. code-block:: python

   from src.database.tranasactions import delete_transaction

   delete_transaction(conn, user_id=42, transaction_id=101)

---------

delete_all_transactions
^^^^^^^^^^^^^^^^^^^^^^^

Deletes all transactions belonging to a specific user. This is a destructive operation
and cannot be undone.

**Parameters:**

- ``conn`` — an open psycopg2 database connection
- ``user_id`` *(int)* — the ID of the user whose transactions should all be deleted

**Returns:** ``None``. Commits the deletion to the database.

**Notes:** This function should be called with caution. It is intended for use in
account deletion or data reset flows. No soft-delete mechanism is implemented.

**Example:**

.. code-block:: python

   from src.database.tranasactions import delete_all_transactions

   delete_all_transactions(conn, user_id=42)

---------

Dependencies
------------

================ ========== ========================================
Dependency       Version    Purpose
================ ========== ========================================
PostgreSQL       >= 13      Primary relational database
psycopg2         >= 2.9     Python PostgreSQL adapter
Python           >= 3.8     Runtime for the query layer
================ ========== ========================================

---------

Known Issues
------------

- The filename ``tranasactions.py`` contains a typo (extra ``a``). It should be renamed
  to ``transactions.py`` to avoid import confusion.
- ``delete_all_transactions`` has no soft-delete or audit trail. Consider adding a
  ``deleted_at`` column if data recovery may be needed.
- The ``allowance`` table uses ``VARCHAR(100,2)`` which is invalid SQL — ``VARCHAR``
  does not take a precision argument. This should be ``VARCHAR(100)``.
- The ``allowance`` table ``CHECK`` constraint references ``period`` but the column
  is named ``frequency`` — these must match for the constraint to apply.
