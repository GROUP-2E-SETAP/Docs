Transactions Page
=================

.. contents:: Page contents
   :local:
   :depth: 2
   :backlinks: none

----

Overview
--------

The **Transactions Page** is the primary hub for viewing and managing all financial
records.  It provides a searchable, filterable list of every transaction stored in
the backend, together with an inline modal for creating new entries and one-tap
deletion of existing ones.

.. note::
   All mutations (add, delete) are executed against the live backend API through
   ``FinanceContext``.  The local list re-renders automatically after each
   successful write because the context refetches from the server.

.. important::
   The Transactions page is the **single source of truth** for financial data
   displayed across the whole app — the Dashboard, Budget, and AI Advisor pages
   all derive their figures from the same ``transactions[]`` array in context.

----

File Structure
--------------

.. list-table::
   :header-rows: 1
   :widths: 45 55

   * - File
     - Purpose
   * - ``Transactions.tsx``
     - Page entry point; assembles filters, list, and modal
   * - ``Transactionscomponents.tsx``
     - Reusable display components (row, filters, empty state)
   * - ``Transactionshelpers.ts``
     - Pure filtering, formatting, and style-mapping utilities
   * - ``Transactions.styles.ts``
     - ``StyleSheet`` definitions for the entire Transactions feature
   * - ``AddTransactionModal.tsx``
     - Modal orchestrator; owns form state and submission logic
   * - ``AddTransactionModalcomponents.tsx``
     - Individual form field components used inside the modal
   * - ``AddTransactionModal.styles.ts``
     - ``StyleSheet`` definitions for the modal
   * - ``AddTransactionModalhelpers.ts``
     - ``FormState`` type, default state factory, and validation logic

----

Data Flow
---------

The diagram below shows how data moves from the global context through the filter
layer to the rendered list, and how mutations travel back through context to the API:

.. code-block:: text

    FinanceContext
        │
        ├─ transactions[]  ──► filterTransactions()  ──► FlatList (TransactionRow[])
        │                             ▲
        │                    filterType │ filterCategory │ searchTerm (local state)
        │
        ├─ categories[]    ──► buildFilterCategories() ──► CategoryFilter chips
        │
        ├─ addTransaction()  ◄── AddTransactionModal (handleSubmit)
        │                                │
        │                       POST /api/v1/transaction
        │
        └─ removeTransaction() ◄── TransactionRow (onDelete)
                                           │
                                  DELETE /api/v1/transaction/{id}

.. tip::
   Because ``filtered`` is computed with ``useMemo``, the list only re-renders
   when ``transactions``, ``filterType``, ``filterCategory``, or ``searchTerm``
   actually change — not on every parent render.

----

Main Component — ``Transactions``
---------------------------------

:File: ``src/Pages/Transactions/Transactions.tsx``
:Dependencies: ``FinanceContext``, ``Transactionscomponents``, ``Transactionshelpers``, ``AddTransactionModal``

The root component for the Transactions feature.  It reads the global transaction
list and category catalogue from :func:`useFinance`, derives filtered results via
``useMemo``, and renders the search bar, filter controls, and transaction list.

**Props**

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Prop
     - Type
     - Description
   * - ``onBack``
     - ``() => void``
     - Navigates back to the previous screen when the header chevron is tapped

**State**

.. list-table::
   :header-rows: 1
   :widths: 25 25 50

   * - Variable
     - Type
     - Description
   * - ``filterType``
     - :class:`FilterType`
     - Active type filter: ``'all'``, ``'income'``, or ``'expense'``
   * - ``filterCategory``
     - :class:`FilterCategory`
     - Active category chip; ``'All'`` means no category filter applied
   * - ``searchTerm``
     - ``string``
     - Live search string matched against description and category
   * - ``modalOpen``
     - ``boolean``
     - Controls visibility of the ``AddTransactionModal`` overlay

**Context values consumed**

.. list-table::
   :header-rows: 1
   :widths: 30 25 45

   * - Value
     - Type
     - Description
   * - ``transactions``
     - ``Transaction[]``
     - Full list of user transactions fetched from the API
   * - ``categories``
     - ``string[]``
     - Available category names used to populate the category chip list
   * - ``removeTransaction``
     - ``(id: string) => Promise<void>``
     - Deletes a transaction by ID via the backend API
   * - ``isLoading``
     - ``boolean``
     - Shows a loading message in the list while data is being fetched
   * - ``errorMessage``
     - ``string | null``
     - Shown in place of the list if the API request fails

