Frontend
========

The SFT frontend is built with **React Native**, targeting both web and mobile
platforms from a single codebase.  All pages share a global state layer provided
by ``FinanceContext`` and are styled with React Native ``StyleSheet`` objects.

----

Folder Structure
----------------

.. code-block:: text

    src/
    ├── context/
    │   └── FinanceContext.tsx      # Global state & API integration
    ├── services/
    │   └── financeApi.ts           # HTTP client for the backend API
    ├── Pages/
    │   ├── Budget/
    │   │   ├── Budget.tsx
    │   │   ├── BudgetComponents.tsx
    │   │   ├── BudgetHelpers.ts
    │   │   ├── Budget.styles.ts
    │   │   └── EditBudgetsModal.tsx
    │   ├── Dashboard/
    │   │   ├── Dashboard.tsx
    │   │   ├── Dashboardcomponents.tsx
    │   │   ├── Dashboardhelpers.ts
    │   │   └── DashBoard.styles.ts
    │   ├── AIAdvisor/
    │   │   ├── AIAdvisor.tsx
    │   │   └── AIAdvisorApi.ts
    │   └── Goals/
    │       ├── Goals.tsx
    │       ├── Goalscomponents.tsx
    │       ├── Goalshelpers.ts
    │       └── Goals.styles.ts
    └── Sidebar.tsx                 # Navigation / tab bar

----

.. toctree::
   :maxdepth: 2
   :caption: Frontend Pages

   budget_page
   goals_page
   dashboard_page
   ai_page
   transactions_page
