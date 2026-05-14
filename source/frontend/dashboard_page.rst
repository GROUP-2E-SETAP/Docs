Dashboard Page
==============

Overview
--------

The **Dashboard Page** is the first screen shown by the Expo app.  It gives the
user a compact summary of their current finances, reward progress, profile
state, notifications, and latest transactions.

The page also acts as the quickest entry point for adding a new transaction
through the shared ``AddTransactionModal``.

.. note::
   Dashboard finance values are read from ``FinanceContext``.  Transactions,
   profile details, notifications, and gamification data are fetched through
   the backend API, while the unread notification state is updated locally in
   the frontend.

----

File Structure
--------------

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - File
     - Purpose
   * - ``Dashboard.tsx``
     - Page entry point; consumes context data, runs the mount animation, and controls the transaction modal
   * - ``Dashboardcomponents.tsx``
     - Reusable UI components for the header, notifications, profile modal, balance cards, and recent transactions
   * - ``Dashboardhelpers.ts``
     - Shared types, formatting utilities, layout constants, and platform shadow helper
   * - ``DashBoard.styles.ts``
     - ``StyleSheet`` definitions for the Dashboard feature
   * - ``../Transactions/AddTransactionModal.tsx``
     - Modal opened from the Dashboard **Add** button

----

Data Flow
---------

.. code-block:: text

    FinanceContext
        |
        |- currentUser, gamification, notifications
        |       |
        |       +--> DashboardHeader
        |              |
        |              |- NotificationModal
        |              |- ProfileModal --> updateUserProfile()
        |              +--> Add button --> setModalOpen(true)
        |
        |- totalBalance, monthlyIncome, monthlyExpenses
        |       |
        |       +--> BalanceCards
        |
        |- transactions[], isLoading, errorMessage
        |       |
        |       +--> TransactionList --> latest 5 transactions
        |
        +--> addTransaction()
                ^
                |
          AddTransactionModal

----

Main Component - ``Dashboard``
------------------------------

:File: ``src/Pages/Dashboard/Dashboard.tsx``

The root component of the Dashboard feature.  It pulls all visible finance,
profile, notification, and reward values from ``useFinance()``, then passes the
data into focused child components.

**Props**

.. list-table::
   :header-rows: 1
   :widths: 25 25 50

   * - Prop
     - Type
     - Description
   * - ``onViewAll``
     - ``() => void``
     - Optional callback shown as a **View All** action in the recent transactions card

**Context values consumed**

.. list-table::
   :header-rows: 1
   :widths: 30 25 45

   * - Value
     - Type
     - Description
   * - ``totalBalance``
     - ``number``
     - Net balance, calculated as income minus expenses
   * - ``monthlyIncome``
     - ``number``
     - Sum of all income transactions in context
   * - ``monthlyExpenses``
     - ``number``
     - Sum of all expense transactions in context
   * - ``transactions``
     - ``Transaction[]``
     - Source list for the latest transaction preview
   * - ``currentUser``
     - ``UserProfile``
     - Profile details shown in the avatar and profile modal
   * - ``notifications``
     - ``AppNotification[]``
     - Notification feed displayed in the modal and reward strip
   * - ``unreadNotificationCount``
     - ``number``
     - Drives the bell badge count
   * - ``markNotificationsRead``
     - ``() => void``
     - Marks notification objects as read in local state
   * - ``gamification``
     - ``GamificationSummary``
     - XP, level, and streak values shown in the header
   * - ``updateUserProfile``
     - ``(profile) => Promise<void>``
     - Persists profile changes through the context/API layer
   * - ``isLoading``
     - ``boolean``
     - Used by ``TransactionList`` to show a loading state
   * - ``isProfileSaving``
     - ``boolean``
     - Shows an activity indicator while profile changes save
   * - ``errorMessage``
     - ``string``
     - Displayed in the recent transaction card when loading fails

**Local state**

.. list-table::
   :header-rows: 1
   :widths: 25 20 55

   * - Variable
     - Type
     - Description
   * - ``modalOpen``
     - ``boolean``
     - Controls visibility of ``AddTransactionModal``
   * - ``fadeAnim``
     - ``Animated.Value``
     - Starts at ``0`` and animates content opacity to ``1``
   * - ``slideAnim``
     - ``Animated.Value``
     - Starts at ``20`` and animates content upward into place

