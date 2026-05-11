AI Advisor Page
===============

Overview
--------

The **AI Advisor Page** provides two finance-assistance tools in one screen:

* **Price Comparison** searches for estimated product prices in a chosen
  location using the OpenAI Responses API.
* **Financial Insights** analyses the user's tracked income, expenses, balance,
  categories, and savings goals to generate practical recommendations.

.. warning::
   ``AIAdvisorApi.ts`` reads ``EXPO_PUBLIC_OPENAI_API_KEY`` from the Expo
   environment, but falls back to ``sk-mock-openai-key`` when no key is set.
   Real API calls require a valid key and model configuration.

----

File Structure
--------------

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - File
     - Purpose
   * - ``AIAdvisor.tsx``
     - Full page implementation, tab state, price form, insights calculations, fallback recommendations, and styles
   * - ``AIAdvisorApi.ts``
     - OpenAI API client, response parsing, price comparison request, and financial advice request
   * - ``app/ai-advisor.tsx``
     - Expo Router route that renders ``AIAdvisor``
   * - ``FinanceContext.tsx``
     - Supplies transactions, balances, goals, loading state, and errors

----

Data Flow
---------

.. code-block:: text

    FinanceContext
        |
        |- transactions[], monthlyIncome, monthlyExpenses, totalBalance, goals
        |       |
        |       +--> local insight calculations
        |              |
        |              |- insights[] cards
        |              |- watchlist panel
        |              +--> buildRecommendations() fallback
        |
        +--> useEffect()
                |
                +--> getFinancialAdvice()
                       |
                       +--> OpenAI Responses API
                       |
                       +--> aiRecommendations[]

    Product + Location form
        |
        +--> handleFindPrices()
                |
                +--> getPriceComparison()
                       |
                       +--> OpenAI Responses API
                       |
                       +--> sorted PriceQuote[]
                               |
                               +--> Price Results list

----

Main Component - ``AIAdvisor``
------------------------------

:File: ``src/Pages/AIAdvisor/AIAdvisor.tsx``

The root component of the AI feature.  It owns the tab switcher, validates the
price-search form, derives local finance insight metrics, calls the OpenAI
helper functions, and renders both the price-results and insights views.

**Context values consumed**

.. list-table::
   :header-rows: 1
   :widths: 30 25 45

   * - Value
     - Type
     - Description
   * - ``transactions``
     - ``Transaction[]``
     - Source data for spending totals, category concentration, and AI advice
   * - ``monthlyIncome``
     - ``number``
     - Used for surplus and savings-rate calculations
   * - ``monthlyExpenses``
     - ``number``
     - Used for surplus and overspending checks
   * - ``totalBalance``
     - ``number``
     - Shown as an insight card and sent to OpenAI
   * - ``goals``
     - ``Goal[]``
     - Used to calculate open goal gap, next goal, and goal runway
   * - ``isLoading``
     - ``boolean``
     - Prevents advice loading while finance data is still loading
   * - ``errorMessage``
     - ``string``
     - Displayed in the insights panel if finance data fails to load

**Local state**

.. list-table::
   :header-rows: 1
   :widths: 30 25 45

   * - Variable
     - Type
     - Description
   * - ``activeTab``
     - ``'prices' | 'insights'``
     - Controls which advisor view is visible
   * - ``product``
     - ``string``
     - Controlled input for the searched product
   * - ``location``
     - ``string``
     - Controlled input for city, zip code, or postcode
   * - ``attemptedSubmit``
     - ``boolean``
     - Enables validation messaging after the first submit attempt
   * - ``showLocationSuggestions``
     - ``boolean``
     - Shows or hides the location suggestion dropdown
   * - ``isLoading``
     - ``boolean``
     - Loading state for price comparison requests
   * - ``errorMessage``
     - ``string``
     - Price-search validation or API error message
   * - ``quotes``
     - ``PriceQuote[]``
     - Sorted price results returned by OpenAI
   * - ``lastSearch``
     - ``{ product, location } | null``
     - Used to label the current price-results list
   * - ``aiRecommendations``
     - ``string[]``
     - Recommendations returned by OpenAI
   * - ``isInsightsLoading``
     - ``boolean``
     - Loading state for financial advice requests
   * - ``insightsErrorMessage``
     - ``string``
     - Error message from the OpenAI advice request

**Validation constants**

