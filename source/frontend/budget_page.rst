Budget Page
===========

Overview
--------

The **Budget Page** gives users a complete picture of their spending habits.
It combines three interactive visualisations — a donut chart, an area trend line,
and per-category health cards — together with an inline modal for editing
spending limits.

.. note::
   Budget limits are stored in the ``FinanceContext`` local state only.
   They are **not** persisted to the backend API between sessions.

----

File Structure
--------------

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - File
     - Purpose
   * - ``Budget.tsx``
     - Page entry point; assembles all sections and manages modal state
   * - ``BudgetComponents.tsx``
     - Reusable UI components (charts, cards, empty state)
   * - ``BudgetHelpers.ts``
     - Pure data-transformation utilities and shared type definitions
   * - ``Budget.styles.ts``
     - ``StyleSheet`` definitions for the entire Budget feature
   * - ``EditBudgetsModal.tsx``
     - Modal overlay for editing per-category spending limits

----

Data Flow
---------

The diagram below shows how data moves from the global context through to
the rendered UI:

.. code-block:: text

    FinanceContext
        │
        ├─ transactions[]   ──► aggregateExpensesByCategory()
        │                            │
        │                    ┌───────┴────────────────┐
        │                    │                        │
        │               buildPieData()          buildTrendData()
        │                    │                        │
        │             SpendingPieChart      SpendingTrendChart
        │
        └─ budgetLimits{}  ──► barData (useMemo)
                                    │
                              BudgetHealthCard[]
                                    │
                            EditBudgetsModal ──► updateBudgetLimit()

----

Main Component — ``Budget``
---------------------------

:File: ``src/Pages/Budget/Budget.tsx``

The root component of the Budget feature.  It consumes ``useFinance()`` to obtain
live transaction and budget-limit data, derives chart datasets through the helper
functions, and renders three ``SectionCard`` sections.

**State**

.. list-table::
   :header-rows: 1
   :widths: 25 20 55

   * - Variable
     - Type
     - Description
   * - ``isEditOpen``
     - ``boolean``
     - Controls visibility of the ``EditBudgetsModal`` overlay

**Context values consumed**

.. list-table::
   :header-rows: 1
   :widths: 30 25 45

   * - Value
     - Type
     - Description
   * - ``transactions``
     - ``Transaction[]``
     - All user transactions; filtered to expenses for chart data
   * - ``budgetLimits``
     - ``Record<string, number>``
     - Per-category spending limits
   * - ``updateBudgetLimit``
     - ``(category, limit) => void``
     - Mutates a single category's limit in context
   * - ``isLoading``
     - ``boolean``
     - Shown in the header subtitle while data is being fetched
   * - ``errorMessage``
     - ``string | null``
     - Displayed in the header subtitle if the API returns an error

**Derived data (computed on every render)**

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Variable
     - How it is produced
   * - ``expensesByCategory``
     - ``aggregateExpensesByCategory(transactions)``
   * - ``pieData``
     - ``buildPieData(expensesByCategory)``
   * - ``barData``
     - ``useMemo`` — maps ``budgetLimits`` keys to ``{ category, spent, limit, remaining }``
   * - ``trendData``
     - ``buildTrendData(transactions)``

**Implementation**

.. code-block:: typescript

   export function Budget() {
     const { transactions, budgetLimits, updateBudgetLimit,
             isLoading, errorMessage } = useFinance();
     const { width } = useWindowDimensions();
     const [isEditOpen, setIsEditOpen] = useState(false);

     const expensesByCategory = aggregateExpensesByCategory(transactions);
     const pieData            = buildPieData(expensesByCategory);
     const trendData          = buildTrendData(transactions);

     // Build per-category health data once; only recalculates when
     // expensesByCategory or budgetLimits change
     const barData = useMemo(
       () =>
         Object.keys(budgetLimits).map((category) => {
           const spent = expensesByCategory[category] || 0;
           const limit = budgetLimits[category] || 0;
           return { category, spent, limit, remaining: Math.max(0, limit - spent) };
         }),
       [expensesByCategory, budgetLimits]
     );

     return (
       <SafeAreaView style={styles.screen}>
         <ScrollView contentContainerStyle={styles.content}>
           {/* Header — shows loading / error state in subtitle */}
           <View style={styles.header}>
             <Text style={styles.headerTitle}>Budget & Analytics</Text>
             <Text style={styles.headerSubtitle}>
               {isLoading ? 'Loading…' : errorMessage || 'Track your spending'}
             </Text>
           </View>

           <SectionCard title="Spending Distribution" subtitle="Where your money goes">
             <SpendingPieChart pieData={pieData} />
           </SectionCard>

           <SectionCard title="Spending Trend" subtitle="Daily expenses over time">
             <SpendingTrendChart trendData={trendData} chartWidth={width} />
           </SectionCard>

           <SectionCard title="Budget Health Check">
             <Pressable onPress={() => setIsEditOpen(true)}>
               <Pencil size={16} color="#4f46e5" />
               <Text>Edit Budgets</Text>
             </Pressable>
             <View style={styles.healthGrid}>
               {barData.map((item) => (
                 <BudgetHealthCard key={item.category} item={item} />
               ))}
             </View>
           </SectionCard>

           <EditBudgetsModal
             isOpen={isEditOpen}
             onClose={() => setIsEditOpen(false)}
             budgetLimits={budgetLimits}
             updateBudgetLimit={updateBudgetLimit}
           />
         </ScrollView>
       </SafeAreaView>
     );
   }

