ML Analysis 
=======================

After every transaction is created, an ML analysis is automatically triggered
for that user. The analysis sends the user's full transaction history to an
external Python ML service, which returns a budget prediction and financial
health message that is then saved as a notification.

.. note::
   ``triggerMLAnalysis`` is called without ``await`` in the transaction service,
   meaning it runs asynchronously in the background and any failures are
   non-fatal — the transaction is still saved regardless of whether the ML
   call succeeds.

----------------

Flow
----

.. code-block:: text

   Transaction Created
         │
         ▼
   Fetch all user transactions (getTrxModal)
         │
         ▼
   Calculate currentBalance from transaction history
         │
         ▼
   POST payload to ML service (/predict)
         │
         ▼
   Save response as a notification (createNotification)

----------------

``triggerMLAnalysis(userId)``
------------------------------

Fetches all transactions for the user, computes a current balance by summing
income and subtracting expenses, then builds a payload and posts it to the
external ML service. The response is saved as a notification of type
``"Budget Prediction and Health"``.

.. code-block:: javascript

   export default async function triggerMLAnalysis(userId) {
     try {
       const transactions = await getTrxModal(userId);

       const currentBalance = transactions.reduce((acc, t) => {
         if (!t.type) return acc;
         return t.type === "income" ? acc + Number(t.amount) : acc - Number(t.amount);
       }, 0) ;

       const payload = {
         userId: String(userId),
         currentBalance,
         transactions: transactions.map((t) => ({
           date:     t.date,
           amount:   Number(t.amount),
           type:     t.type,
           category: t.name,
         })),
       };

       const response = await axios.post(`${ML_URI}/predict`, payload);
       createNotification(userId, "Budget Prediction and Health", response.data);

     } catch (error) {
       if (error.response) {
         console.error("ML 422 detail:", JSON.stringify(error.response.data, null, 2));
       } else {
         console.error("ML analysis failed (non-fatal):", error.message);
       }
     }
   }

**Payload sent to ML service:**

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Field
     - Description
   * - ``userId``
     - User ID cast to a string
   * - ``currentBalance``
     - Computed balance from all transactions plus a base offset of ``10000``
   * - ``transactions``
     - Array of ``{ date, amount, type, category }`` objects from the joined transaction query

The ML service URL is read from ``config.ML_URI`` and set via environment
variables.
