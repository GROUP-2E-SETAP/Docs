Notification Cron
=========================================

A scheduled job that runs daily at 9:00 AM and emails each user their unread
notifications. After sending, all notified notifications are marked as read
in MongoDB so they are not sent again.

---------------

Schedule
--------

.. code-block:: javascript

   cron.schedule("0 9 * * *", runJob);

Runs every day at **09:00** using ``node-cron``. The cron expression
``0 9 * * *`` means: minute 0, hour 9, every day, every month, every weekday.

-------------

Email Transport
---------------

Emails are sent via ``nodemailer`` using the credentials from the application
config. The service defaults to Gmail if ``EMAIL_SERVICE`` is not set.

.. code-block:: javascript

   const transporter = nodemailer.createTransport({
     service: config.EMAIL_SERVICE || "gmail",
     auth: {
       user: config.EMAIL_USER,
       pass: config.EMAIL_PASSWORD,
     },
   });

---------------

``getAllUserId()``
------------------

Fetches ``id`` and ``email`` for all users with ``role = 'user'`` from
PostgreSQL. Returns an empty array on error so the job can exit cleanly
without crashing.

.. code-block:: javascript

   async function getAllUserId() {
     try {
       const get = await sql`
         SELECT id, email FROM users WHERE role = 'user'
       `;
       return get;
     } catch (error) {
       console.error(`Error fetching data from database : Notification Cron error`);
       return [];
     }
   }

-------------------

``runJob()``
------------

The main job function. For each user it fetches unread notifications, builds
an HTML email listing them, sends the email, then bulk-marks all sent
notifications as read in MongoDB.

.. code-block:: javascript

   async function runJob() {
     try {
       const users = await getAllUserId();
       if (!users.length) return;

       for (const user of users) {
         const unread = await getNotificationsByUserId(user.id);
         if (!unread.length) continue;

         const notificationList = unread
           .map(n => `<li><strong>${n.type}</strong>: ${n.message}</li>`)
           .join("");

         await transporter.sendMail({
           from:    `"SETAP Finance" <${config.EMAIL_USER}>`,
           to:      user.email,
           subject: "Your Notifications - SETAP Finance",
           html:    `<ul>${notificationList}</ul>`,
         });

         const db = getNoSql();
         await db.collection(COLLECTION).updateMany(
           { _id: { $in: unread.map(n => n._id) } },
           { $set: { isRead: true } }
         );
       }
     } catch (error) {
       console.error(`Error running cron job : notification Cron Error`, error);
     }
   }

**Job steps per user:**

1. Fetch all unread notifications from MongoDB via ``getNotificationsByUserId``
2. Skip the user if there are no unread notifications
3. Build an HTML list of notification type and message pairs
4. Send the email via ``nodemailer``
5. Bulk update all sent notifications to ``isRead: true`` using ``updateMany``