.. code-block:: typescript

   const MIN_PRODUCT_LENGTH = 3;
   const MIN_LOCATION_LENGTH = 3;

   const isProductValid = trimmedProduct.length >= MIN_PRODUCT_LENGTH;
   const isLocationValid = trimmedLocation.length >= MIN_LOCATION_LENGTH;
   const canFindPrices = isProductValid && isLocationValid;

Both product and location must contain at least three trimmed characters before
``handleFindPrices`` will call the API.

----

Price Comparison Flow
---------------------

The **Price Comparison** tab contains a product input, location input,
autocomplete suggestions, submit button, validation messages, and a result
list.

**Location suggestions**

``LOCATION_OPTIONS`` contains UK cities, US cities, and sample postcode/zip
entries.  The component filters this list using the current location query:

.. code-block:: typescript

   const filteredLocations = LOCATION_OPTIONS
     .filter((entry) => entry.toLowerCase().includes(locationQuery))
     .slice(0, 6);

Only the first six matching suggestions are shown.

**Submit handler - ``handleFindPrices``**

.. code-block:: typescript

   const handleFindPrices = async () => {
     setAttemptedSubmit(true);

     if (!canFindPrices) {
       if (!isProductFilled || !isLocationFilled) {
         setErrorMessage('Please enter both a product and a location.');
       } else {
         setErrorMessage(
           `Please enter at least ${MIN_PRODUCT_LENGTH} characters for product and ${MIN_LOCATION_LENGTH} for location.`,
         );
       }
       setQuotes([]);
       setLastSearch(null);
       return;
     }

     setIsLoading(true);
     setErrorMessage('');
     setShowLocationSuggestions(false);

     try {
       const result = await getPriceComparison({
         product: trimmedProduct,
         location: trimmedLocation,
       });
       setQuotes(result);
       setLastSearch({ product: trimmedProduct, location: trimmedLocation });
     } catch (error) {
       setQuotes([]);
       setErrorMessage(
         error instanceof Error
           ? error.message
           : 'Unable to fetch price comparisons right now.',
       );
     } finally {
       setIsLoading(false);
     }
   };

**Result states**

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Condition
     - Output
   * - ``isLoading``
     - Spinner with *"Searching stores..."*
   * - ``errorMessage``
     - Error text in the results section
   * - ``quotes.length > 0``
     - Result cards with store, price, stock status, delivery estimate, and optional deal link
   * - ``index === 0``
     - First quote receives the **Best Price** badge because results are sorted by price

----

Financial Insights Flow
-----------------------

The **Financial Insights** tab combines local deterministic calculations with
AI-generated recommendations.

**Derived finance values**

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Variable
     - Calculation
   * - ``expenseTransactions``
     - ``transactions.filter((transaction) => transaction.type === 'expense')``
   * - ``totalSpent``
     - Sum of all expense transaction amounts
   * - ``estimatedMonthlySurplus``
     - ``Math.max(0, monthlyIncome - monthlyExpenses)``
   * - ``savingsRate``
     - ``((monthlyIncome - monthlyExpenses) / monthlyIncome) * 100`` when income exists
   * - ``categorySpend``
     - Expense totals grouped by category
   * - ``topCategory``
     - Highest-spend category, defaulting to ``'Other'``
   * - ``activeGoals``
     - Goals where ``currentAmount < targetAmount``
   * - ``nearestGoal``
     - Active goal with the earliest deadline
   * - ``totalGoalGap``
     - Sum of remaining amount across active goals
   * - ``goalRunwayMonths``
     - ``Math.ceil(totalGoalGap / estimatedMonthlySurplus)`` when surplus is positive

**Insight cards**

.. list-table::
   :header-rows: 1
   :widths: 30 35 35

   * - Card
     - Metric
     - Tone logic
   * - Savings posture
     - ``savingsRate``
     - Positive at ``>= 20%``, neutral at ``>= 10%``, otherwise warning
   * - Highest spend category
     - ``topCategorySpend``
     - Warning when the top category is more than 35% of tracked spending
   * - Goal runway
     - ``goalRunwayMonths``
     - Positive when open goals can be covered in 3 months or less
   * - Available balance
     - ``totalBalance``
     - Positive when balance is non-negative, warning when negative

**OpenAI recommendation effect**

