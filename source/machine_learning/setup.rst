Machine Learning Setup
======================

This guide walks you through setting up the Machine Learning service for local development.

Prerequisites
-------------

Make sure you have the following installed:

- Python 3.8 or higher
- pip (Python package installer)

--------------------------

Installation
------------

1. Clone the repository:

   .. code-block:: bash

      git clone git@github.com:GROUP-2E-SETAP/ML-Model.git

2. Navigate to the ML directory:

   .. code-block:: bash

      cd ML-Model

3. Create a virtual environment (recommended):

   .. code-block:: bash

      python -m venv venv
      source venv/bin/activate  # On Windows: venv\Scripts\activate

4. Install the required packages:

   .. code-block:: bash

      pip install -r requirements.txt

5. Set up environment variables by creating a ``.env`` file in the project root:

   .. code-block:: text

      EXPRESS_API_URL=http://localhost:3000/api/runway
      ML_URI=http://localhost:8000

6. Run the service:

   .. code-block:: bash

      uvicorn main:app --reload

--------------------------

Environment Variables
---------------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Variable
     - Description
   * - ``EXPRESS_API_URL``
     - URL of the Express backend callback endpoint. Defaults to ``http://localhost:3000/api/runway``
   * - ``ML_URI``
     - Used by the Node.js backend to reach this service. Set in the backend ``.env``