**Implementation**

.. code-block:: tsx

   export function Dashboard({ onViewAll }: DashboardProps): React.JSX.Element {
     const {
       totalBalance,
       monthlyIncome,
       monthlyExpenses,
       transactions,
       currentUser,
       notifications,
       unreadNotificationCount,
       markNotificationsRead,
       gamification,
       updateUserProfile,
       isLoading,
       isProfileSaving,
       errorMessage,
     } = useFinance();

     const [modalOpen, setModalOpen] = useState(false);
     const fadeAnim = useRef(new Animated.Value(0)).current;
     const slideAnim = useRef(new Animated.Value(20)).current;

     useEffect(() => {
       Animated.parallel([
         Animated.timing(fadeAnim, {
           toValue: 1,
           duration: 400,
           useNativeDriver: true,
         }),
         Animated.timing(slideAnim, {
           toValue: 0,
           duration: 400,
           useNativeDriver: true,
         }),
       ]).start();
     }, [fadeAnim, slideAnim]);

     return (
       <SafeAreaView style={styles.safeArea}>
         <ScrollView contentContainerStyle={styles.scrollContent}>
           <Animated.View
             style={[
               styles.container,
               { opacity: fadeAnim, transform: [{ translateY: slideAnim }] },
             ]}
           >
             <DashboardHeader
               currentUser={currentUser}
               gamification={gamification}
               notifications={notifications}
               unreadNotificationCount={unreadNotificationCount}
               isProfileSaving={isProfileSaving}
               onUpdateProfile={updateUserProfile}
               onMarkNotificationsRead={markNotificationsRead}
               onAddTransaction={() => setModalOpen(true)}
             />

             <BalanceCards
               totalBalance={totalBalance}
               monthlyIncome={monthlyIncome}
               monthlyExpenses={monthlyExpenses}
             />

             <TransactionList
               transactions={transactions}
               onViewAll={onViewAll}
               isLoading={isLoading}
               errorMessage={errorMessage}
             />
           </Animated.View>
         </ScrollView>

         <AddTransactionModal
           isOpen={modalOpen}
           onClose={() => setModalOpen(false)}
         />
       </SafeAreaView>
     );
   }

----

UI Components - ``Dashboardcomponents.tsx``
--------------------------------------------

:File: ``src/Pages/Dashboard/Dashboardcomponents.tsx``

.. rubric:: DashboardHeader

Renders the top dashboard toolbar, XP badge, **Add** transaction button,
notifications button, avatar pill, reward strip, and the two modal panels used
for notifications and profile editing.

**Props**

.. list-table::
   :header-rows: 1
   :widths: 25 35 40

   * - Prop
     - Type
     - Description
   * - ``currentUser``
     - ``UserProfile``
     - Profile data used by the avatar and profile modal
   * - ``gamification``
     - ``GamificationSummary``
     - XP, level, and streak values
   * - ``notifications``
     - ``AppNotification[]``
     - Notifications shown in the modal and recent reward panel
   * - ``unreadNotificationCount``
     - ``number``
     - Badge count displayed over the bell icon
   * - ``isProfileSaving``
     - ``boolean``
     - Displays a spinner on the profile save button
   * - ``onUpdateProfile``
     - ``(profile) => Promise<void>``
     - Called by ``handleSaveProfile``
   * - ``onMarkNotificationsRead``
     - ``() => void``
     - Called when the notification panel opens
   * - ``onAddTransaction``
     - ``() => void``
     - Opens ``AddTransactionModal`` in the parent component

**Internal state**

.. list-table::
   :header-rows: 1
   :widths: 25 20 55

   * - Variable
     - Type
     - Description
   * - ``isNotificationsOpen``
     - ``boolean``
     - Controls the notification modal
   * - ``isProfileOpen``
     - ``boolean``
     - Controls the profile modal
   * - ``name``
     - ``string``
     - Draft profile name
   * - ``email``
     - ``string``
     - Draft profile email
   * - ``phone``
     - ``string``
     - Draft profile phone number

**Profile save flow**

