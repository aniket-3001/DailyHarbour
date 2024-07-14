---

# Ecommerce Application

This repository contains an end-to-end ecommerce application developed using Python and Flask for the backend, and vanilla HTML, CSS, and JavaScript for the frontend. The application focuses on robust DBMS and SQL integration, ensuring a high-performing and scalable database through the use of query optimization and transaction control principles.

## Features

- **Backend**: Developed using Flask, a lightweight WSGI web application framework in Python.
- **Frontend**: Created with vanilla HTML, CSS, and JavaScript to ensure a responsive and user-friendly interface.
- **AJAX**: Implemented for seamless asynchronous communication between the frontend and backend.
- **Database Management**: Utilized SQL for robust database integration, with a focus on query optimization and transaction control to maintain performance and scalability.

## Installation

### Prerequisites

- Python 3.x
- Flask
- SQLAlchemy
- A SQL database (e.g., MySQL, PostgreSQL)

### Setting Up the Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

### Database Setup

1. Create a SQL database.
2. Update the database configuration in the `app.py` file.

## Running the Application

```bash
python app.py
```

The application will be available at `http://127.0.0.1:5000`.

## Project Structure

```
DailyHarbour/
│   ├── __init__.py
│   ├── app.py
│   ├── static/
│   └── templates/
```

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

---
