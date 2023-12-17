===============
Privacy Policy
===============

:Date: 2023-12-17

Introduction
============

This Privacy Policy describes how we collect, use, and handle your personal information when you use |spotted_dmi_bot|_.

Information We Collect
======================

Each user is assigned a unique |user_id|_ by telegram, which corresponds to their |chat_id|_.
It can be easily obtained by any client or bot and is not to be considered sensitive information.
In fact, it is necessary for the bot to send the user messages, as shown in the prototype of |send_message|_.

How We Use Your Information
===========================

When a spot or report is submitted, the |user_id|_ is stored in the database.
This is done for the following reasons:

- To notify the user of the outcome of the admin's judgment on your spot.
- To respond to user inquiries and provide support.
- To prevent spamming of spots (each user can have only one spot in pending at any given time).
- To allow the user to cancel a spot still pending, before receiving the final judgment of the admins.
- To ban a user.

To see more in detail what tables require the |user_id|_, please refer to the :ref:`Database Schema <dbschema>` section.

Are spots and reports anonymous to the admins?
==============================================

**Yes**. 
While the bot has to store the |user_id|_ in order to function, the information is not shared with the admins.
Spot and reports are presented to them without any information about the original sender.

Even when replying to a spot or banning an user, the admins are not shown any information that could be used to identify the user.

Are spots anonymous to the other users?
=======================================

**Yes**.
All normal users with access to the channel will see the spots as sent by the bot.
No information about the original sender is available to them.

How long we retain your information for
=======================================

The bot only stores the |user_id|_ as long as a spot is pending.
Upon admin's approval or rejection, the record is expunged from the database.
This also happens when the user **/cancel** a spot still pending.

Reports are a different matter.
Again, the |user_id|_ is stored in order to prevent miss-use and to allow communication between the admins and the user.
But there is currently no system in place to delete reports from the database.

Data Security
=============

All data is stored on the server hosting |spotted_dmi_bot|_.
Access to the server is restricted to a small subset of the developers of the bot.
All of them are trusted in not accessing the data and keeping it safe and confidential.
In any case, the |user_id|_ alone provides very little information, since the content of the actual spot is not stored in the database.

Sharing of Information
======================

We do not sell, trade, or otherwise transfer your personal information to outside parties. 

Updates to This Privacy Policy
==============================

We may update this Privacy Policy to reflect changes in our practices. We will notify users of any material changes by posting the updated policy on our website or through other communication channels.

Contact Us
==========

If you have any questions or concerns about this Privacy Policy, please contact us by opening an issue on GitHub.

Acceptance of Terms
===================

By using |spotted_dmi_bot|_, you signify your acceptance of this Privacy Policy. 
If you do not agree to this policy, please do not use the bot in order to send spots.

This Privacy Policy is effective as of the date stated at the beginning of the document and may be subject to updates. Please review this policy periodically for any changes.

.. |spotted_dmi_bot| replace:: @Spotted_DMI_bot
.. |user_id| replace:: **User.id**
.. |chat_id| replace:: **Chat.id**
.. |send_message| replace:: *sendMessage()*

.. _spotted_dmi_bot: https://t.me/Spotted_DMI_bot
.. _user_id: https://core.telegram.org/bots/api#user
.. _chat_id: https://core.telegram.org/bots/api#chat
.. _send_message: https://core.telegram.org/bots/api#sendmessage
