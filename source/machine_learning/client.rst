Express Client 
===========================================

A sample Express router that demonstrates how to integrate with the FastAPI
ML service from the Node.js backend. Provides routes for requesting
predictions, receiving callbacks from the ML service, checking ML service
health, and fetching stored predictions.

---------------------

Configuration
-------------

.. code-block:: javascript

   const ML_API_URL     = process.env.ML_API_URL     || 'http://localhost:8000';
   const ML_API_TIMEOUT = parseInt(process.env.ML_API_TIMEOUT || '30000');

   const mlClient = axios.create({
     baseURL: ML_API_URL,
     timeout: ML_API_TIMEOUT,
     headers: { 'Content-Type': 'application/json' }
   });

--------------

Routes
------

**POST /api/predict**

Validates ``currentBalance`` and ``transactions`` then forwards the request
to the ML service via ``getPredictionFromML()``. Returns the prediction result
on success.

.. code-block:: javascript

   router.post('/api/predict', async (req, res) => {
     const { userId, currentBalance, transactions } = req.body;

     if (!currentBalance || currentBalance < 0)
       return res.status(422).json({ success: false, error: 'currentBalance must be a positive number' });

     if (!transactions || transactions.length === 0)
       return res.status(422).json({ success: false, error: 'transactions array is required' });

     const predictionResult = await getPredictionFromML({ userId, currentBalance, transactions });
     res.json({ success: true, prediction: predictionResult.data, userId });
   });

**POST /api/runway**

Callback endpoint called by the FastAPI service asynchronously after each
prediction. Receives the prediction result, ``userId``, and ``timestamp``.
Database save and user notification are stubbed as TODOs.

**GET /api/ml-health**

Proxies a health check to the ML service and returns its status. Returns
``503`` if the ML service is unreachable.

**GET /api/runway/:userId/latest**

Intended to return the latest stored prediction for a user. Database query
is stubbed as a TODO — currently returns an empty object.

---------------

``getPredictionFromML(predictionData)``
----------------------------------------

Helper function that posts to ``/predict`` on the ML service and returns
the response data. Throws an error if the request fails.

.. code-block:: javascript

   async function getPredictionFromML(predictionData) {
     try {
       const response = await mlClient.post('/predict', predictionData);
       return response.data;
     } catch (error) {
       throw new Error(`Failed to get prediction: ${error.message}`);
     }
   }