.. code-block:: typescript

   useEffect(() => {
     let isCancelled = false;

     const loadAdvice = async () => {
       if (isFinanceLoading || transactions.length === 0) {
         setAiRecommendations([]);
         return;
       }

       setIsInsightsLoading(true);
       setInsightsErrorMessage('');

       try {
         const recommendations = await getFinancialAdvice({
           monthlyIncome,
           monthlyExpenses,
           totalBalance,
           transactions,
           goals,
         });

         if (!isCancelled) {
           setAiRecommendations(recommendations);
         }
       } catch (error) {
         if (!isCancelled) {
           setAiRecommendations([]);
           setInsightsErrorMessage(
             error instanceof Error ? error.message : 'Unable to load AI recommendations.',
           );
         }
       } finally {
         if (!isCancelled) {
           setIsInsightsLoading(false);
         }
       }
     };

     void loadAdvice();

     return () => {
       isCancelled = true;
     };
   }, [goals, isFinanceLoading, monthlyExpenses, monthlyIncome, totalBalance, transactions]);

The ``isCancelled`` flag prevents state updates after the component unmounts or
the dependency set changes before the async request finishes.

----

Fallback Recommendations - ``buildRecommendations``
---------------------------------------------------

When OpenAI does not return recommendations, the page still displays local
guidance from ``buildRecommendations``.

.. rubric:: Input context

.. code-block:: typescript

   interface RecommendationContext {
     monthlyIncome: number;
     monthlyExpenses: number;
     savingsRate: number;
     topCategory: string;
     topCategorySpend: number;
     totalSpent: number;
     nearestGoalName?: string;
     estimatedMonthlySurplus: number;
     goalRunwayMonths: number | null;
     totalGoalGap: number;
   }

.. rubric:: Rule summary

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Condition
     - Recommendation
   * - ``monthlyIncome <= 0``
     - Add income so the advisor can calculate savings rate and funding pace
   * - ``totalSpent <= 0``
     - Track expenses to unlock category guidance
   * - ``topCategorySpend / totalSpent > 0.35``
     - Review the largest expense category first
   * - ``savingsRate < 10``
     - Trim flexible expenses before fixed expenses
   * - ``savingsRate >= 20``
     - Automate some surplus into goals or emergency savings
   * - Open goal gap with surplus
     - Estimate months required to cover the gap
   * - Open goal gap without surplus
     - Warn that no monthly surplus is available for the goal
   * - ``monthlyExpenses > monthlyIncome``
     - Freeze discretionary purchases until balance improves

The function returns at most four recommendations:

.. code-block:: typescript

   return items.slice(0, 4);

----

OpenAI API Client - ``AIAdvisorApi.ts``
---------------------------------------

:File: ``src/Pages/AIAdvisor/AIAdvisorApi.ts``

This module isolates all OpenAI calls from the React component.

**Configuration**

.. code-block:: typescript

   const OPENAI_API_URL = 'https://api.openai.com/v1/responses';
   const OPENAI_MODEL = process.env.EXPO_PUBLIC_OPENAI_MODEL?.trim() || 'gpt-4.1';
   const OPENAI_API_KEY =
     process.env.EXPO_PUBLIC_OPENAI_API_KEY?.trim() || 'sk-mock-openai-key';

**Shared request helper**

.. code-block:: typescript

   async function createOpenAIResponse(
     instructions: string,
     input: string,
   ): Promise<string> {
     const response = await fetch(OPENAI_API_URL, {
       method: 'POST',
       headers: {
         'Content-Type': 'application/json',
         Authorization: `Bearer ${OPENAI_API_KEY}`,
       },
       body: JSON.stringify({
         model: OPENAI_MODEL,
         instructions,
         input,
       }),
     });

     if (!response.ok) {
       throw new Error(`OpenAI request failed (${response.status})`);
     }

     const payload = (await response.json()) as OpenAIResponsePayload;
     if (!payload.output_text) {
       throw new Error('OpenAI response was empty.');
     }

     return payload.output_text;
   }

----

.. rubric:: extractJsonBlock

.. code-block:: typescript

   function extractJsonBlock<T>(value: string): T {
     const start = value.indexOf('{');
     const end = value.lastIndexOf('}');

     if (start < 0 || end < 0 || end <= start) {
       throw new Error('OpenAI response did not include JSON output.');
     }

     return JSON.parse(value.slice(start, end + 1)) as T;
   }

Extracts and parses the first JSON object found in the returned text.  This
keeps the API helpers defensive even if the model returns extra text around the
JSON object.

----

.. rubric:: getPriceComparison

