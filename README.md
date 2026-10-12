# DB Lab 2 - Login application (Part I)

Python / Flask back end, plain HTML front end, MySQL database `registration`.

## How to run

1. Install Python 3 and MySQL.
2. Install the libraries: `pip install -r requirements.txt`
3. Create the database: run `database/schema.sql` in MySQL
   (for example `mysql -u root -p < database/schema.sql`).
4. Copy `.env.example` to `.env` and fill in your MySQL password and a random `SECRET_KEY`.
5. Start the server: `python app.py`
6. Open http://127.0.0.1:5000
