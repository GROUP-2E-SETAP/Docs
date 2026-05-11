Goals Page
==========

Overview
--------

The **Goals Page** lets users create and track personal savings goals.
Each goal has a name, a target amount, and a deadline.  Users can add money
to a goal using quick-add buttons (``+£10``, ``+£50``, ``+£100``) and watch
their progress bar fill up as they save.

.. note::
   Goals are stored in ``FinanceContext`` local state only and are **not**
   persisted to the backend API.  Refreshing the app will reset all goals.

----

File Structure
--------------

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - File
     - Purpose
   * - ``Goals.tsx``
     - Page entry point; manages form state and renders the goal grid
   * - ``Goalscomponents.tsx``
     - Reusable UI components (``GoalCard``, ``AddGoalForm``, ``AddGoalButton``)
   * - ``Goalshelpers.ts``
     - Pure utility functions for progress calculation, color, and formatting
   * - ``Goals.styles.ts``
     - ``StyleSheet`` definitions for the entire Goals feature

----

Data Flow
---------

.. code-block:: text

    FinanceContext
        │
        ├─ goals[]          ──► GoalCard[] (grid)
        │                            │
        │                    onUpdateAmount()
        │                            │
        │                    updateGoalAmount() ──► context state update
        │                                               │
        │                                       gamification refresh
        │                                       toast on completion
        │
        ├─ addGoal()         ◄── handleAddGoal() (form submit)
        │
        └─ updateGoalAmount() ◄── GoalCard quick-add buttons

----

Main Component — ``Goals``
--------------------------

:File: ``src/Pages/Goals/Goals.tsx``

The root component of the Goals feature.  It reads the ``goals`` array and
mutation helpers from ``useFinance()``, computes a summary banner total, and
conditionally renders either an inline add form or a grid of ``GoalCard``
components.

**Context values consumed**

.. list-table::
   :header-rows: 1
   :widths: 25 30 45

   * - Value
     - Type
     - Description
   * - ``goals``
     - ``Goal[]``
     - Array of all user-created goals
   * - ``addGoal``
     - ``(goal: Omit<Goal,'id'>) => void``
     - Creates a new goal; ``id`` is assigned automatically by the context
   * - ``updateGoalAmount``
     - ``(id: string, newAmount: number) => void``
     - Updates ``currentAmount`` for a goal; triggers XP toast on completion

**Local state**

.. list-table::
   :header-rows: 1
   :widths: 25 20 55

   * - Variable
     - Type
     - Description
   * - ``isAdding``
     - ``boolean``
     - Toggles the inline ``AddGoalForm`` panel
   * - ``newGoalName``
     - ``string``
     - Controlled input value for the new goal's name
   * - ``newGoalTarget``
     - ``string``
     - Controlled input value for the new goal's target amount

**Computed values**

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Variable
     - Calculation
   * - ``totalSaved``
     - ``goals.reduce((sum, g) => sum + g.currentAmount, 0)``
   * - ``totalTarget``
     - ``goals.reduce((sum, g) => sum + g.targetAmount, 0)``

These values populate the **Total Progress** summary banner at the top of the page.

**Implementation**

.. code-block:: typescript

   export function Goals() {
     const { goals, addGoal, updateGoalAmount } = useFinance();

     const [isAdding, setIsAdding]         = useState(false);
     const [newGoalName, setNewGoalName]   = useState('');
     const [newGoalTarget, setNewGoalTarget] = useState('');

     // Running totals for the summary banner
     const totalSaved  = goals.reduce((sum, g) => sum + g.currentAmount, 0);
     const totalTarget = goals.reduce((sum, g) => sum + g.targetAmount, 0);

     return (
       <SafeAreaView style={{ flex: 1, backgroundColor: '#f9fafb' }}>
         <ScrollView contentContainerStyle={styles.container}>
           <View style={styles.header}>
             <Text style={styles.title}>Savings Goals</Text>
             <AddGoalButton onClick={() => setIsAdding((v) => !v)} />
           </View>

           <View style={styles.summary}>
             <Text style={styles.summaryTitle}>Total Progress</Text>
             <Text style={styles.summaryValue}>
               £{totalSaved.toLocaleString()} / £{totalTarget.toLocaleString()}
             </Text>
           </View>

           {isAdding && (
             <AddGoalForm
               newGoalName={newGoalName}
               newGoalTarget={newGoalTarget}
               onNameChange={setNewGoalName}
               onTargetChange={setNewGoalTarget}
               onSubmit={handleAddGoal}
               onCancel={() => setIsAdding(false)}
             />
           )}

           {goals.length === 0 ? (
             <View style={styles.emptyState}>
               <Text style={styles.emptyTitle}>No Goals Yet</Text>
               <Text style={styles.emptyText}>
                 Start by creating your first savings goal.
               </Text>
             </View>
           ) : (
             <View style={styles.grid}>
               {goals.map((goal) => (
                 <GoalCard
                   key={goal.id}
                   goal={goal}
                   onUpdateAmount={updateGoalAmount}
                 />
               ))}
             </View>
           )}
         </ScrollView>
       </SafeAreaView>
     );
   }

