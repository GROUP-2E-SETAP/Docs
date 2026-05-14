Training 
===============================================

The model is trained in two steps — first the raw transaction data is processed
into training samples, then a ``RandomForestRegressor`` is fitted and saved.

---------------------

Data Preparation (``preparedata.py``)
--------------------------------------

Reads raw transaction data from ``train.csv``, which contains real transaction
records with columns ``date``, ``amount``, ``type``, and ``category``.

.. code-block:: text

   date,amount,type,category
   2026-01-01,1500,income,salary
   2026-01-02,50,expense,food
   ...

The script splits the data by calendar month, computes daily net cash flows
for each month, then generates training samples across nine starting balance
profiles for each month. Runway is calculated by simulating the balance day
by day until it hits zero.

.. code-block:: python

   def calculate_runway(daily_net_flows, starting_balance):
       balance = starting_balance
       for day_idx, net in enumerate(daily_net_flows):
           balance += net
           if balance <= 0:
               return day_idx
       return 999   # never depleted within the period

   for start_bal in [100, 300, 500, 800, 1200, 1500, 2000, 3000, 5000]:
       runway = calculate_runway(daily_flows, start_bal)
       training_data.append({
           'starting_balance': start_bal,
           'total_income':     income,
           'total_expenses':   expenses,
           'avg_daily_burn':   abs(daily_flows[daily_flows < 0].mean()),
           'transaction_count': len(daily_flows),
           'runway_days':      runway
       })

Output is saved to ``runway_training.csv``. A runway of ``999`` indicates
the balance was never depleted within the month window.

Run with:

.. code-block:: bash

   python preparedata.py

-------------------

Model Training (``training.py``)
----------------------------------

Reads ``runway_training.csv`` and trains a ``RandomForestRegressor`` to
predict ``runway_days`` from five input features.

.. code-block:: python

   X = df[['starting_balance', 'total_income', 'total_expenses', 'avg_daily_burn', 'transaction_count']]
   y = df['runway_days']

   X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

   model = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42)
   model.fit(X_train, y_train)

   with open('runway_model.pkl', 'wb') as f:
       pickle.dump(model, f)

Model performance is evaluated using R² score on the 20% test split and
printed to the console. The trained model is saved to ``runway_model.pkl``
and loaded automatically by ``predictor.py`` at service startup.

Run with:

.. code-block:: bash

   python training.py
