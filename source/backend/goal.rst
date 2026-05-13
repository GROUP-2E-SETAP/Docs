Goals
=====

Allows users to set savings goals with a target amount and a deadline.
Progress is tracked via a ``current`` field which is updated as the user
saves towards their target.

-------------------

Schema
------

Stores one savings goal per row linked to a user. The ``target`` must be
greater than zero and ``current`` cannot go negative — both enforced at the
database level via CHECK constraints.

.. code-block:: sql

   CREATE TABLE IF NOT EXISTS goals (
     id         SERIAL PRIMARY KEY,
     user_id    INTEGER      REFERENCES users(id) ON DELETE CASCADE,
     name       VARCHAR(200) NOT NULL DEFAULT 'Savings Goal',
     target     DECIMAL(10,2) NOT NULL CHECK (target > 0),
     current    DECIMAL(10,2) NOT NULL DEFAULT 0 CHECK (current >= 0),
     deadline   TIMESTAMP    NOT NULL DEFAULT (NOW() + INTERVAL '7 days'),
     created_at TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
   );

----------------

Routes (``routes/v1/goalsRoutes.js``)
--------------------------------------

Three routes — create, update, and delete. No ``authenticate`` middleware
applied and no GET route exists;

.. code-block:: javascript

   router.post('/',   createGoals);
   router.patch('/',  updateGoals);
   router.delete('/', deleteGoals);

-----------------

Controller (``controllers/goalsControllers.js``)
-------------------------------------------------

Validates request fields and delegates to the service layer via
``ResponseHandler``.

``createGoals``
~~~~~~~~~~~~~~~
Extracts ``userId``, ``goalName``, ``targetAmount``, and ``deadline`` from
``req.body``. Returns ``400`` if any field is missing, and a separate ``400``
if ``targetAmount`` is zero or negative.

.. code-block:: javascript

   export async function createGoals(req, res) {
     try {
       const { userId, goalName, targetAmount, deadline } = req.body;
       if (!userId || !goalName || !targetAmount || !deadline) {
         return ResponseHandler.badRequest(res, "All fields required");
       }
       if (targetAmount <= 0) {
         return ResponseHandler.badRequest(res, "Target amount too small");
       }
       const createGoalService = await createG(userId, goalName, targetAmount, deadline);
       if (createGoalService) return ResponseHandler.success(res, createGoalService);
       return ResponseHandler.error(res);
     } catch (error) {
       return ResponseHandler.serverError(res, error);
     }
   }

``updateGoals``
~~~~~~~~~~~~~~~
Extracts ``goalId`` and ``newAmount`` from ``req.body`` and updates the
``current`` field of the goal. Both fields are required.

.. code-block:: javascript

   export async function updateGoals(req, res) {
     try {
       const { goalId, newAmount } = req.body;
       if (!goalId || !newAmount) {
         return ResponseHandler.badRequest(res, "All fields required");
       }
       const updateGoalsService = await updateG(goalId, newAmount);
       if (updateGoalsService) return ResponseHandler.success(res, updateGoalsService);
       return ResponseHandler.error(res);
     } catch (error) {
       return ResponseHandler.serverError(res, error);
     }
   }

``deleteGoals``
~~~~~~~~~~~~~~~
Extracts ``goalId`` from ``req.body`` and delegates to the service.
Returns ``400`` if missing.

.. code-block:: javascript

   export async function deleteGoals(req, res) {
     try {
       const { goalId } = req.body;
       if (!goalId) return ResponseHandler.badRequest(req, "WHERES THE ID BRO");
       const deleteGoalService = await delG(goalId);
       if (deleteGoalService) return ResponseHandler.success(res, deleteGoalService);
       return ResponseHandler.error(res);
     } catch (error) {
       return ResponseHandler.serverError(res, error);
     }
   }

---------------

Service (``services/goalsServices.js``)
----------------------------------------

All database interaction using ``sql`` from neon. Errors are logged and
re-thrown to the controller.

``createG(userId, goalName, targetAmount, deadline)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Inserts a new goal into the ``goals`` table and returns the created record.

.. code-block:: javascript

   export async function createG(userId, goalName, targetAmount, deadline) {
     try {
       const create = await sql`
         INSERT INTO goals (user_id, name, target, deadline)
         VALUES (${userId}, ${goalName}, ${targetAmount}, ${deadline})
         RETURNING *
       `;
       return create[0];
     } catch (error) {
       console.error(errMessage("creating", error));
       throw error;
     }
   }

``updateG(goalId, newAmount)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Updates the ``current`` field of a goal by its ``id`` and returns the
updated record.

.. code-block:: javascript

   export async function updateG(goalId, newAmount) {
     try {
       const update = await sql`
         UPDATE goals
         SET current = ${newAmount}
         WHERE id = ${goalId}
         RETURNING *
       `;
       return update[0];
     } catch (error) {
       console.error(errMessage("updating", error));
       throw error;
     }
   }

``delG(goalId)``
~~~~~~~~~~~~~~~~~
Deletes a goal by ``id`` and returns the deleted record.

.. code-block:: javascript

   export async function delG(goalId) {
     try {
       const del = await sql`
         DELETE FROM goals WHERE id = ${goalId} RETURNING *
       `;
       return del[0];
     } catch (error) {
       console.error(errMessage("deleting", error));
       throw error;
     }
   }
