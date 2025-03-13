from flask import Flask, render_template, request, redirect, url_for, flash ,session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from datetime import datetime, timedelta

# Initialize Flask app
app = Flask(__name__)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Session lasts for 7 days.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SECRET_KEY'] = '17726878'  # Required for session management and flashing messages

# Initialize the database
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Define models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    tasks = db.relationship('Task', backref='user', lazy=True)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), nullable=False)  # e.g., "To-Do", "In Progress", "Completed"
    priority = db.Column(db.String(50), nullable=False)  # e.g., "Low", "Medium", "High"
    deadline = db.Column(db.DateTime, nullable=True)  # DateTime field
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Create the database tables (run this once)
with app.app_context():
    db.create_all()
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('copilot.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            session['username'] = user.username  # Store the username in the session
            session['user_id'] = user.id  # Store user ID in session
            session.permanent = True  # Set the session to be permanent
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists')
        else:
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/terms_privacy')
def terms_privacy():
    return render_template('terms_privacy.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        # Add logic to handle password reset
        flash('Password reset link sent to your email')
    return render_template('forgot_password.html')

@app.route('/dashboard')
def dashboard():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    return render_template('startfor free.html', tasks=tasks)

@app.route('/task/<int:task_id>')
@login_required
def task_detail(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash('You do not have permission to view this task')
        return redirect(url_for('dashboard'))
    return render_template('task_detail.html', task=task)

@app.route('/create_task', methods=['GET', 'POST'])
@login_required
def create_task():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        status = request.form.get('status')
        priority = request.form.get('priority')
        deadline_str = request.form.get('deadline')  # Get deadline as a string
        

        # Convert the deadline string to a datetime object
        try:
            deadline = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M')
        except (ValueError, TypeError):
            flash('Invalid deadline format. Please use YYYY-MM-DDTHH:MM.')
            return redirect(url_for('create_task'))

        # Create a new task
        new_task = Task(
            title=title,
            description=description,
            status=status,
            priority=priority,
            deadline=deadline,  # Use the datetime object
            user_id=current_user.id
        )

        # Add and commit the task to the database
        db.session.add(new_task)
        db.session.commit()

        return redirect(url_for('dashboard'))
    return render_template('create_task.html')
@app.route('/logout')
@login_required
def logout():
    session.pop('username', None)  # Remove username from session
    session.pop('user_id', None)   # Remove user_id from session
    logout_user()
    return redirect(url_for('login'))

# Run the application
if __name__ == '__main__':
    app.run(debug=True)
