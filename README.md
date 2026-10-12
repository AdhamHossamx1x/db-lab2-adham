    
Names:
            1.Adham Hossam----2304036
            2.Alaa Abdullah---2304054
===============================================================================================
## Answers of the question
==========================
(a) Why do UPDATE and DELETE contain `AND user_id = ?`, and what changes if you remove it?**
The id of a to-do comes from the browser, so anybody can send somebody else's number. Adding `AND user_id = ?` (the id of the logged-in user, taken from the session) makes the statement change zero rows when the to-do is not yours. If we remove it, any logged-in user could edit or delete the to-dos of other users.

(b) What happens if you insert a to-do for a `user_id` that does not exist, and which constraint of the lecture is that?**
MySQL rejects the INSERT and returns an error, because `todos.user_id` is a foreign key that must match an existing `users.user_id`. This is the foreign key constraint, which enforces referential integrity.

(c) Why do you store a hash and not the password?**
If the database is leaked, the real passwords are not exposed, because a hash cannot be reversed. bcrypt adds a random salt, so two equal passwords give different hashes, and it is slow on purpose, which makes guessing passwords expensive.

(d) The `name` column is NOT NULL: why did you still need your own check for an empty name?**
NOT NULL only refuses NULL. An empty text `''` is a value, so MySQL accepts it. Only our own check, in the browser and on the server, can refuse an empty name (after trimming spaces).