----

UI Components — ``BudgetComponents.tsx``
-----------------------------------------

:File: ``src/Pages/Budget/BudgetComponents.tsx``

.. rubric:: SectionCard

A generic white card wrapper used to group each chart section.

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Prop
     - Type
     - Description
   * - ``title``
     - ``string``
     - Bold heading rendered at the top of the card
   * - ``subtitle``
     - ``string?``
     - Optional smaller text beneath the heading
   * - ``children``
     - ``ReactNode``
     - Card body content

**Implementation**

.. code-block:: typescript

   export function SectionCard({ title, subtitle, children }: {
     title: string;
     subtitle?: string;
     children: React.ReactNode;
   }) {
     return (
       <View style={styles.card}>
         <Text style={styles.cardTitle}>{title}</Text>
         {subtitle ? <Text style={styles.cardSubtitle}>{subtitle}</Text> : null}
         {children}
       </View>
     );
   }

----

.. rubric:: SpendingPieChart

Donut chart showing each category's share of total spending, with a colour legend.

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Prop
     - Type
     - Description
   * - ``pieData``
     - ``PieDataItem[]``
     - Array of slices; each item carries ``value``, ``color``, ``text``, ``label``

.. note::
   Renders ``EmptyState`` when ``pieData`` is an empty array (no expense transactions yet).

**Chart configuration**

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Option
     - Value
   * - Chart type
     - Donut (``donut`` prop)
   * - Inner radius
     - 70 px
   * - Outer radius
     - 110 px
   * - Labels
     - Values shown on each slice (``showValuesAsLabels``)
   * - Legend
     - Color-dot legend rendered below the chart

**Implementation**

.. code-block:: typescript

   export function SpendingPieChart({ pieData }: { pieData: PieDataItem[] }) {
     if (pieData.length === 0) {
       return <EmptyState message="No expense data available" />;
     }
     return (
       <View style={styles.pieContainer}>
         <PieChart
           data={pieData}
           donut
           innerRadius={70}
           radius={110}
           textColor="#fff"
           textSize={11}
           showText
           showValuesAsLabels
         />
         {/* Color legend beneath the chart */}
         <View style={styles.legendContainer}>
           {pieData.map((item) => (
             <View key={item.label} style={styles.legendItem}>
               <View style={[styles.legendDot, { backgroundColor: item.color }]} />
               <Text style={styles.legendText}>{item.label}</Text>
             </View>
           ))}
         </View>
       </View>
     );
   }

----

.. rubric:: SpendingTrendChart

Animated area line chart showing daily expense totals for the past seven days.

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Prop
     - Type
     - Description
   * - ``trendData``
     - ``TrendDataItem[]``
     - Array of ``{ value, label }`` points, one per day
   * - ``chartWidth``
     - ``number``
     - Current screen width, used to fill the card horizontally

.. note::
   Renders ``EmptyState`` when ``trendData`` is empty.

**Chart configuration**

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Option
     - Value
   * - Chart type
     - Area line chart (``areaChart`` prop)
   * - Line colour
     - ``#6366f1`` (indigo)
   * - Fill gradient
     - Indigo (25 % opacity) → transparent
   * - Curve style
     - Smooth (``curved`` prop)
   * - Animated
     - Yes (``isAnimated`` prop)
   * - Axis lines
     - Hidden (thickness set to 0)

**Implementation**

.. code-block:: typescript

   export function SpendingTrendChart({
     trendData,
     chartWidth,
   }: {
     trendData: TrendDataItem[];
     chartWidth: number;
   }) {
     if (trendData.length === 0) {
       return <EmptyState message="Not enough data to show trends yet" />;
     }
     return (
       <View style={styles.chartWrapper}>
         <LineChart
           data={trendData}
           width={chartWidth - 64}   // subtract card padding
           height={200}
           color="#6366f1"
           thickness={3}
           startFillColor="#6366f1"
           endFillColor="transparent"
           startOpacity={0.25}
           endOpacity={0}
           areaChart
           isAnimated
           dataPointsColor="#6366f1"
           dataPointsRadius={5}
           noOfSections={4}
           xAxisThickness={0}
           yAxisThickness={0}
           curved
         />
       </View>
     );
   }