.. code-block:: tsx

   useEffect(() => {
     setName(currentUser.name);
     setEmail(currentUser.email);
     setPhone(currentUser.phone);
   }, [currentUser.email, currentUser.name, currentUser.phone]);

   const handleSaveProfile = async () => {
     await onUpdateProfile({ name, email, phone });
     setIsProfileOpen(false);
   };

1. Local input fields are synced from ``currentUser``.
2. User edits the modal fields.
3. Save calls ``onUpdateProfile({ name, email, phone })``.
4. The modal closes after the promise resolves.

----

.. rubric:: NotificationModal

Transparent modal opened from the bell button.  It displays an empty message
when there are no notifications, otherwise it renders cards newest-first as
supplied by ``FinanceContext``.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Element
     - Behaviour
   * - Backdrop
     - Pressing outside the modal calls ``onClose``
   * - Close icon
     - Calls ``onClose``
   * - XP pill
     - Rendered only when ``notification.xpAwarded`` exists
   * - Timestamp
     - Formatted with ``Intl.DateTimeFormat('en-GB')``

**Implementation**

.. code-block:: tsx

   notifications.map((notification) => (
     <View key={notification.id} style={styles.notificationCard}>
       <Text style={styles.notificationTitle}>{notification.title}</Text>
       {notification.xpAwarded ? (
         <View style={styles.notificationXpPill}>
           <Text>+{notification.xpAwarded} XP</Text>
         </View>
       ) : null}
       <Text>{notification.message}</Text>
     </View>
   ))

----

.. rubric:: ProfileModal

Allows the user to edit their name, email address, and phone number.  The modal
uses controlled inputs owned by ``DashboardHeader`` so changes are not pushed to
global state until **Save changes** is pressed.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Field
     - Input behaviour
   * - Name
     - Plain text input
   * - Email
     - ``keyboardType="email-address"`` and ``autoCapitalize="none"``
   * - Phone
     - ``keyboardType="phone-pad"``
   * - Save button
     - Shows ``ActivityIndicator`` when ``isSaving`` is ``true``

.. warning::
   ``updateUserProfile`` attempts to persist profile changes through the API.
   If the API call fails, ``FinanceContext`` applies the profile edits locally
   and shows a toast saying the profile was saved locally.

----

.. rubric:: BalanceCards

Shows the three key account summary values: total balance, monthly income, and
monthly expenses.

.. list-table::
   :header-rows: 1
   :widths: 25 25 50

   * - Prop
     - Type
     - Description
   * - ``totalBalance``
     - ``number``
     - Rendered in the primary indigo card
   * - ``monthlyIncome``
     - ``number``
     - Rendered with an upward green icon
   * - ``monthlyExpenses``
     - ``number``
     - Rendered with a downward red icon

**Implementation**

.. code-block:: tsx

   export function BalanceCards({
     totalBalance,
     monthlyIncome,
     monthlyExpenses,
   }: BalanceCardsProps): React.JSX.Element {
     return (
       <View style={[styles.cardRow, isWide && styles.cardRowWide]}>
         <View style={[styles.card, styles.cardPrimary, isWide && styles.cardFlex]}>
           <Wallet size={20} color="#ffffff" />
           <Text>{formatCurrency(totalBalance)}</Text>
         </View>

         <View style={[styles.card, styles.cardWhite, isWide && styles.cardFlex]}>
           <ArrowUpCircle size={16} color="#16a34a" />
           <Text>{formatCurrency(monthlyIncome)}</Text>

           <ArrowDownCircle size={16} color="#dc2626" />
           <Text>{formatCurrency(monthlyExpenses)}</Text>
         </View>
       </View>
     );
   }

----

.. rubric:: TransactionList

Displays the five most recent transactions plus optional loading, error, empty,
and **View All** states.

**Props**

.. list-table::
   :header-rows: 1
   :widths: 25 30 45

   * - Prop
     - Type
     - Description
   * - ``transactions``
     - ``Transaction[]``
     - Source transaction list
   * - ``onViewAll``
     - ``() => void``
     - Optional callback that makes the **View All** button visible
   * - ``isLoading``
     - ``boolean?``
     - Shows *"Loading transactions..."*
   * - ``errorMessage``
     - ``string?``
     - Shows the error instead of transaction rows

