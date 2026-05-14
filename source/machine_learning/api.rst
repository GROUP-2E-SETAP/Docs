API 
=================

The FastAPI application that serves as the entry point for the ML service.
Exposes two endpoints — a prediction endpoint and a health check — and handles
input validation via Pydantic models.

------------

Pydantic Models
---------------

Input and output are validated using Pydantic. These are defined at the top
of ``main.py`` and used by the ``/predict`` endpoint.

.. code-block:: python

   class Transaction(BaseModel):
       date: str
       amount: float
       type: str       # "income" or "expense"
       category: str

   class PredictRequest(BaseModel):
       currentBalance: float
       transactions: list[Transaction]
       userId: str = None   # optional

   class PredictionResponse(BaseModel):
       success: bool
       data: dict = None
       error: str = None

-----------------

POST /predict
-------------

Receives a user's transaction history and current balance, runs the runway
prediction, and returns the result. Also registers a background task to
forward the result to the Express backend asynchronously — this does not
block the response.

Returns ``422`` for invalid input (negative balance or empty transactions).
Returns a ``success: false`` response body (not an HTTP error) for any
unexpected exception so the calling service always gets a parseable response.

.. code-block:: python

   @app.post("/predict", response_model=PredictionResponse)
   async def predict(data: PredictRequest, background_tasks: BackgroundTasks):
       if data.currentBalance < 0:
           raise HTTPException(status_code=422, detail="Current balance cannot be negative")
       if not data.transactions:
           raise HTTPException(status_code=422, detail="At least one transaction is required")

       transactions = [t.dict() for t in data.transactions]
       result = predict_runway(transactions, data.currentBalance)

       background_tasks.add_task(send_to_express_backend, result=result, user_id=data.userId)

       return PredictionResponse(success=True, data=result)

------------------

GET /health
-----------

Health check endpoint. Returns service name, version, and the configured
Express backend URL.

.. code-block:: python

   @app.get("/health")
   async def health():
       return {
           "status": "healthy",
           "service": "ml-runway-predictor",
           "version": "1.0.0",
           "express_backend": EXPRESS_API
       }

------------------------

``send_to_express_backend(result, user_id)``
---------------------------------------------

An async helper fired as a background task after each prediction. Posts the
result back to the Express backend at ``EXPRESS_API`` (configured via
``EXPRESS_API_URL`` environment variable, defaults to
``http://localhost:3000/api/runway``). Failures are logged as warnings and
silently swallowed — they do not affect the prediction response.

.. code-block:: python

   async def send_to_express_backend(result: dict, user_id: str = None):
       try:
           payload = {
               "prediction": result,
               "userId": user_id,
               "timestamp": result.get("depletion_date")
           }
           async with httpx.AsyncClient(timeout=10.0) as client:
               response = await client.post(EXPRESS_API, json=payload)
               response.raise_for_status()
       except Exception as e:
           logger.warning(f"Failed to forward prediction to Express backend: {e}")