----

.. rubric:: BudgetHealthCard

One card per budget category showing spent vs limit, a progress bar, and an
on-track / over-budget badge.

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Prop
     - Type
     - Description
   * - ``item``
     - ``BarDataItem``
     - Object with ``category``, ``spent``, ``limit``, ``remaining``

**Visual behaviour**

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Condition
     - Appearance
   * - ``spent <= limit``
     - Progress bar is **indigo**; badge reads "On Track" (green tint)
   * - ``spent > limit``
     - Progress bar is **red**; badge reads "Over Budget" (red tint)
   * - Any value
     - Bar width is capped at 100 % even when limit is exceeded

**Implementation**

.. code-block:: typescript

   export function BudgetHealthCard({ item }: { item: BarDataItem }) {
     // Cap at 100 % visually even if spending exceeded the limit
     const percentage = Math.min(100, (item.spent / item.limit) * 100);
     const isOver     = item.spent > item.limit;

     const progressStyle: ViewStyle = {
       width: `${percentage}%` as `${number}%`,
       backgroundColor: isOver ? '#ef4444' : '#6366f1',
       height: '100%',
       borderRadius: 99,
     };

     return (
       <View style={styles.healthCard}>
         <View style={styles.healthCardHeader}>
           <Text style={styles.healthCardCategory}>{item.category}</Text>
           <View style={[styles.statusBadge,
             isOver ? styles.statusBadgeOver : styles.statusBadgeOk]}>
             <Text style={[styles.statusBadgeText,
               isOver ? styles.statusTextOver : styles.statusTextOk]}>
               {isOver ? 'Over Budget' : 'On Track'}
             </Text>
           </View>
         </View>
         <View style={styles.healthCardAmounts}>
           <Text>£{item.spent.toLocaleString()} spent</Text>
           <Text>of £{item.limit.toLocaleString()}</Text>
         </View>
         <View style={styles.progressTrack}>
           <View style={progressStyle} />
         </View>
         <Text style={styles.percentageText}>{percentage.toFixed(0)}% used</Text>
       </View>
     );
   }

----

.. rubric:: EmptyState

Shared placeholder displayed inside a chart section when there is no data.

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Prop
     - Type
     - Description
   * - ``message``
     - ``string``
     - Human-readable explanation shown to the user

**Implementation**

.. code-block:: typescript

   export function EmptyState({ message }: { message: string }) {
     return (
       <View style={styles.emptyState}>
         <Text style={styles.emptyStateText}>{message}</Text>
       </View>
     );
   }

----

Edit Budgets Modal — ``EditBudgetsModal``
-----------------------------------------

:File: ``src/Pages/Budget/EditBudgetsModal.tsx``

A full-screen transparent modal that allows users to update the spending limit
for each budget category.  It maintains a local ``draft`` copy of all limit
values so that dismissed edits are never persisted.

.. warning::
   Changes are saved to ``FinanceContext`` in-memory only.
   Closing and re-opening the app will reset limits to their API-fetched defaults.

**Props**

.. list-table::
   :header-rows: 1
   :widths: 25 35 40

   * - Prop
     - Type
     - Description
   * - ``isOpen``
     - ``boolean``
     - Mounts and displays the modal when ``true``
   * - ``onClose``
     - ``() => void``
     - Called by the X button, backdrop tap, and Save action
   * - ``budgetLimits``
     - ``Record<string, number>``
     - Current limits — used to pre-populate inputs when the modal opens
   * - ``updateBudgetLimit``
     - ``(category: Category, limit: number) => void``
     - Context mutation called once per category on save

**Internal state**

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Variable
     - Type
     - Description
   * - ``draft``
     - ``Record<string, string>``
     - String copy of limits for controlled ``TextInput`` components

**Helper — ``toNumberOrZero``**

Strips non-numeric characters from a string and converts it to a number.
Returns ``0`` for blank or non-numeric input.

.. code-block:: typescript

   const toNumberOrZero = (value: string) => {
     const cleaned = value.replace(/[^\d.]/g, '');
     const n = Number(cleaned);
     return Number.isFinite(n) ? n : 0;
   };

   // Examples
   toNumberOrZero('£ 150.00')  // → 150
   toNumberOrZero('')           // → 0
   toNumberOrZero('abc')        // → 0

**Draft initialisation — ``useEffect``**

Runs whenever the modal opens, copying the current ``budgetLimits`` into
the local ``draft`` state so each ``TextInput`` is pre-populated:

.. code-block:: typescript

   useEffect(() => {
     if (!isOpen) return;
     const next: Record<string, string> = {};
     for (const key of categories) next[key] = String(budgetLimits[key] ?? 0);
     setDraft(next);
   }, [isOpen, categories, budgetLimits]);