**handleAddGoal**

Validates that both fields are non-empty before creating the goal, then resets
the form:

.. code-block:: typescript

   const handleAddGoal = () => {
     // Both fields are required before creating the goal
     if (!newGoalName || !newGoalTarget) return;

     addGoal({
       name: newGoalName,
       targetAmount: Number(newGoalTarget),
       currentAmount: 0,
       deadline: defaultDeadline(),   // 90 days from today
     });

     // Clear inputs and collapse the form
     setNewGoalName('');
     setNewGoalTarget('');
     setIsAdding(false);
   };

----

UI Components — ``Goalscomponents.tsx``
----------------------------------------

:File: ``src/Pages/Goals/Goalscomponents.tsx``

.. rubric:: GoalCard

Displays a single savings goal with its current progress and quick-add buttons.

**Props**

.. list-table::
   :header-rows: 1
   :widths: 25 30 45

   * - Prop
     - Type
     - Description
   * - ``goal``
     - ``Goal``
     - The goal object from ``FinanceContext``
   * - ``onUpdateAmount``
     - ``(id: string, newAmount: number) => void``
     - Called by the quick-add buttons with the new total amount

**Implementation**

.. code-block:: typescript

   export function GoalCard({ goal, onUpdateAmount }: GoalCardProps) {
     const progress = calcProgress(goal.currentAmount, goal.targetAmount);

     return (
       <View style={styles.card}>
         {/* Header: icon + name + target on the left, amount + % on the right */}
         <View style={styles.cardHeader}>
           <View style={styles.cardLeft}>
             <View style={styles.iconWrapper}>
               <Target size={20} color="#4f46e5" />
             </View>
             <View>
               <Text style={styles.goalName}>{goal.name}</Text>
               <Text style={styles.goalTarget}>
                 Target: {formatCurrency(goal.targetAmount)}
               </Text>
             </View>
           </View>
           <View style={styles.cardRight}>
             <Text style={styles.currentAmount}>
               {formatCurrency(goal.currentAmount)}
             </Text>
             <Text style={styles.progressPercent}>{progress.toFixed(0)}%</Text>
           </View>
         </View>

         {/* Progress bar — turns green at 100% */}
         <View style={styles.progressTrack}>
           <View style={{
             height: '100%',
             width: `${progress}%`,
             backgroundColor: progressColor(progress),
             borderRadius: 9999,
           }} />
         </View>

         {/* Quick-add buttons: +£10, +£50, +£100 */}
         <View style={styles.quickButtons}>
           {[10, 50, 100].map((amount) => (
             <TouchableOpacity
               key={amount}
               style={styles.quickButton}
               onPress={() => onUpdateAmount(goal.id, goal.currentAmount + amount)}
             >
               <Text style={styles.quickButtonText}>+£{amount}</Text>
             </TouchableOpacity>
           ))}
         </View>
       </View>
     );
   }

**Progress bar colour logic**

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Progress condition
     - Bar colour
   * - ``progress < 100``
     - Indigo ``#4f46e5``
   * - ``progress >= 100``
     - Green ``#10b981``

----

.. rubric:: AddGoalForm

Inline form for creating a new goal.  Appears between the header and the grid
when ``isAdding`` is ``true``; collapses on cancel or submit.

**Props**

.. list-table::
   :header-rows: 1
   :widths: 25 25 50

   * - Prop
     - Type
     - Description
   * - ``newGoalName``
     - ``string``
     - Controlled value for the name input
   * - ``newGoalTarget``
     - ``string``
     - Controlled value for the target amount input
   * - ``onNameChange``
     - ``(value: string) => void``
     - Updates ``newGoalName`` in the parent
   * - ``onTargetChange``
     - ``(value: string) => void``
     - Updates ``newGoalTarget`` in the parent
   * - ``onSubmit``
     - ``() => void``
     - Called when the user taps **Create Goal**
   * - ``onCancel``
     - ``() => void``
     - Called when the user taps **Cancel**; collapses the form

**Implementation**

.. code-block:: typescript

   export function AddGoalForm({
     newGoalName, newGoalTarget,
     onNameChange, onTargetChange,
     onSubmit, onCancel,
   }: AddGoalFormProps) {
     return (
       <View style={styles.form}>
         <TextInput
           placeholder="Goal Name (e.g. New Laptop)"
           value={newGoalName}
           onChangeText={onNameChange}
           style={styles.input}
           placeholderTextColor="#9ca3af"
         />
         <TextInput
           placeholder="Target Amount"
           value={newGoalTarget}
           onChangeText={onTargetChange}
           style={styles.input}
           keyboardType="numeric"
           placeholderTextColor="#9ca3af"
         />
         <View style={styles.formActions}>
           <TouchableOpacity onPress={onCancel} style={styles.cancelButton}>
             <Text style={styles.cancelButtonText}>Cancel</Text>
           </TouchableOpacity>
           <TouchableOpacity onPress={onSubmit} style={styles.submitButton}>
             <Text style={styles.submitButtonText}>Create Goal</Text>
           </TouchableOpacity>
         </View>
       </View>
     );
   }

