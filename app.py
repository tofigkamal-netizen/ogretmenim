import os
from datetime import datetime
from functools import wraps

from flask import (Flask, render_template, request, redirect, url_for,
                    session, flash, jsonify, abort)
from werkzeug.utils import secure_filename

from models import db, User, Exam, Question, Attempt, Answer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads', 'questions')
ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = '1234'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-change-me'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'exam.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db.init_app(app)


# ---------- helpers ----------

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT


def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if 'role' not in session:
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                abort(403)
            return f(*args, **kwargs)
        return wrapped
    return decorator


def overall_percentage_for_student(student_id):
    attempts = Attempt.query.filter_by(student_id=student_id).filter(
        Attempt.status.in_(['completed', 'auto_submitted'])).all()
    if not attempts:
        return 0.0
    return round(sum(a.percentage for a in attempts) / len(attempts), 2)


# ---------- public / login ----------

@app.route('/')
def index():
    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))
    if session.get('role') == 'student':
        return redirect(url_for('student_dashboard'))
    if session.get('role') == 'parent':
        return redirect(url_for('parent_dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Shared login page. Type of account picked at the top right (admin / şagird-valideyn),
    matching the app's original 'admin seç / şagird seç' switch."""
    mode = request.values.get('mode', 'student')  # 'admin' or 'student' (student|parent share the form)

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if mode == 'admin':
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                session.clear()
                session['role'] = 'admin'
                session['username'] = 'admin'
                return redirect(url_for('admin_dashboard'))
            flash('Admin istifadəçi adı və ya şifrə yanlışdır.', 'error')
            return redirect(url_for('login', mode='admin'))
        else:
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password) and user.role in ('student', 'parent'):
                session.clear()
                session['role'] = user.role
                session['user_id'] = user.id
                session['username'] = user.username
                session['full_name'] = user.full_name
                if user.role == 'student':
                    return redirect(url_for('student_dashboard'))
                return redirect(url_for('parent_dashboard'))
            flash('İstifadəçi adı və ya şifrə yanlışdır.', 'error')
            return redirect(url_for('login', mode=mode))

    return render_template('login.html', mode=mode)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ---------- ADMIN ----------

@app.route('/admin')
@login_required('admin')
def admin_dashboard():
    exams = Exam.query.order_by(Exam.id.desc()).all()
    students = User.query.filter_by(role='student').all()
    parents = User.query.filter_by(role='parent').all()
    return render_template('admin_dashboard.html', exams=exams, students=students, parents=parents, now=datetime.utcnow())


@app.route('/admin/exam/new', methods=['GET', 'POST'])
@login_required('admin')
def admin_exam_new():
    if request.method == 'POST':
        title = request.form.get('title', '').strip() or 'Adsız imtahan'
        subject = request.form.get('subject', '').strip() or 'Riyaziyyat'
        question_count = int(request.form.get('question_count') or 5)
        time_limit_raw = request.form.get('time_limit', '10')
        time_limit = 0 if time_limit_raw == 'limitsiz' else int(time_limit_raw or 10)
        start_time_raw = request.form.get('start_time')
        start_time = datetime.fromisoformat(start_time_raw) if start_time_raw else datetime.utcnow()

        exam = Exam(title=title, subject=subject, question_count=question_count,
                    time_limit_minutes=time_limit, start_time=start_time)
        db.session.add(exam)
        db.session.flush()  # get exam.id

        for i in range(1, question_count + 1):
            text = request.form.get(f'q{i}_text', '').strip()
            if not text:
                continue
            correct = request.form.get(f'q{i}_correct', 'A')
            image_file = request.files.get(f'q{i}_image')
            image_filename = None
            if image_file and image_file.filename and allowed_file(image_file.filename):
                fname = secure_filename(f"exam_new_q{i}_{image_file.filename}")
                image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
                image_filename = fname

            q = Question(
                exam_id=exam.id, order=i, text=text, image_filename=image_filename,
                option_a=request.form.get(f'q{i}_a', ''),
                option_b=request.form.get(f'q{i}_b', ''),
                option_c=request.form.get(f'q{i}_c', ''),
                option_d=request.form.get(f'q{i}_d', ''),
                option_e=request.form.get(f'q{i}_e', ''),
                correct_option=correct,
            )
            db.session.add(q)

        db.session.commit()
        flash(f'"{title}" imtahanı yaradıldı.', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin_exam_new.html')


@app.route('/admin/exam/<int:exam_id>/delete', methods=['POST'])
@login_required('admin')
def admin_exam_delete(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    db.session.delete(exam)
    db.session.commit()
    flash('İmtahan silindi.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/users/new', methods=['GET', 'POST'])
@login_required('admin')
def admin_users_new():
    if request.method == 'POST':
        student_username = request.form.get('student_username', '').strip()
        student_password = request.form.get('student_password', '').strip()
        student_name = request.form.get('student_name', '').strip()
        parent_username = request.form.get('parent_username', '').strip()
        parent_password = request.form.get('parent_password', '').strip()
        parent_name = request.form.get('parent_name', '').strip()

        if not all([student_username, student_password, student_name,
                    parent_username, parent_password, parent_name]):
            flash('Bütün xanaları doldurun.', 'error')
            return redirect(url_for('admin_users_new'))

        if User.query.filter_by(username=student_username).first() or \
           User.query.filter_by(username=parent_username).first():
            flash('Bu istifadəçi adı artıq mövcuddur.', 'error')
            return redirect(url_for('admin_users_new'))

        parent = User(username=parent_username, full_name=parent_name, role='parent')
        parent.set_password(parent_password)
        db.session.add(parent)
        db.session.flush()

        student = User(username=student_username, full_name=student_name, role='student',
                        parent_id=parent.id)
        student.set_password(student_password)
        db.session.add(student)

        db.session.commit()
        flash(f'{student_name} (şagird) və {parent_name} (valideyn) hesabları yaradıldı.', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin_users_new.html')


@app.route('/admin/exam/<int:exam_id>/results')
@login_required('admin')
def admin_exam_results(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    attempts = Attempt.query.filter_by(exam_id=exam_id).order_by(Attempt.id.desc()).all()
    return render_template('admin_exam_results.html', exam=exam, attempts=attempts)


# ---------- STUDENT ----------

@app.route('/student')
@login_required('student')
def student_dashboard():
    student_id = session['user_id']
    exams = Exam.query.order_by(Exam.start_time.desc()).all()
    attempts = {a.exam_id: a for a in Attempt.query.filter_by(student_id=student_id).all()}
    overall = overall_percentage_for_student(student_id)
    return render_template('student_dashboard.html', exams=exams, attempts=attempts,
                            overall=overall, now=datetime.utcnow())


@app.route('/student/exam/<int:exam_id>/warning')
@login_required('student')
def student_exam_warning(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    if not exam.is_open():
        flash('Bu imtahan hələ başlamayıb.', 'error')
        return redirect(url_for('student_dashboard'))
    existing = Attempt.query.filter_by(exam_id=exam_id, student_id=session['user_id']).first()
    if existing:
        return redirect(url_for('student_exam_result', attempt_id=existing.id))
    return render_template('student_exam_warning.html', exam=exam)


@app.route('/student/exam/<int:exam_id>/start', methods=['POST'])
@login_required('student')
def student_exam_start(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    existing = Attempt.query.filter_by(exam_id=exam_id, student_id=session['user_id']).first()
    if existing:
        return redirect(url_for('student_exam_take', attempt_id=existing.id))
    attempt = Attempt(exam_id=exam_id, student_id=session['user_id'], total=len(exam.questions))
    db.session.add(attempt)
    db.session.commit()
    return redirect(url_for('student_exam_take', attempt_id=attempt.id))


@app.route('/student/attempt/<int:attempt_id>/take')
@login_required('student')
def student_exam_take(attempt_id):
    attempt = Attempt.query.get_or_404(attempt_id)
    if attempt.student_id != session['user_id']:
        abort(403)
    if attempt.status != 'in_progress':
        return redirect(url_for('student_exam_result', attempt_id=attempt.id))
    exam = attempt.exam
    elapsed_seconds = (datetime.utcnow() - attempt.start_time).total_seconds()
    remaining_seconds = None
    if exam.time_limit_minutes and exam.time_limit_minutes > 0:
        remaining_seconds = max(0, exam.time_limit_minutes * 60 - int(elapsed_seconds))
        if remaining_seconds <= 0:
            return redirect(url_for('student_exam_submit_auto', attempt_id=attempt.id))
    return render_template('student_exam_take.html', exam=exam, attempt=attempt,
                            remaining_seconds=remaining_seconds)


@app.route('/student/attempt/<int:attempt_id>/submit', methods=['POST'])
@login_required('student')
def student_exam_submit(attempt_id):
    return _grade_and_finish(attempt_id, status='completed')


@app.route('/student/attempt/<int:attempt_id>/auto_submit', methods=['GET', 'POST'])
@login_required('student')
def student_exam_submit_auto(attempt_id):
    return _grade_and_finish(attempt_id, status='auto_submitted')


def _grade_and_finish(attempt_id, status):
    attempt = Attempt.query.get_or_404(attempt_id)
    if attempt.student_id != session['user_id']:
        abort(403)
    if attempt.status == 'in_progress':
        exam = attempt.exam
        correct = 0
        for q in exam.questions:
            selected = request.form.get(f'answer_{q.id}')
            is_correct = bool(selected) and selected == q.correct_option
            if is_correct:
                correct += 1
            db.session.add(Answer(attempt_id=attempt.id, question_id=q.id,
                                   selected_option=selected, is_correct=is_correct))
        total = len(exam.questions)
        attempt.total = total
        attempt.correct_count = correct
        attempt.wrong_count = total - correct
        attempt.percentage = round((correct / total) * 100, 2) if total else 0.0
        attempt.status = status
        attempt.end_time = datetime.utcnow()
        db.session.commit()

    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'fetch':
        return jsonify({'ok': True, 'redirect': url_for('student_exam_result', attempt_id=attempt.id)})
    return redirect(url_for('student_exam_result', attempt_id=attempt.id))


@app.route('/student/attempt/<int:attempt_id>/result')
@login_required('student')
def student_exam_result(attempt_id):
    attempt = Attempt.query.get_or_404(attempt_id)
    if attempt.student_id != session['user_id'] and session.get('role') != 'parent':
        abort(403)
    return render_template('student_exam_result.html', attempt=attempt)


# ---------- PARENT ----------

@app.route('/parent')
@login_required('parent')
def parent_dashboard():
    parent_id = session['user_id']
    children = User.query.filter_by(parent_id=parent_id, role='student').all()
    data = []
    for child in children:
        attempts = Attempt.query.filter_by(student_id=child.id).filter(
            Attempt.status.in_(['completed', 'auto_submitted'])).order_by(Attempt.id.desc()).all()
        overall = overall_percentage_for_student(child.id)
        data.append({'child': child, 'attempts': attempts, 'overall': overall})
    return render_template('parent_dashboard.html', data=data)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