**Derived data (memoised)**

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Variable
     - How it is produced
   * - ``filterCategories``
     - :func:`buildFilterCategories` ``(categories)`` — prepends ``'All'`` to the API list
   * - ``filtered``
     - :func:`filterTransactions` ``(transactions, filterType, filterCategory, searchTerm)``

**Implementation**

.. code-block:: typescript

   export function Transactions({ onBack }: TransactionsProps) {
     const { transactions, categories, removeTransaction,
             isLoading, errorMessage } = useFinance();

     const [filterType, setFilterType]         = useState<FilterType>('all');
     const [filterCategory, setFilterCategory] = useState<FilterCategory>('All');
     const [searchTerm, setSearchTerm]         = useState('');
     const [modalOpen, setModalOpen]           = useState(false);

     const filterCategories = useMemo(
       () => buildFilterCategories(categories),
       [categories],
     );

     const filtered = useMemo(
       () => filterTransactions(transactions, filterType, filterCategory, searchTerm),
       [transactions, filterType, filterCategory, searchTerm],
     );

     return (
       <SafeAreaView style={styles.screen}>
         <View style={styles.pageHeader}>
           <TouchableOpacity onPress={onBack}>
             <ChevronLeft size={24} color="#4f46e5" />
           </TouchableOpacity>
           <Text style={styles.pageTitle}>Transactions</Text>
           <Text style={styles.pageSubtitle}>
             {filtered.length} record{filtered.length !== 1 ? 's' : ''}
           </Text>
           <TouchableOpacity style={styles.addButton} onPress={() => setModalOpen(true)}>
             <Plus size={18} color="#fff" />
             <Text style={styles.addButtonText}>Add</Text>
           </TouchableOpacity>
         </View>

         <View style={styles.searchContainer}>
           <Search size={16} color="#9ca3af" />
           <TextInput value={searchTerm} onChangeText={setSearchTerm} placeholder="Search..." />
         </View>

         <TypeFilter value={filterType} onChange={setFilterType} />
         <CategoryFilter categories={filterCategories}
                         value={filterCategory} onChange={setFilterCategory} />

         <FlatList
           data={filtered}
           keyExtractor={(item) => String(item.id)}
           renderItem={({ item }) => (
             <TransactionRow item={item}
                             onDelete={(id) => void removeTransaction(id)} />
           )}
           ListEmptyComponent={
             isLoading   ? <LoadingState /> :
             errorMessage ? <ErrorState message={errorMessage} /> :
                            <EmptyTransactions />
           }
         />

         <AddTransactionModal isOpen={modalOpen} onClose={() => setModalOpen(false)} />
       </SafeAreaView>
     );
   }

----

UI Components — ``Transactionscomponents.tsx``
-----------------------------------------------

:File: ``src/Pages/Transactions/Transactionscomponents.tsx``

----

.. rubric:: CategoryIcon

Maps a category name to the appropriate ``lucide-react-native`` icon.

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Prop
     - Type
     - Description
   * - ``category``
     - ``string``
     - Transaction category name
   * - ``color``
     - ``string``
     - Icon fill color (supplied by :func:`getCategoryStyle`)

**Category-to-icon mapping**

.. hlist::
   :columns: 2

   - ``Food`` → ``Utensils``
   - ``Transportation`` → ``Car``
   - ``Housing`` → ``Home``
   - ``Bills`` → ``Receipt``
   - ``Education`` → ``GraduationCap``
   - ``Entertainment`` → ``Film``
   - ``Shopping`` → ``ShoppingBag``
   - *(any other)* → ``MoreHorizontal``

----

.. rubric:: TransactionRow

Renders a single transaction as a list row with icon, description, category badge,
date, formatted amount, and a delete button.

.. list-table::
   :header-rows: 1
   :widths: 20 30 50

   * - Prop
     - Type
     - Description
   * - ``item``
     - :class:`Transaction`
     - The transaction object to display
   * - ``onDelete``
     - ``(id: string) => void``
     - Called when the trash icon is pressed