**Save handler — ``handleSave``**

Iterates over every category, converts the draft string back to a number,
then calls ``updateBudgetLimit`` before closing the modal:

.. code-block:: typescript

   const handleSave = () => {
     for (const key of categories) {
       updateBudgetLimit(key as Category, toNumberOrZero(draft[key] ?? '0'));
     }
     onClose();
   };

**Interaction flow**

1. Modal opens → ``useEffect`` copies ``budgetLimits`` into ``draft`` state.
2. User edits a ``TextInput`` → ``draft`` is updated with the raw string value.
3. User taps **Save Limits** → ``handleSave`` converts and persists all values, then closes.
4. User taps **X** or the backdrop → modal closes; ``draft`` changes are discarded.

----

Helper Functions — ``BudgetHelpers.ts``
----------------------------------------

:File: ``src/Pages/Budget/BudgetHelpers.ts``

All functions in this module are **pure** — they take data as arguments and
return new values without side effects.

.. rubric:: aggregateExpensesByCategory

.. code-block:: typescript

   export function aggregateExpensesByCategory(
     transactions: Transaction[]
   ): Record<string, number> {
     return transactions
       .filter((t) => t.type === 'expense')
       .reduce<Record<string, number>>((acc, curr) => {
         acc[curr.category] = (acc[curr.category] || 0) + curr.amount;
         return acc;
       }, {});
   }

Filters the full transaction list to ``type === 'expense'`` entries and sums
amounts per category.

**Example output**

.. code-block:: typescript

   { Food: 320, Housing: 900, Transport: 145 }

----

.. rubric:: buildPieData

.. code-block:: typescript

   export function buildPieData(
     expensesByCategory: Record<string, number>
   ): PieDataItem[] {
     return Object.keys(expensesByCategory).map((key, index) => ({
       value: expensesByCategory[key],
       color: COLORS[index % COLORS.length],   // cycle through palette
       text: key,
       label: key,
     }));
   }

Converts the category-totals dictionary into the array format expected by
``react-native-gifted-charts`` ``PieChart``.  Colors are assigned by cycling
through the ``COLORS`` palette.

----

.. rubric:: buildTrendData

.. code-block:: typescript

   export function buildTrendData(transactions: Transaction[]): TrendDataItem[] {
     const spendingByDate = transactions
       .filter((t) => t.type === 'expense')
       .reduce<Record<string, number>>((acc, curr) => {
         acc[curr.date] = (acc[curr.date] || 0) + curr.amount;
         return acc;
       }, {});

     return Object.keys(spendingByDate)
       .sort()
       .slice(-7)                              // keep last 7 days only
       .map((date) => ({
         value: spendingByDate[date],
         label: new Date(date).toLocaleDateString('en-US', {
           month: 'short',
           day: 'numeric',
         }),
       }));
   }

Groups expense transactions by ``date``, sorts chronologically, and returns
only the **last 7 days** as ``{ value, label }`` pairs.  Labels are formatted
as ``"May 1"`` for x-axis display.

----

.. rubric:: COLORS palette

.. code-block:: typescript

   export const COLORS: string[] = [
     '#6366f1', '#ec4899', '#14b8a6', '#f59e0b',
     '#8b5cf6', '#ef4444', '#3b82f6', '#10b981',
   ];

Eight distinct colors cycled across pie slices in the order listed above.

----

Type Definitions
----------------

:File: ``src/Pages/Budget/BudgetHelpers.ts``

.. rubric:: PieDataItem

.. code-block:: typescript

   export interface PieDataItem {
     value:  number;   // total spending for the category
     color:  string;   // hex color assigned to the slice
     text:   string;   // label drawn on the slice
     label:  string;   // category name used in the legend
   }

----

.. rubric:: BarDataItem

.. code-block:: typescript

   export interface BarDataItem {
     category:  string;   // e.g. "Food"
     spent:     number;   // total amount spent
     limit:     number;   // user-defined spending limit
     remaining: number;   // Math.max(0, limit - spent)
   }

----

.. rubric:: TrendDataItem

.. code-block:: typescript

   export interface TrendDataItem {
     value: number;   // total daily spending
     label: string;   // formatted x-axis label, e.g. "May 1"
   }

----

Dependencies
------------

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Package
     - Used for
   * - ``react-native-gifted-charts``
     - ``PieChart`` and ``LineChart`` chart components
   * - ``lucide-react-native``
     - ``Pencil`` icon on the Edit Budgets button
   * - ``FinanceContext`` (internal)
     - Shared transactions and budget-limit state

----

.. seealso::

   - :doc:`goals_page` — Savings goals feature built with the same context layer
   - ``src/context/FinanceContext.tsx`` — Global state provider and API client
