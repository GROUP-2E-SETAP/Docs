Budgets
=======

Allows users to set spending limits against a specific category over a defined
period. Budgets are linked to both a user and a category, and a user can only
have one budget per category per period, enforced at the database level via
a unique constraint.

----------------

Schema
--------

Stores one budget per user per category per period. The ``period`` field is
constrained to ``daily``, ``weekly``, ``monthly``, or ``yearly``.

.. code-block:: sql

   CREATE TABLE IF NOT EXISTS budgets (
     id          SERIAL PRIMARY KEY,
     user_id     INTEGER      REFERENCES users(id)      ON DELETE CASCADE,
     category_id INTEGER      REFERENCES categories(id) ON DELETE CASCADE,
     amount      DECIMAL(12,2) NOT NULL,
     period      VARCHAR(20)  DEFAULT 'monthly' CHECK (period IN ('daily', 'weekly', 'monthly', 'yearly')),
     start_date  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
     end_date    TIMESTAMP,
     created_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
     updated_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
     UNIQUE (user_id, category_id, period)
   );

--------------

Routes (``routes/v1/budgetRoutes.js``)
---------------------------------------

Four routes covering full CRUD. No ``authenticate`` middleware is applied —
unlike auth routes, budget routes are currently unprotected.

.. code-block:: javascript

   router.post('/',          addBudget);
   router.get('/:userId',   getBudgets);
   router.put('/:budgetId', updateExistingBudget);
   router.delete('/:budgetId', removeBudget);

----------------

Controller (``controllers/budgetControllers.js``)
--------------------------------------------------

Validates request fields and delegates to the service layer via
``ResponseHandler``.

``addBudget``
~~~~~~~~~~~~~
Extracts ``userId``, ``categoryId``, ``amount``, ``period``, ``startDate``,
and ``endDate`` from ``req.body``. Returns ``400`` if ``userId``,
``categoryId``, or ``amount`` are missing. Uses ``typeof amount === 'undefined'``
so that ``0`` is accepted as a valid amount.

.. code-block:: javascript

   export async function addBudget(req, res) {
     try {
       const { userId, categoryId, amount, period, startDate, endDate } = req.body;
       if (!userId || !categoryId || typeof amount === 'undefined') {
         return ResponseHandler.badRequest(res, "userId, categoryId, and amount are required fields");
       }
       const newBudget = await createBudget(userId, categoryId, amount, period, startDate, endDate);
       if (newBudget) return ResponseHandler.success(res, newBudget);
       return ResponseHandler.error(res);
     } catch (error) {
       return ResponseHandler.serverError(res, error);
     }
   }

``getBudgets``
~~~~~~~~~~~~~~
Extracts ``userId`` from ``req.params`` and returns ``404`` if no budgets
are found, unlike most other GET endpoints which return an empty array.

.. code-block:: javascript

   export async function getBudgets(req, res) {
     try {
       const { userId } = req.params;
       if (!userId) return ResponseHandler.badRequest(res, "userId is required");
       const budgets = await getBudgetsByUserId(userId);
       if (budgets) return ResponseHandler.success(res, budgets);
       return ResponseHandler.notFound(res, "budgets not found");
     } catch (error) {
       return ResponseHandler.serverError(res, error);
     }
   }

``updateExistingBudget``
~~~~~~~~~~~~~~~~~~~~~~~~
Extracts ``budgetId`` from ``req.params`` and ``amount`` from ``req.body``.
Only ``amount`` can be updated — ``period``, ``startDate``, and ``endDate``
cannot be changed via this endpoint. Returns ``404`` if the budget does not exist.

.. code-block:: javascript

   export async function updateExistingBudget(req, res) {
     try {
       const { budgetId } = req.params;
       const { amount } = req.body;
       if (!budgetId || typeof amount === 'undefined') {
         return ResponseHandler.badRequest(res, "budgetId and amount are required fields");
       }
       const updatedBudget = await updateBudget(budgetId, amount);
       if (updatedBudget) return ResponseHandler.success(res, updatedBudget);
       return ResponseHandler.notFound(res, "Budget not found or could not be updated");
     } catch (error) {
       return ResponseHandler.serverError(res, error);
     }
   }


``removeBudget``
~~~~~~~~~~~~~~~~
Extracts ``budgetId`` from ``req.params`` and returns ``404`` if not found.

.. code-block:: javascript

   export async function removeBudget(req, res) {
     try {
       const { budgetId } = req.params;
       if (!budgetId) return ResponseHandler.badRequest(res, "budgetId is required");
       const deletedBudget = await deleteBudget(budgetId);
       if (deletedBudget) return ResponseHandler.success(res, deletedBudget);
       return ResponseHandler.notFound(res, "Budget not found or could not be deleted");
     } catch (error) {
       return ResponseHandler.serverError(res, error);
     }
   }

-------------

Service (``services/budgetServices.js``)
-----------------------------------------

All database interaction using the ``sql`` from neon.
Errors are logged and re-thrown to the controller.

``createBudget(userId, categoryId, amount, period, startDate, endDate)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Inserts a new budget. Defaults ``period`` to ``'monthly'``, ``startDate``
to the current timestamp, and ``endDate`` to ``null`` if not provided.

.. code-block:: javascript

   export async function createBudget(userId, categoryId, amount, period, startDate, endDate) {
     try {
       const create = await sql`
         INSERT INTO budgets (user_id, category_id, amount, period, start_date, end_date)
         VALUES (${userId}, ${categoryId}, ${amount}, ${period || 'monthly'}, ${startDate || new Date().toISOString()}, ${endDate || null})
         RETURNING *
       `;
       return create[0];
     } catch (error) {
       console.error(errMessage("inserting"), error);
       throw error;
     }
   }

.. note::
   If a budget already exists for the same ``user_id``, ``category_id``, and
   ``period`` combination, the database will throw a unique constraint violation.

``getBudgetsByUserId(userId)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Joins ``budgets`` with ``categories`` to return the category ``name``,
``color``, and ``icon`` alongside each budget, ordered by creation date descending.

.. code-block:: javascript

   export async function getBudgetsByUserId(userId) {
     try {
       const get = await sql`
         SELECT
           b.id, b.user_id, b.category_id, b.amount, b.period,
           b.start_date, b.end_date, b.created_at, b.updated_at,
           c.name as category_name, c.color as category_color, c.icon as category_icon
         FROM budgets b
         JOIN categories c ON b.category_id = c.id
         WHERE b.user_id = ${userId}
         ORDER BY b.created_at DESC
       `;
       return get;
     } catch (error) {
       console.error(errMessage("selecting"), error);
       throw error;
     }
   }

``updateBudget(budgetId, amount)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Updates only the ``amount`` and ``updated_at`` fields. Returns the updated
record or ``undefined`` if no matching budget was found.

.. code-block:: javascript

   export async function updateBudget(budgetId, amount) {
     try {
       const update = await sql`
         UPDATE budgets
         SET amount = ${amount}, updated_at = NOW()
         WHERE id = ${budgetId}
         RETURNING *
       `;
       return update[0];
     } catch (error) {
       console.error(errMessage("updating"), error);
       throw error;
     }
   }

``deleteBudget(budgetId)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Deletes the budget by ``id`` and returns the deleted record.

.. code-block:: javascript

   export async function deleteBudget(budgetId) {
     try {
       const delBudget = await sql`
         DELETE FROM budgets WHERE id = ${budgetId} RETURNING *
       `;
       return delBudget[0];
     } catch (error) {
       console.error(errMessage("deleting"), error);
       throw error;
     }
   }