**Visual behaviour**

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Condition
     - Appearance
   * - ``type === 'income'``
     - Amount prefixed with ``+``, displayed in green (``#16a34a``)
   * - ``type === 'expense'``
     - Amount prefixed with ``-``, displayed in red (``#dc2626``)
   * - ``description`` present
     - Description shown as the primary label; category in badge below
   * - ``description`` absent
     - Category name used as the fallback primary label

**Implementation**

.. code-block:: typescript

   export function TransactionRow({ item, onDelete }: TransactionRowProps) {
     const { bg, icon } = getCategoryStyle(item.category, item.type);
     const isIncome = item.type === 'income';

     return (
       <View style={styles.txRow}>
         <View style={[styles.txIcon, { backgroundColor: bg }]}>
           <CategoryIcon category={item.category} color={icon} />
         </View>
         <View style={styles.txInfo}>
           <Text style={styles.txDescription} numberOfLines={1}>
             {item.description ?? item.category}
           </Text>
           <View style={styles.txMeta}>
             <View style={[styles.categoryBadge, { backgroundColor: bg }]}>
               <Text style={[styles.categoryBadgeText, { color: icon }]}>
                 {item.category}
               </Text>
             </View>
             <Text style={styles.txDate}>• {item.date}</Text>
           </View>
         </View>
         <View style={styles.txRight}>
           <Text style={[styles.txAmount,
             isIncome ? styles.txAmountIncome : styles.txAmountExpense]}>
             {isIncome ? '+' : '-'}£{formatAmount(item.amount)}
           </Text>
           <TouchableOpacity onPress={() => onDelete(item.id)}>
             <Trash2 size={15} color="#f87171" />
           </TouchableOpacity>
         </View>
       </View>
     );
   }

----

.. rubric:: TypeFilter

A three-button toggle row for filtering the list by transaction type.

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Prop
     - Type
     - Description
   * - ``value``
     - :class:`FilterType`
     - Currently active filter
   * - ``onChange``
     - ``(type: FilterType) => void``
     - Called when any button is pressed

**Active-button colour overrides**

.. csv-table::
   :header: "Option", "Text colour"
   :widths: 30, 70

   "``income``", "Green — ``#16a34a``"
   "``expense``", "Red — ``#dc2626``"
   "``all``", "Default indigo active style"

----

.. rubric:: CategoryFilter

A horizontally scrolling list of category chip buttons sourced from the API.

.. list-table::
   :header-rows: 1
   :widths: 20 25 55

   * - Prop
     - Type
     - Description
   * - ``categories``
     - ``FilterCategory[]``
     - Ordered chip labels; first entry is always ``'All'``
   * - ``value``
     - ``FilterCategory``
     - Currently selected chip
   * - ``onChange``
     - ``(cat: FilterCategory) => void``
     - Called when a chip is tapped

----

.. rubric:: EmptyTransactions

Placeholder rendered when the filtered list is empty and no loading or error state
is active.

.. admonition:: Display conditions

   ``EmptyTransactions`` is shown only when **all three** of the following are true:

   1. ``isLoading`` is ``false``
   2. ``errorMessage`` is ``null``
   3. The ``filtered`` array has length ``0``

----

Add Transaction Modal — ``AddTransactionModal``
------------------------------------------------

:File: ``src/Pages/Transactions/AddTransactionModal.tsx``

A full-screen transparent modal presenting a form for creating a new transaction.
It owns all form state and delegates validation and submission to the helper module.

.. warning::
   Closing the modal with the **X** button or by tapping the backdrop discards all
   unsaved input.  There is no draft persistence between modal sessions.

**Props**

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Prop
     - Type
     - Description
   * - ``isOpen``
     - ``boolean``
     - Mounts and shows the modal when ``true``
   * - ``onClose``
     - ``() => void``
     - Called by the X button, backdrop tap, and after a successful submit

**Internal state**

.. list-table::
   :header-rows: 1
   :widths: 20 30 50

   * - Variable
     - Type
     - Description
   * - ``form``
     - :class:`FormState`
     - Controlled form values (type, amount, description, category, date)
   * - ``errors``
     - :class:`FormErrors`
     - Validation error strings keyed by field name

**Category sync — ``useEffect``**

When the ``categories`` list loads (or changes), the effect ensures the selected
category remains valid.  If the current selection is no longer present in the list,
it resets to the first available category:

.. code-block:: typescript

   useEffect(() => {
     if (categories.length === 0) return;
     setForm((previous) =>
       categories.includes(previous.category)
         ? previous
         : { ...previous, category: categories[0] },
     );
   }, [categories]);

**Submit handler — ``handleSubmit``**

.. code-block:: typescript

   const handleSubmit = () => {
     const newErrors = validateForm(form);
     setErrors(newErrors);
     if (Object.keys(newErrors).length > 0) return;   // abort if invalid

     void addTransaction({
       type:        form.type,
       amount:      Number(form.amount),
       description: form.description.trim(),
       category:    form.category,
       date:        form.date,
     })
       .then(() => {
         RootToast.show('Transaction added successfully!', {
           duration:        RootToast.durations.SHORT,
           position:        RootToast.positions.BOTTOM,
           backgroundColor: '#4f46e5',
         });
         setForm(defaultFormState(categories));
         setErrors({});
         onClose();
       })
       .catch((error: unknown) => {
         RootToast.show(
           error instanceof Error ? error.message : 'Unable to add transaction.',
           { duration: RootToast.durations.SHORT, backgroundColor: '#dc2626' },
         );
       });
   };

**Interaction flow**

1. User taps **Add** in the page header → ``modalOpen`` becomes ``true``.
2. Modal mounts; ``form`` is pre-populated by :func:`defaultFormState` (today's date, first available category).
3. User fills in the form fields; each keystroke updates ``form`` via the ``set`` helper.
4. User taps **Add Transaction** → :func:`handleSubmit` runs :func:`validateForm`.

   - **Validation fails** → ``errors`` state updated; field-level messages appear inline.
   - **Validation passes** → ``addTransaction`` API call is made.

5. On **API success**: indigo toast shown, form reset, modal closed.
6. On **API failure**: red error toast shown; form stays open for correction.
7. User taps backdrop or **X** → ``handleClose`` clears ``errors`` and calls ``onClose``.

----

Modal Form Components — ``AddTransactionModalcomponents.tsx``
--------------------------------------------------------------

:File: ``src/Pages/Transactions/AddTransactionModalcomponents.tsx``

.. rubric:: ModalHeader

Renders the modal title ``"Add Transaction"`` and a close (``X``) button.

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Prop
     - Type
     - Description
   * - ``onClose``
     - ``() => void``
     - Triggered by the X ``TouchableOpacity``

----

.. rubric:: TypeToggle

A two-button toggle for selecting :attr:`'expense'` or :attr:`'income'`.  Mirrors
the visual style of :class:`TypeFilter` on the main page.

.. list-table::
   :header-rows: 1
   :widths: 20 25 55

   * - Prop
     - Type
     - Description
   * - ``value``
     - ``TransactionType``
     - Currently selected type
   * - ``onChange``
     - ``(type: TransactionType) => void``
     - Called when either button is pressed

----

.. rubric:: AmountField

A numeric input prefixed with the ``£`` currency symbol.

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Prop
     - Type
     - Description
   * - ``value``
     - ``string``
     - Controlled input value (raw string; parsed on submit)
   * - ``onChange``
     - ``(v: string) => void``
     - Called on every keystroke
   * - ``error``
     - ``string?``
     - Validation message shown beneath the input when present

.. note::
   ``keyboardType="decimal-pad"`` is set so that mobile users see a numeric
   keyboard rather than the full QWERTY layout.

----

.. rubric:: TextField

A generic labelled ``TextInput`` used for both the **Description** and **Date**
fields.

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Prop
     - Type
     - Description
   * - ``label``
     - ``string``
     - Field label rendered above the input
   * - ``value``
     - ``string``
     - Controlled input value
   * - ``onChange``
     - ``(v: string) => void``
     - Called on every keystroke
   * - ``placeholder``
     - ``string?``
     - Hint text shown when the field is empty
   * - ``error``
     - ``string?``
     - Validation message shown beneath the input when present

----

.. rubric:: CategoryPicker

A wrap-layout grid of tappable category chips.  Only one chip can be active at a
time; selecting a new chip deselects the previous one.

.. list-table::
   :header-rows: 1
   :widths: 20 25 55

   * - Prop
     - Type
     - Description
   * - ``categories``
     - ``Category[]``
     - List of available category names from the API
   * - ``value``
     - ``Category``
     - Currently selected category
   * - ``onChange``
     - ``(cat: Category) => void``
     - Called when a chip is tapped
   * - ``error``
     - ``string?``
     - Validation message shown beneath the grid when present

.. note::
   Falls back to ``['Uncategorized']`` if the API has not yet returned any
   categories, ensuring the picker always has at least one selectable option.

----

.. rubric:: SubmitButton

A full-width indigo button labelled **"Add Transaction"**.

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Prop
     - Type
     - Description
   * - ``onPress``
     - ``() => void``
     - Triggered on tap; wired to :func:`handleSubmit` in the parent modal

----

Helper Functions — ``AddTransactionModalhelpers.ts``
-----------------------------------------------------

:File: ``src/Pages/Transactions/AddTransactionModalhelpers.ts``

All functions are **pure** — they accept data as arguments and return new values
with no side effects.

.. rubric:: defaultFormState

Returns a fresh :class:`FormState` object pre-populated with safe defaults.

.. code-block:: typescript

   export function defaultFormState(categories: Category[] = []): FormState {
     return {
       type:        'expense',
       amount:      '',
       description: '',
       category:    categories[0] ?? 'Uncategorized',
       date:        new Date().toISOString().split('T')[0],   // today as YYYY-MM-DD
     };
   }

Default values
   ``type``
      ``'expense'`` — the most common transaction type.
   ``amount``
      Empty string — forces the user to enter a value explicitly.
   ``description``
      Empty string.
   ``category``
      First element of the ``categories`` array, or ``'Uncategorized'`` if the
      array is empty.
   ``date``
      Today's date in ``YYYY-MM-DD`` format, derived from ``new Date()``.

----

.. rubric:: validateForm

Runs synchronous validation on a :class:`FormState` and returns a
:class:`FormErrors` map of field-level error strings.  Returns an empty object
when the form is valid.

.. code-block:: typescript

   export function validateForm(form: FormState): FormErrors {
     const errors: FormErrors = {};

     if (!form.description.trim())
       errors.description = 'Description is required';
     if (!form.category.trim())
       errors.category    = 'Category is required';
     if (!form.amount ||
         Number.isNaN(Number(form.amount)) ||
         Number(form.amount) <= 0) {
       errors.amount = 'Enter a valid amount greater than 0';
     }
     if (!form.date)
       errors.date = 'Date is required';

     return errors;
   }

**Validation rules**

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Field
     - Rule
   * - ``description``
     - Must be a non-empty string after trimming whitespace
   * - ``category``
     - Must be a non-empty string after trimming whitespace
   * - ``amount``
     - Must be present, parse as a finite number, and be greater than ``0``
   * - ``date``
     - Must be a truthy string (``YYYY-MM-DD`` format expected by the API)

----

Helper Functions — ``Transactionshelpers.ts``
----------------------------------------------

:File: ``src/Pages/Transactions/Transactionshelpers.ts``

All functions are **pure** — no side effects.

----

.. rubric:: buildFilterCategories

.. code-block:: typescript

   export function buildFilterCategories(categories: string[]): FilterCategory[] {
     return ['All', ...categories];
   }

Prepends the ``'All'`` sentinel to the API category list so :class:`CategoryFilter`
always has a "show everything" option at position zero.

**Example**

.. code-block:: typescript

   buildFilterCategories(['Food', 'Housing', 'Transport'])
   // → ['All', 'Food', 'Housing', 'Transport']

----

.. rubric:: getCategoryStyle

.. code-block:: typescript

   export function getCategoryStyle(category: string, type: TransactionType): CategoryStyle {
     if (type === 'income') return { bg: '#f0fdf4', icon: '#16a34a' };

     switch (category.toLowerCase()) {
       case 'food':           return { bg: '#fff7ed', icon: '#ea580c' };
       case 'transportation': return { bg: '#eff6ff', icon: '#2563eb' };
       case 'housing':        return { bg: '#faf5ff', icon: '#9333ea' };
       case 'bills':          return { bg: '#fefce8', icon: '#ca8a04' };
       case 'education':      return { bg: '#eef2ff', icon: '#4f46e5' };
       case 'entertainment':  return { bg: '#fdf2f8', icon: '#db2777' };
       case 'shopping':       return { bg: '#ecfeff', icon: '#0891b2' };
       default:               return { bg: '#f9fafb', icon: '#6b7280' };
     }
   }

Returns a :class:`CategoryStyle` pair used to style the icon container and the
:class:`CategoryIcon` foreground color.  Income transactions always use green
regardless of their category.

**Color palette**

.. csv-table::
   :header: "Category", "Background", "Icon color"
   :widths: 25, 25, 25

   "*(income — any category)*", "``#f0fdf4``", "``#16a34a``"
   "Food", "``#fff7ed``", "``#ea580c``"
   "Transportation", "``#eff6ff``", "``#2563eb``"
   "Housing", "``#faf5ff``", "``#9333ea``"
   "Bills", "``#fefce8``", "``#ca8a04``"
   "Education", "``#eef2ff``", "``#4f46e5``"
   "Entertainment", "``#fdf2f8``", "``#db2777``"
   "Shopping", "``#ecfeff``", "``#0891b2``"
   "*(default / unknown)*", "``#f9fafb``", "``#6b7280``"

----

.. rubric:: filterTransactions

.. code-block:: typescript

   export function filterTransactions<T extends {
     type: TransactionType;
     category: string;
     description?: string;
   }>(
     transactions: T[],
     filterType: FilterType,
     filterCategory: FilterCategory,
     searchTerm: string,
   ): T[] {
     const search = searchTerm.toLowerCase();

     return transactions.filter((transaction) => {
       const matchType     = filterType === 'all' ||
                             transaction.type === filterType;
       const matchCategory = filterCategory === 'All' ||
                             transaction.category === filterCategory;
       const matchSearch   =
         (transaction.description ?? '').toLowerCase().includes(search) ||
         transaction.category.toLowerCase().includes(search);

       return matchType && matchCategory && matchSearch;
     });
   }

All three predicates must pass for a transaction to appear in the result.

.. topic:: Search behaviour

   The search term is compared **case-insensitively** against two fields:

   - ``description`` (falls back to an empty string if absent)
   - ``category``

   This means searching ``"food"`` will match transactions whose category is
   ``"Food"`` *or* whose description contains the word "food".

----

.. rubric:: formatAmount

.. code-block:: typescript

   export function formatAmount(amount: number | string): string {
     return Number(amount).toLocaleString(undefined, {
       minimumFractionDigits: 2,
       maximumFractionDigits: 2,
     });
   }

Converts a raw amount value to a locale-formatted string with exactly two decimal
places.

**Examples**

.. code-block:: typescript

   formatAmount(1234.5)    // → "1,234.50"  (en-GB locale)
   formatAmount('99')      // → "99.00"
   formatAmount(0.1 + 0.2) // → "0.30"  (avoids floating-point display issues)

----

Type Definitions
----------------

.. rubric:: Transaction

:File: ``src/context/FinanceContext.tsx``

.. code-block:: typescript

   export interface Transaction {
     id:           string;
     type:         'expense' | 'income';
     category:     string;
     amount:       number;
     date:         string;          // YYYY-MM-DD
     description?: string;          // optional free-text label
   }

----

.. rubric:: FormState

:File: ``src/Pages/Transactions/AddTransactionModalhelpers.ts``

.. code-block:: typescript

   export interface FormState {
     type:        TransactionType;   // 'expense' | 'income'
     amount:      string;            // raw input; converted to number on submit
     description: string;
     category:    Category;
     date:        string;            // YYYY-MM-DD
   }

.. note::
   ``amount`` is stored as a ``string`` (not ``number``) so that the controlled
   ``TextInput`` can reflect partial input such as ``"12."`` without rounding.

----

.. rubric:: FormErrors

.. code-block:: typescript

   export type FormErrors = Partial<Record<keyof FormState, string>>;

A partial map from field name to validation error string.  An empty object
(``{}``) indicates a valid form ready for submission.

----

.. rubric:: CategoryStyle

.. code-block:: typescript

   export interface CategoryStyle {
     bg:   string;   // background hex — used on icon container and category badge
     icon: string;   // foreground hex — used on the icon and badge text
   }

----

.. rubric:: FilterType / FilterCategory

.. code-block:: typescript

   export type FilterType     = 'all' | TransactionType;   // 'all' | 'income' | 'expense'
   export type FilterCategory = string;                    // 'All' or any API category name

----

Dependencies
------------

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Package
     - Used for
   * - ``lucide-react-native``
     - Category icons, ``Search``, ``ChevronLeft``, ``Plus``, ``Trash2``, ``X``
   * - ``react-native-root-toast``
     - Success (indigo) and error (red) toast notifications on form submit
   * - ``FinanceContext`` (internal)
     - Shared transaction list, categories, ``addTransaction``, ``removeTransaction``

----

.. seealso::

   - :doc:`budget_page` — Aggregates the same transaction list into spending charts
   - :doc:`dashboard_page` — Displays the most recent transactions via ``TransactionList``
   - :doc:`ai_page` — Uses transaction data to generate AI-powered financial insights
   - ``src/context/FinanceContext.tsx`` — Global state provider and REST API client
