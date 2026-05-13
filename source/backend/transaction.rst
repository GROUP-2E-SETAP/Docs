Transactions
===========

Records financial transaction input by the user, linking it to a specific income type and category.
All other features (e.g. budgets, goals, categories, notifications, ML ...etc) are dependant on **transactions** 
making it the core of the application.


.. note::
   When a transaction is created, an ML analysis is automatically triggered 
   for that user via ``triggerMLAnalysis(userId)`` to update spending insights.

.. note::
   Fetching transactions returns a joined result with the category ``name``
   and ``type`` alongside each transaction, ordered by date descending.


Schema
-------

Defined using ``PostgreSQL``

.. code-block:: sql
    
    CREATE TABLE IF NOT EXISTS transactions (
      id SERIAL PRIMARY KEY,
      user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
      category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
      amount DECIMAL(12,2) NOT NULL,
      description VARCHAR(255),
      date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

-----------------------------

Routes(``routes/v1/transactionRoutes.js``)
---------------------------------------

.. code-block:: javascript
   
    router.post('/', createTrx);
    router.get('/:userId', getTrxByUserId);
    router.delete('/', deleteTrx);

------------------------------

.. list-table::
   :header-rows: 1
   :widths: 10 30 60

   * - Method
     - Endpoint
     - Description
   * - POST
     - ``/api/v1/transactions``
     - Create a new transactions
   * - GET
     - ``/api/v1/transactions/:userId``
     - Fetch all transactions by userId
   * - DELETE
     - ``/api/v1/transactions``
     - Delete all transactions by userID

------------

Modals(``models/transactionModals.js``)
----------------------------------------

These are function blocks which deals only with database manipulation

``createTrxModal``
~~~~~~~~~~~~~~~~~~

Inserts given data to transactions table

.. code-block:: javascript
   
  export async function createTrxModal(userId,categoryId,amount,description,date) {
  try {
    const create = await sql`
      INSERT INTO transactions (user_id, category_id, amount, description, date)
      VALUES (${userId}, ${categoryId}, ${amount}, ${description}, ${date || new Date().toISOString()})
      RETURNING * 
  `;

    return create[0];
  } catch (error) {
    throw error ;
  }
}

``getTrxModal``
~~~~~~~~~~~~~~~

Join transactions table with category table and return all transaction data along with 
category name and type of given userId in latest to earliest order.

.. code-block:: javascript
   
  export async function getTrxModal(userId) {
    try {
      const get  = await sql`
        SELECT 
          t.id, t.user_id, t.category_id,c.type,c.name, t.amount, t.description, t.date, t.created_at, t.updated_at
        FROM 
          transactions t 
        JOIN 
          categories c 
        ON 
          t.category_id = c.id
        WHERE 
          t.user_id = ${userId}
        ORDER BY date DESC
    `;
      return get ;
    } catch (error) {
      throw error ;
    }
   }

``deleteTrxModal(``
~~~~~~~~~~~~~~~~~~

Deletes all transactions of given userId

.. code-block:: javascript

  export async function deleteTrxModal(transactionId) {
    try {

      const delTransaction = await sql`
        DELETE 
          FROM transactions 
        WHERE 
          id = ${transactionId}
        RETURNING * 
  `;

      return delTransaction[0];
    } catch (error) {
      throw error ;
    }
  }

------------

Controllers (``controllers/transactionControllers.js``)
--------------------------------------------------------

Thin layer responsible for validating the request and returning a response
via ``ResponseHandler``. All business logic is delegated to the service layer.

``createTrx``
~~~~~~~~~~~~~
Extracts ``userId``, ``categoryId``, ``amount``, ``description``, and ``date``
from ``req.body``. Returns ``400`` if ``userId``, ``categoryId``, or ``amount``
are missing. Note that ``amount`` is checked with ``typeof amount === 'undefined'``
rather than a falsy check, so ``0`` is a valid amount.

.. code-block:: javascript

   export async function createTrx(req, res) {
     try {
       const { userId, categoryId, amount, description, date } = req.body;
       if (!userId || !categoryId || typeof amount === 'undefined') {
         return ResponseHandler.badRequest(res, "userId, categoryId, and amount are required fields");
       }
       const newTransaction = await createTransaction(userId, categoryId, amount, description, date);
       if (newTransaction) return ResponseHandler.success(res, newTransaction);
       return ResponseHandler.error(res);
     } catch (error) {
       return ResponseHandler.serverError(res, error);
     }
   }

``getTrxByUserId``
~~~~~~~~~~~~~~~~~~
Extracts ``userId`` from ``req.params`` and delegates to the service.
Returns ``400`` with a plain JSON string if the service returns nothing —
note this is inconsistent with the other controllers which use ``ResponseHandler``.

.. code-block:: javascript

   export async function getTrxByUserId(req, res) {
     try {
       const { userId } = req.params;
       if (!userId) {
         return ResponseHandler.badRequest(res, "userId is required");
       }
       const transactions = await getTransactionsByUserId(userId);
       if (transactions) return ResponseHandler.success(res, transactions);
       return res.status(400).json("Error fetching transactions");
     } catch (error) {
       return ResponseHandler.serverError(res, error);
     }
   }

``deleteTrx``
~~~~~~~~~~~~~
Extracts ``transactionId`` from ``req.body`` and validates it is present
before delegating to the service. Returns ``400`` if missing.

.. code-block:: javascript

   export async function deleteTrx(req, res) {
     try {
       const transactionId = req.body.transactionId;
       if (!transactionId) return ResponseHandler.badRequest(res, "transactionId is required");
       const deletedTransaction = await deleteTransaction(transactionId);
       if (deletedTransaction) return ResponseHandler.success(res, deletedTransaction);
       return ResponseHandler.error(res, "Transaction not found or could not be deleted");
     } catch (error) {
       return ResponseHandler.serverError(res, error);
     }
   }

--------------------

Services (``services/transactionServices.js``)
-----------------------------------------------
Acts as the bridge between the controller and the model. Also responsible
for triggering ML analysis after a transaction is created.

``createTransaction(userId, categoryId, amount, description, date)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Calls ``createTrxModal`` to insert the transaction, then triggers
``triggerMLAnalysis(userId)`` to update spending insights for that user.

.. code-block:: javascript

   export async function createTransaction(userId, categoryId, amount, description, date) {
     try {
       const response = await createTrxModal(userId, categoryId, amount, description, date);
       triggerMLAnalysis(userId);
       return response;
     } catch (error) {
       console.error(errMessage("inserting"), error);
       throw error;
     }
   }

.. note::
   ``triggerMLAnalysis`` is called after every transaction creation but there
   is no await on it, meaning it runs asynchronously and any errors it throws
   will not be caught here.

``getTransactionsByUserId(userId)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Delegates directly to ``getTrxModal`` with no additional logic.

.. code-block:: javascript

   export async function getTransactionsByUserId(userId) {
     try {
       return getTrxModal(userId);
     } catch (error) {
       console.error(errMessage("selecting"), error);
       throw error;
     }
   }

``deleteTransaction(transactionId)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Delegates directly to ``deleteTrxModal`` with no additional logic.

.. code-block:: javascript

   export async function deleteTransaction(transactionId) {
     try {
       return deleteTrxModal(transactionId);
     } catch (error) {
       console.error(errMessage("deleting"), error);
       throw error;
     }
   }
