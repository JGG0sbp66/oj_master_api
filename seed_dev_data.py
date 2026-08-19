# -*- coding: utf-8 -*-
"""开发环境种子数据：管理员账号、测试题目（含评测用例）、测试竞赛。可重复运行（已存在则跳过）。"""
import os
import bcrypt
from datetime import datetime, timedelta

from app import create_app
from app.extensions import db
from app.models import User, QuestionsData, RaceData

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TESTCASE_ROOT = os.path.join(BASE_DIR, 'data', 'test_case', 'problems')

app = create_app()


def hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def write_testcases(qid: int, cases: list[tuple[str, str]]):
    for i, (inp, outp) in enumerate(cases, start=1):
        case_dir = os.path.join(TESTCASE_ROOT, f'testcases_{qid}', str(i))
        os.makedirs(case_dir, exist_ok=True)
        with open(os.path.join(case_dir, f'{i}.in'), 'w', encoding='utf-8') as f:
            f.write(inp + '\n')
        with open(os.path.join(case_dir, f'{i}.out'), 'w', encoding='utf-8') as f:
            f.write(outp + '\n')


with app.app_context():
    # ---------- 用户 ----------
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            password=hash_pw('admin123'),
            email='admin@ojmaster.local',
            role='admin',
            description='系统管理员',
            rating=2000,
        )
        db.session.add(admin)
        print('[+] 创建管理员 admin / admin123')
    else:
        print('[=] 管理员 admin 已存在，跳过')

    test_user = User.query.filter_by(username='test').first()
    if not test_user:
        test_user = User(
            username='test',
            password=hash_pw('test123'),
            email='test@ojmaster.local',
            role='user',
            rating=1500,
        )
        db.session.add(test_user)
        print('[+] 创建测试用户 test / test123')
    else:
        print('[=] 测试用户 test 已存在，跳过')
    db.session.flush()

    # ---------- 题目 ----------
    questions_seed = [
        {
            'topic': '入门',
            'question': {
                'title': 'A+B 问题',
                'description': '输入两个整数 a 和 b，输出它们的和。',
                'time_limit': 1000,
                'memory_limit': 128,
                'input_format': '一行，两个整数 a 和 b，空格分隔。',
                'output_format': '一个整数，表示 a + b 的结果。',
                'constraints': ['-10^9 ≤ a, b ≤ 10^9'],
                'examples': [{'input': '1 2', 'output': '3'}],
                'submit_num': 0,
                'solve_num': 0,
            },
            'cases': [('1 2', '3'), ('10 20', '30'), ('-5 5', '0')],
        },
        {
            'topic': '入门',
            'question': {
                'title': '判断回文数',
                'description': '给定一个整数，判断它是否是回文数（正序和倒序读相同）。',
                'time_limit': 1000,
                'memory_limit': 128,
                'input_format': '一行，一个整数 n。',
                'output_format': '如果是回文数输出 Yes，否则输出 No。',
                'constraints': ['0 ≤ n ≤ 10^9'],
                'examples': [{'input': '121', 'output': 'Yes'}],
                'submit_num': 0,
                'solve_num': 0,
            },
            'cases': [('121', 'Yes'), ('123', 'No'), ('1221', 'Yes')],
        },
        {
            'topic': '普及',
            'question': {
                'title': '斐波那契数列',
                'description': '斐波那契数列定义为 F(1)=1, F(2)=1, F(n)=F(n-1)+F(n-2)。给定 n，输出 F(n)。',
                'time_limit': 1000,
                'memory_limit': 128,
                'input_format': '一行，一个整数 n。',
                'output_format': '一个整数，表示 F(n)。',
                'constraints': ['1 ≤ n ≤ 40'],
                'examples': [{'input': '5', 'output': '5'}],
                'submit_num': 0,
                'solve_num': 0,
            },
            'cases': [('5', '5'), ('10', '55'), ('1', '1')],
        },
        {
            'topic': '提高',
            'question': {
                'title': '最大子数组和',
                'description': '给定一个整数数组，找到具有最大和的连续子数组，输出其最大和。',
                'time_limit': 1000,
                'memory_limit': 256,
                'input_format': '一行，若干个空格分隔的整数。',
                'output_format': '一个整数，表示最大子数组和。',
                'constraints': ['1 ≤ 数组长度 ≤ 10^5', '-10^4 ≤ 元素值 ≤ 10^4'],
                'examples': [{'input': '1 -2 3 4 -5', 'output': '7'}],
                'submit_num': 0,
                'solve_num': 0,
            },
            'cases': [('1 -2 3 4 -5', '7'), ('-1 -2 -3', '-1'), ('1 2 3', '6')],
        },
    ]

    qids = {}
    for seed in questions_seed:
        title = seed['question']['title']
        existing = None
        for q in QuestionsData.query.all():
            if q.question and q.question.get('title') == title:
                existing = q
                break
        if existing:
            print(f'[=] 题目「{title}」已存在 (uid={existing.uid})，跳过')
            qids[title] = existing.uid
            continue
        q = QuestionsData(topic=seed['topic'], question=seed['question'], is_contest_question=False)
        db.session.add(q)
        db.session.flush()
        write_testcases(q.uid, seed['cases'])
        qids[title] = q.uid
        print(f'[+] 创建题目「{title}」uid={q.uid}，含 {len(seed["cases"])} 组评测用例')

    # ---------- 竞赛 ----------
    def fmt_duration(seconds: int) -> str:
        h, rem = divmod(seconds, 3600)
        m, s = divmod(rem, 60)
        return f'{h:02d}小时{m:02d}分{s:02d}秒'

    now = datetime.now()
    races_seed = [
        {
            'title': '新手入门赛',
            'logos': ['OJMaster'],
            'start_time': now - timedelta(hours=1),
            'end_time': now + timedelta(days=1),
            'tags': [{'name': '进行中', 'type': 'success'}],
            'problems_list': [qids['A+B 问题'], qids['判断回文数'], qids['斐波那契数列']],
            'status': 'running',
        },
        {
            'title': '算法进阶挑战赛',
            'logos': ['OJMaster', 'ACM'],
            'start_time': now + timedelta(days=3),
            'end_time': now + timedelta(days=3, hours=4),
            'tags': [{'name': '未开始', 'type': 'pending'}],
            'problems_list': [qids['斐波那契数列'], qids['最大子数组和']],
            'status': 'upcoming',
        },
        {
            'title': '往期练习赛（已结束）',
            'logos': ['OJMaster'],
            'start_time': now - timedelta(days=7),
            'end_time': now - timedelta(days=7) + timedelta(hours=3),
            'tags': [{'name': '已结束', 'type': 'info'}],
            'problems_list': [qids['A+B 问题'], qids['最大子数组和']],
            'status': 'ended',
        },
    ]

    for seed in races_seed:
        if RaceData.query.filter_by(title=seed['title']).first():
            print(f'[=] 竞赛「{seed["title"]}」已存在，跳过')
            continue
        duration = fmt_duration(int((seed['end_time'] - seed['start_time']).total_seconds()))
        race = RaceData(
            title=seed['title'],
            logos=seed['logos'],
            start_time=seed['start_time'],
            end_time=seed['end_time'],
            duration=duration,
            tags=seed['tags'],
            problems_list=seed['problems_list'],
            user_list=[admin.uid, test_user.uid],
            status=seed['status'],
        )
        db.session.add(race)
        db.session.flush()
        print(f'[+] 创建竞赛「{seed["title"]}」uid={race.uid}，状态={seed["status"]}，题目={seed["problems_list"]}')

    db.session.commit()
    print('\n[√] 种子数据写入完成')
