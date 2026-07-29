"""
Demo məlumatları yaradır: 1 valideyn, 1 şagird və 5 sualdan ibarət
"Riyaziyyat" imtahanı (indi başlayıb, 10 dəqiqə davam edir).

İşlətmək üçün:
    python3 seed.py
"""
from datetime import datetime, timedelta

from app import app, db
from models import User, Exam, Question


def run():
    with app.app_context():
        db.create_all()

        if User.query.filter_by(username='nezrin').first():
            print('Demo məlumatlar artıq mövcuddur, seed edilmədi.')
            return

        parent = User(username='ana1', full_name='Aygün Məmmədova', role='parent')
        parent.set_password('1234')
        db.session.add(parent)
        db.session.flush()

        student = User(username='nezrin', full_name='Nəzrin Məmmədova',
                        role='student', parent_id=parent.id)
        student.set_password('1234')
        db.session.add(student)

        exam = Exam(title='Toplama və Çıxma', subject='Riyaziyyat',
                    question_count=5, time_limit_minutes=10,
                    start_time=datetime.utcnow() - timedelta(minutes=1))
        db.session.add(exam)
        db.session.flush()

        questions = [
            ('2 + 2 = ?', dict(A='3', B='4', C='5', D='6', E='7'), 'B'),
            ('7 - 3 = ?', dict(A='2', B='3', C='4', D='5', E='6'), 'C'),
            ('5 x 3 = ?', dict(A='10', B='12', C='14', D='15', E='20'), 'D'),
            ('12 / 4 = ?', dict(A='2', B='3', C='4', D='5', E='6'), 'B'),
            ('9 + 6 = ?', dict(A='13', B='14', C='15', D='16', E='17'), 'C'),
        ]
        for i, (text, opts, correct) in enumerate(questions, start=1):
            db.session.add(Question(
                exam_id=exam.id, order=i, text=text,
                option_a=opts['A'], option_b=opts['B'], option_c=opts['C'],
                option_d=opts['D'], option_e=opts['E'], correct_option=correct,
            ))

        db.session.commit()
        print('Demo hesablar yaradıldı:')
        print('  Admin   -> istifadəçi adı: admin   şifrə: 1234')
        print('  Şagird  -> istifadəçi adı: nezrin  şifrə: 1234')
        print('  Valideyn-> istifadəçi adı: ana1    şifrə: 1234')


if __name__ == '__main__':
    run()