----

.. rubric:: AddGoalButton

Small indigo button in the page header that toggles the ``AddGoalForm`` panel.

**Props**

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Prop
     - Type
     - Description
   * - ``onClick``
     - ``() => void``
     - Toggles ``isAdding`` in the parent ``Goals`` component

**Implementation**

.. code-block:: typescript

   export function AddGoalButton({ onClick }: AddGoalButtonProps) {
     return (
       <TouchableOpacity
         onPress={onClick}
         style={styles.addButton}
         activeOpacity={0.8}
       >
         <Plus size={18} color="#fff" />
         <Text style={styles.addButtonText}>New Goal</Text>
       </TouchableOpacity>
     );
   }

----

Helper Functions — ``Goalshelpers.ts``
---------------------------------------

:File: ``src/Pages/Goals/Goalshelpers.ts``

All functions are **pure** — they have no side effects.

.. rubric:: calcProgress

.. code-block:: typescript

   export function calcProgress(
     currentAmount: number,
     targetAmount: number
   ): number {
     if (targetAmount === 0) return 0;               // guard: avoid division by zero
     return Math.min(100, (currentAmount / targetAmount) * 100);
   }

Returns the percentage of the goal completed, capped at ``100``.

**Examples**

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - ``currentAmount``
     - ``targetAmount``
     - Result
   * - 50
     - 100
     - ``50``
   * - 120
     - 100
     - ``100`` (capped)
   * - 0
     - 0
     - ``0`` (guard clause)

----

.. rubric:: progressColor

.. code-block:: typescript

   export function progressColor(progress: number): string {
     return progress >= 100 ? '#10b981' : '#4f46e5';
   }

Returns the hex color for the progress bar fill — green when complete,
indigo while in progress.

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Condition
     - Return value
   * - ``progress >= 100``
     - ``'#10b981'`` (green — goal complete)
   * - ``progress < 100``
     - ``'#4f46e5'`` (indigo — in progress)

----

.. rubric:: defaultDeadline

.. code-block:: typescript

   export function defaultDeadline(): string {
     return new Date(Date.now() + 90 * 24 * 60 * 60 * 1000)
       .toISOString()
       .split('T')[0];
   }

Calculates a deadline 90 days from the current date and returns it as an
ISO 8601 date string (``YYYY-MM-DD``).

.. code-block:: typescript

   // Called on 2026-05-11 → returns "2026-08-09"
   defaultDeadline()

----

.. rubric:: formatCurrency

.. code-block:: typescript

   export function formatCurrency(amount: number): string {
     return `£${amount.toLocaleString()}`;
   }

Formats a number as a British pounds string.

.. code-block:: typescript

   formatCurrency(1500)   // → "£1,500"
   formatCurrency(50)     // → "£50"

----

Type Definitions
----------------

The ``Goal`` type is defined in ``FinanceContext.tsx`` and imported by all Goals feature files.

.. rubric:: Goal

.. code-block:: typescript

   export interface Goal {
     id:            string;   // Date.now().toString() assigned on creation
     name:          string;   // user-provided label, e.g. "New Laptop"
     targetAmount:  number;   // savings target in GBP
     currentAmount: number;   // amount saved so far; starts at 0
     deadline:      string;   // ISO 8601 date, defaults to 90 days from creation
   }

----

Context Integration
-------------------

:File: ``src/context/FinanceContext.tsx``

The Goals page relies on three context operations:

**addGoal**

.. code-block:: typescript

   addGoal(goal: Omit<Goal, 'id'>): void

Adds a new goal to the ``goals`` array.  The ``id`` is generated automatically
as ``Date.now().toString()``.

----

**updateGoalAmount**

.. code-block:: typescript

   updateGoalAmount(id: string, newAmount: number): void

Updates the ``currentAmount`` field of the matching goal.

.. admonition:: Side effects

   - Triggers a **gamification refresh** (XP recalculation).
   - Fires a **toast notification** if the goal reaches 100 % for the first time.

----

**removeGoal**

.. code-block:: typescript

   removeGoal(id: string): void

Deletes the goal with the given ``id`` from the ``goals`` array.

.. note::
   ``removeGoal`` is available in the context but is not currently wired up to
   any UI element on the Goals page.

----

Empty State
-----------

When ``goals.length === 0`` the page renders a centred message in place of
the grid:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Element
     - Content
   * - Title
     - *"No Goals Yet"*
   * - Body text
     - *"Start by creating your first savings goal."*

The empty state disappears automatically as soon as the first goal is added.

----

Dependencies
------------

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Package
     - Used for
   * - ``lucide-react-native``
     - ``Target`` icon on each ``GoalCard`` header; ``Plus`` icon on the add button
   * - ``FinanceContext`` (internal)
     - Shared goals state and mutation helpers

----

.. seealso::

   - :doc:`budget_page` — Budget tracking feature built on the same context layer
   - ``src/context/FinanceContext.tsx`` — Global state provider and API client
