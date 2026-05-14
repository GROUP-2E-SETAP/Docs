Predictor 
============================

Core prediction logic for the ML service. Computes financial runway —
how many days until a user's balance reaches zero — based on their
transaction history and current balance.

A ``RandomForestRegressor`` model is loaded from ``runway_model.pkl`` at
startup if the file exists, but the current prediction logic uses a direct
arithmetic calculation rather than the model. The model infrastructure
is in place for future use.

--------------------

``extract_features(transactions, current_balance)``
----------------------------------------------------

Converts the raw transaction list into a Pandas DataFrame and computes
summary statistics used by the predictor.

.. code-block:: python

   def extract_features(transactions, current_balance):
       df = pd.DataFrame(transactions)
       df['date'] = pd.to_datetime(df['date'])
       df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)

       income     = float(df[df['type'] == 'income']['amount'].sum())
       expenses   = float(df[df['type'] == 'expense']['amount'].sum())
       daily_burn = expenses / max(len(df.groupby('date')), 1)

       return {
           'starting_balance':  float(current_balance),
           'total_income':      income,
           'total_expenses':    expenses,
           'avg_daily_burn':    daily_burn,
           'transaction_count': int(len(df))
       }

``avg_daily_burn`` is computed as total expenses divided by the number of
unique days in the transaction history, giving an average daily spend rate.

-------------------

``predict_runway(transactions, current_balance)``
-------------------------------------------------

Main prediction function. Computes runway as
``current_balance / avg_daily_burn``, capped at 365 days, then classifies
the result into a status and generates a recommendation message.

For ``critical`` and ``warning`` statuses, the top 3 expense categories
are identified and split into fixed costs (rent, mortgage, loan, insurance)
and discretionary spending, producing a targeted ``message_2`` field.

.. code-block:: python

   def predict_runway(transactions, current_balance):
       features   = extract_features(transactions, current_balance)
       daily_burn = features['avg_daily_burn']

       simple_runway = int(current_balance / daily_burn) if daily_burn > 0 else 999
       runway_days   = min(simple_runway, 365)
       depletion_date = (datetime.now() + timedelta(days=runway_days)).strftime('%Y-%m-%d')

       # status classification
       if runway_days <= 7:   status = "critical"
       elif runway_days <= 30: status = "warning"
       elif runway_days <= 90: status = "caution"
       else:                   status = "healthy"

       return {
           "status":          status,
           "runway_days":     runway_days,
           "depletion_date":  depletion_date,
           "current_balance": float(current_balance),
           "daily_burn":      float(daily_burn),
           "total_income":    features['total_income'],
           "total_expenses":  features['total_expenses'],
           "message":         message,
           "message_2":       message_2,
           "recommendation":  get_recommendation(status, runway_days)
       }

**Status thresholds:**

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Status
     - Runway
     - Meaning
   * - ``critical``
     - ≤ 7 days
     - Immediate action required
   * - ``warning``
     - ≤ 30 days
     - Budget plan needed
   * - ``caution``
     - ≤ 90 days
     - Monitor spending trends
   * - ``healthy``
     - > 90 days
     - Maintain current patterns
   * - ``sustainable``
     - N/A
     - No expenses — positive cash flow
   * - ``insufficient_data``
     - N/A
     - Empty transactions or zero/negative balance

-------------------

``get_recommendation(status, runway_days)``
-------------------------------------------

Returns a single-line action string based on the runway status.

.. code-block:: python

   def get_recommendation(status, runway_days):
       if status == "critical": return "Take immediate action: reduce expenses or increase income"
       elif status == "warning": return "Create a budget plan to extend runway"
       elif status == "caution": return "Monitor spending trends"
       else: return "Maintain current spending patterns"
