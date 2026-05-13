Categories
==========

Allows users to organise their transactions by creating custom categories
such as "Food", "Rent", or "Salary". Each category belongs to a user and
has a type of either ``income`` or ``expense``.

.. note::
   Deleting a category also deletes all transactions associated with it.

-------------

Schema
-----

Defined in the database initialisation script using PostgreSQL.

.. code-block:: sql

   CREATE TABLE IF NOT EXISTS categories (
     id         SERIAL PRIMARY KEY,
     user_id    INTEGER REFERENCES users(id) ON DELETE CASCADE,
     name       VARCHAR(100) NOT NULL,
     type       VARCHAR(10)  NOT NULL CHECK (type IN ('income', 'expense')),
     icon       VARCHAR(50)  DEFAULT 'default',
     color      VARCHAR(7)   DEFAULT '#000000',
     is_default BOOLEAN      DEFAULT FALSE,
     created_at TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
   );

Routes (``routes/v1/categoryRoutes.js``)
-----------------------------------------

.. code-block:: javascript

   router.post('/', createCategory);
   router.get('/:userId', getCategoryByUserId);
   router.delete('/', deleteCategory);

.. list-table::
   :header-rows: 1
   :widths: 10 30 60

   * - Method
     - Endpoint
     - Description
   * - POST
     - ``/api/v1/categories``
     - Create a new category
   * - GET
     - ``/api/v1/categories/:userId``
     - Fetch all categories for a user
   * - DELETE
     - ``/api/v1/categories``
     - Delete a category by ID

---

Controller (``controllers/categoryController.js``)
----------------------------------------------------

Thin layer responsible for validating the request and returning a response
via ``ResponseHandler``. No business logic lives here — all operations are
delegated to the service layer.

``createCategory``
~~~~~~~~~~~~~~~~~~~

Validates that ``userId``, ``catName``, and ``type`` are all present in the
request body before passing them to the service. Returns a ``400`` if any
field is missing.

.. code-block:: javascript

   export async function createCategory(req, res) {
     try {
       const { userId, catName, type } = req.body;
       if (!userId || !catName || !type) {
         return ResponseHandler.badRequest(res, "All fields required");
       }
       const createService = await createCat(userId, catName, type);
       if (createService) return ResponseHandler.success(res, createService);
       return ResponseHandler.error(res);
     } catch (error) {
       return ResponseHandler.serverError(res, error);
     }
   }

``getCategoryByUserId``
~~~~~~~~~~~~~~~~~~~~~~~~

Extracts ``userId`` from ``req.params`` and delegates directly to the service.
Returns a ``400`` with a plain JSON string if the service returns nothing,
rather than going through ``ResponseHandler`` — note this is inconsistent
with the other controllers.

.. code-block:: javascript

   export async function getCategoryByUserId(req, res) {
     try {
       const { userId } = req.params;
       const getService = await getCat(userId);
       if (getService) return ResponseHandler.success(res, getService);
       return res.status(400).json("Error fetching categories");
     } catch (error) {
       return ResponseHandler.serverError(res, error);
     }
   }

``deleteCategory``
~~~~~~~~~~~~~~~~~~~

Extracts ``catId`` from ``req.body`` and validates it is present before
delegating to the service. Returns a ``400`` if missing.

.. code-block:: javascript

   export async function deleteCategory(req, res) {
     try {
       const { catId } = req.body;
       if (!catId) return ResponseHandler.badRequest(res, "All fields required");
       const deleteService = await deleteCat(catId);
       if (deleteService) return ResponseHandler.success(res);
       return ResponseHandler.error(res);
     } catch (error) {
       return ResponseHandler.serverError(res, error);
     }
   }

---

Service (``services/categoryServices.js``)
-------------------------------------------

All database interaction lives here using tagged template literals via the
``sql`` client from ``psql.js``. Errors are logged and re-thrown to the
controller.

``createCat(userId, catName, type)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Inserts a new row into the ``categories`` table and returns the created record.

.. code-block:: javascript

   export async function createCat(userId, catName, type) {
     try {
       const create = await sql`
         INSERT INTO categories (user_id, name, type)
         VALUES (${userId}, ${catName}, ${type})
         RETURNING *
       `;
       return create[0];
     } catch (error) {
       console.error(errMessage("inserting"), error);
       throw error;
     }
   }

``getCat(userId)``
~~~~~~~~~~~~~~~~~~~

Selects ``id``, ``name``, and ``type`` from ``categories`` filtered by
``user_id``. Returns an array — empty if the user has no categories.

.. note::
   ``icon``, ``color``, ``is_default``, and the timestamp fields are not
   returned by this query even though they exist on the table.

.. code-block:: javascript

   export async function getCat(userId) {
     try {
       const get = await sql`
         SELECT id, name, type
         FROM categories
         WHERE user_id = ${userId}
       `;
       return get;
     } catch (error) {
       console.error(errMessage("selecting"), error);
       throw error;
     }
   }

``deleteCat(catId)``
~~~~~~~~~~~~~~~~~~~~~

Deletes the category and all its associated transactions in two separate queries.
Returns the deleted category record.

.. code-block:: javascript

   export async function deleteCat(catId) {
     try {
       const delCategory = await sql`
         DELETE FROM categories WHERE id = ${catId} RETURNING *
       `;
       const delTransaction = await sql`
         DELETE FROM transactions WHERE category_id = ${catId} RETURNING *
       `;
       return delCategory[0];
     } catch (error) {
       console.error(errMessage("deleting"), error);
       throw error;
     }
   }