**Render states**

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Condition
     - Output
   * - ``isLoading``
     - Loading placeholder
   * - ``errorMessage``
     - Error text from context
   * - ``transactions.length === 0``
     - Empty state: *"No transactions yet. Start by adding one."*
   * - Otherwise
     - ``transactions.slice(0, 5)`` rendered as rows

**Transaction row formatting**

.. code-block:: tsx

   transactions.slice(0, 5).map((transaction) => (
     <View key={String(transaction.id)} style={styles.txRow}>
       {transaction.type === 'income' ? (
         <DollarSign size={18} color="#16a34a" />
       ) : (
         <ArrowDownCircle size={18} color="#dc2626" />
       )}

       <Text>{transaction.description}</Text>
       <Text>{transaction.category} - {transaction.date}</Text>
       <Text>
         {transaction.type === 'income' ? '+' : '-'}
         {formatCurrency(transaction.amount)}
       </Text>
     </View>
   ))

----

Helper Functions - ``Dashboardhelpers.ts``
------------------------------------------

:File: ``src/Pages/Dashboard/Dashboardhelpers.ts``

.. rubric:: formatCurrency

.. code-block:: typescript

   export const formatCurrency = (value: number | string): string =>
     `GBP ${Number(value).toLocaleString()}`;

Formats numeric values for display on dashboard cards and transaction rows.

.. code-block:: typescript

   formatCurrency(1200)      // -> "GBP 1,200"
   formatCurrency("450.5")   // -> "GBP 450.5"

----

.. rubric:: isWide

.. code-block:: typescript

   const { width: screenWidth } = Dimensions.get('window');
   export const isWide = screenWidth >= 768;

Detects wide screens once at module load time.  Dashboard components use this
constant to switch between compact mobile layout and wider card rows.

----

.. rubric:: shadow

.. code-block:: typescript

   export const shadow = (
     color: string,
     offset: { width: number; height: number },
     opacity: number,
     radius: number,
     elevation: number,
   ): object =>
     Platform.select({
       ios: { shadowColor: color, shadowOffset: offset, shadowOpacity: opacity, shadowRadius: radius },
       android: { elevation },
       default: { boxShadow: `0 ${offset.height}px ${radius * 2}px ${color}` } as never,
     }) ?? {};

Returns platform-appropriate shadow syntax for iOS, Android, and web.

----

Type Definitions
----------------

:File: ``src/Pages/Dashboard/Dashboardhelpers.ts``

.. rubric:: Transaction

.. code-block:: typescript

   export type TransactionType = 'income' | 'expense';

   export interface Transaction {
     id: string | number;
     type: TransactionType;
     description?: string;
     category: string;
     date: string;
     amount: number | string;
   }

The Dashboard transaction shape is compatible with the stricter
``FinanceContext`` ``Transaction`` type, while also allowing string amounts for
display-only use.

----

Context Integration
-------------------

:File: ``src/context/FinanceContext.tsx``

The Dashboard relies on context values that are fetched and normalized by the
global provider.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Context operation
     - Dashboard use
   * - ``refreshFinanceData()``
     - Loads transactions and categories, then refreshes gamification
   * - ``refreshGamification()``
     - Loads profile, XP summary, and notifications; runs every 30 seconds
   * - ``updateUserProfile()``
     - Saves profile modal edits through the API with a local fallback
   * - ``markNotificationsRead()``
     - Clears the unread notification count locally
   * - ``addTransaction()``
     - Called indirectly through ``AddTransactionModal``

----

Dependencies
------------

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Package
     - Used for
   * - ``react-native``
     - Layout, animation, modal, scroll, image, input, and status bar components
   * - ``lucide-react-native``
     - Dashboard icons including ``Wallet``, ``Bell``, ``Plus``, ``Trophy``, and transaction icons
   * - ``react-native-root-toast``
     - Toast feedback from context operations triggered by dashboard actions
   * - ``FinanceContext`` (internal)
     - Shared finance, profile, notification, and gamification state

----

.. seealso::

   - :doc:`budget_page` - Budget analytics that uses the same transaction context
   - :doc:`goals_page` - Savings goals and reward-related context behaviour
   - ``src/context/FinanceContext.tsx`` - Global state provider and API integration