.. code-block:: typescript

   export async function getPriceComparison({
     product,
     location,
   }: PriceComparisonRequest): Promise<PriceQuote[]> {
     const output = await createOpenAIResponse(
       [
         'You generate price comparison data.',
         'Return only JSON with the shape {"quotes":[{"store":"","price":0,"currency":"GBP","eta":"","inStock":true,"url":""}]}',
         'Provide between 3 and 5 quotes.',
         'Use GBP currency values.',
       ].join(' '),
       `Find price comparison estimates for "${product}" in "${location}".`,
     );

     const parsed = extractJsonBlock<{ quotes?: PriceQuote[] }>(output);
     const quotes = Array.isArray(parsed.quotes) ? parsed.quotes : [];

     if (quotes.length === 0) {
       throw new Error('No price quotes were returned by OpenAI.');
     }

     return quotes
       .map((quote) => ({
         ...quote,
         currency: quote.currency || 'GBP',
         price: Number(quote.price ?? 0),
       }))
       .sort((left, right) => left.price - right.price);
   }

The returned quotes are normalized so every result has a currency and numeric
price, then sorted cheapest-first.

----

.. rubric:: getFinancialAdvice

.. code-block:: typescript

   export async function getFinancialAdvice(
     payload: FinancialAdviceRequest,
   ): Promise<string[]> {
     const output = await createOpenAIResponse(
       [
         'You are a concise personal finance assistant.',
         'Return only JSON with the shape {"recommendations":["", "", ""]}.',
         'Provide between 3 and 4 actionable recommendations.',
         'Base them strictly on the supplied finance data.',
       ].join(' '),
       JSON.stringify(payload),
     );

     const parsed = extractJsonBlock<{ recommendations?: string[] }>(output);
     const recommendations = Array.isArray(parsed.recommendations)
       ? parsed.recommendations.filter(Boolean)
       : [];

     if (recommendations.length === 0) {
       throw new Error('No financial advice was returned by OpenAI.');
     }

     return recommendations.slice(0, 4);
   }

Returns three to four concise recommendations based strictly on the supplied
finance context.

----

Type Definitions
----------------

:File: ``src/Pages/AIAdvisor/AIAdvisorApi.ts``

.. rubric:: PriceComparisonRequest

.. code-block:: typescript

   export interface PriceComparisonRequest {
     product: string;
     location: string;
   }

----

.. rubric:: PriceQuote

.. code-block:: typescript

   export interface PriceQuote {
     store: string;
     price: number;
     currency: string;
     eta?: string;
     inStock?: boolean;
     url?: string;
   }

----

.. rubric:: FinancialAdviceRequest

.. code-block:: typescript

   export interface FinancialAdviceRequest {
     monthlyIncome: number;
     monthlyExpenses: number;
     totalBalance: number;
     transactions: Transaction[];
     goals: Goal[];
   }

----

Formatting Helpers
------------------

:File: ``src/Pages/AIAdvisor/AIAdvisor.tsx``

.. rubric:: formatCurrency

.. code-block:: typescript

   function formatCurrency(value: number): string {
     return new Intl.NumberFormat('en-GB', {
       style: 'currency',
       currency: 'GBP',
       maximumFractionDigits: 0,
     }).format(value);
   }

Formats insight values as British pounds.

.. code-block:: typescript

   formatCurrency(1500)   // -> "GBP 1,500" depending on platform locale support

----

.. rubric:: formatDeadline

.. code-block:: typescript

   function formatDeadline(value: string): string {
     const date = new Date(value);
     return Number.isNaN(date.getTime())
       ? value
       : new Intl.DateTimeFormat('en-GB', {
           day: 'numeric',
           month: 'short',
           year: 'numeric',
         }).format(date);
   }

Returns the original value if it cannot be parsed as a valid date.

----

Dependencies
------------

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Package
     - Used for
   * - ``expo-linear-gradient``
     - Gradient hero cards for both advisor tabs
   * - ``lucide-react-native``
     - Icons for search, location, insights, watchlist, goals, and savings metrics
   * - ``react-native``
     - Inputs, tabs, loading indicators, linking, layout, and scroll views
   * - ``OpenAI Responses API``
     - Price quotes and finance recommendations through ``AIAdvisorApi.ts``
   * - ``FinanceContext`` (internal)
     - Shared transactions, balances, goals, loading state, and errors

----

.. seealso::

   - :doc:`dashboard_page` - Main finance summary that shares the same context values
   - :doc:`budget_page` - Category spending analytics also derived from transactions
   - :doc:`goals_page` - Goal data used by the AI insight calculations
   - ``src/Pages/AIAdvisor/AIAdvisorApi.ts`` - OpenAI API integration layer
