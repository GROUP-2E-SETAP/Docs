Users
=====

Handles user profile management — updating account details and deleting accounts.
Registration and login are handled by the :doc:`auth` feature. The user schema
is defined there as it is shared across both features.

-----------------

Routes (``routes/v1/userRoutes.js``)
-------------------------------------

Two routes — update and delete. Both take ``userId`` as a URL parameter.
No ``authenticate`` middleware is applied.

.. code-block:: javascript

   router.patch('/:userId',  updateUser);
   router.delete('/:userId', deleteUser);

--------------

Controller (``controllers/userControllers.js``)
------------------------------------------------

Unlike other controllers, error handling here is done by catching named errors
thrown by the service rather than validating fields upfront. Each error message
maps to a specific HTTP response.

``updateUser``
~~~~~~~~~~~~~~
Extracts ``userId`` from ``req.params`` and passes the full ``req.body`` to
the service. Maps service errors to the appropriate ``ResponseHandler`` response —
``400`` for missing ID or no fields, ``403`` for forbidden fields, and ``404``
for user not found.

.. code-block:: javascript

   export async function updateUser(req, res) {
     try {
       const user_id = req.params.userId;
       const result = await updateUserService(user_id, req.body);
       if (result) return ResponseHandler.success(res, result);
       return ResponseHandler.error(res);
     } catch (error) {
       if (error.message == "ID required")       return ResponseHandler.badRequest(res, "ID required");
       else if (error.message == "User not found")    return ResponseHandler.notFound(res, "User not found");
       else if (error.message == "No fields provided") return ResponseHandler.badRequest(res, "No fields provided to update");
       else if (error.message == "Access forbidden")   return ResponseHandler.forbidden(res, "Can not access forbidden fields");
       return ResponseHandler.serverError(res, error);
     }
   }

``deleteUser``
~~~~~~~~~~~~~~
Extracts ``userId`` from ``req.params`` and delegates to the service.
Maps ``"ID required"`` to ``400`` and ``"User not found"`` to ``404``.

.. code-block:: javascript

   export async function deleteUser(req, res) {
     try {
       const userId = req.params.userId;
       const result = await deleteUserService(userId);
       if (result) return ResponseHandler.success(res, result, `User : ${userId} deleted successfully`);
       return ResponseHandler.error(res);
     } catch (error) {
       if (error.message == "ID required")    return ResponseHandler.badRequest(res, "ID required");
       else if (error.message == "User not found") return ResponseHandler.notFound(res, "User not found");
       return ResponseHandler.serverError(res, error);
     }
   }

----------------

Service (``services/userServices.js``)
---------------------------------------

Business logic for updating and deleting users. Uses the ``User`` model from
``models/index.js`` for lookups and updates, and ``sql`` from neon for the
delete query directly.

``updateUserService(id, updates)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Validates the ID, checks the user exists, ensures at least one field is
provided, hashes the password if included, then checks all keys in
``updates`` against an allowed fields list. Throws a named error at each
validation step rather than returning HTTP responses directly.

The allowed fields are:

.. code-block:: javascript

   const allowed_fields = ['name', 'email', 'password', 'phone', 'avatar', 'currency', 'language']

Any field outside this list — such as ``role`` or ``id`` — will cause the
service to throw ``"Access forbidden"``, which the controller maps to a ``403``.

.. code-block:: javascript

   export async function updateUserService(id, updates) {
     if (!id) throw new Error("ID required");

     const user = await User.findById(id);
     if (!user) throw new Error("User not found");

     if (!Object.keys(updates).length) throw new Error("No fields provided");

     if (updates.password) {
       updates.password = await bcrypt.hash(updates.password, 10);
     }

     const invalid = Object.keys(updates).filter(key => !allowed_fields.includes(key));
     if (invalid.length) throw new Error("Access forbidden");

     const result = await User.update(id, updates);
     return result;
   }

.. note::
   Password updates are handled here as a fallback — ``authService`` already
   has a dedicated ``changePassword`` function with current password verification.
   Updating via this endpoint skips that check entirely.

``deleteUserService(userId)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Validates the ID, checks the user exists via ``User.findById()``, then
deletes the row directly using ``sql``. Returns the deleted user record.
Cascading deletes on the database handle removal of all related data
(transactions, budgets, goals, categories, notifications).

.. code-block:: javascript

   export async function deleteUserService(userId) {
     if (!userId) throw new Error("ID required");

     const user = await User.findById(userId);
     if (!user) throw new Error("User not found");

     try {
       const delete_user = await sql`
         DELETE FROM users WHERE id = ${userId} RETURNING *
       `;
       return delete_user[0];
     } catch (error) {
       throw new Error(error.message);
     }
   }
