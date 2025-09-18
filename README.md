# Study Assistant

A smart personal assistant for students that helps plan study time, provides reminders, and tracks progress with intelligent recommendations.

## Features

- **Smart Planning**: Automatically plan study time for each subject and topic
- **Smart Reminders**: Get timely reminders for study sessions, meals, sleep, and other activities
- **Exam Mode**: Focus exclusively on subjects you're about to be tested on
- **Progress Tracking**: Track study time and performance with detailed analytics
- **Smart Recommendations**: Get AI-powered advice based on your study patterns

## Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd study-assistant
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**

   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

5. **Set up environment variables**
   Create a `.env` file in the root directory:

   ```
   FLASK_APP=app.py
   FLASK_ENV=development
   SECRET_KEY=your-secret-key-here-change-this-in-production
   DATABASE_URL=sqlite:///study_assistant.db
   ```

6. **Initialize the database**

   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

7. **Run the application**

   ```bash
   python app.py
   ```

   The application will be available at `http://localhost:5000`

## Project Structure

```
study-assistant/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── models.py            # Database models
│   ├── auth/                # Authentication blueprint
│   │   ├── __init__.py
│   │   ├── forms.py         # Authentication forms
│   │   └── routes.py        # Authentication routes
│   ├── main/                # Main application blueprint
│   │   ├── __init__.py
│   │   └── routes.py        # Main application routes
│   └── templates/           # HTML templates
│       ├── base.html        # Base template
│       ├── auth/            # Authentication templates
│       └── main/            # Main application templates
├── config.py                # Configuration settings
├── app.py                   # Application entry point
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Usage

1. **Register an account** or **login** to access the dashboard
2. **Add subjects** and break them down into topics/modules
3. **Set daily study time** goals for each subject
4. **Get automatic reminders** for study sessions and daily activities
5. **Track your progress** and receive personalized recommendations
6. **Use Exam Mode** when preparing for specific tests

## Database Models

- **User**: User accounts with authentication
- **Subject**: Study subjects (Math, Science, etc.)
- **Topic**: Individual topics within subjects
- **StudySession**: Recorded study sessions with timing
- **ExamMode**: Special exam preparation mode

## Technologies Used

- **Backend**: Flask (Python web framework)
- **Database**: SQLAlchemy (ORM) with SQLite
- **Authentication**: Flask-Login
- **Forms**: Flask-WTF with WTForms
- **Frontend**: Bootstrap 5 with Font Awesome icons
- **Database Migrations**: Flask-Migrate

## Development

To run in development mode:

```bash
export FLASK_ENV=development
python app.py
```

To create a new database migration:

```bash
flask db migrate -m "Description of changes"
flask db upgrade
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.
