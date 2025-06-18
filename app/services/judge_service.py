import os
import subprocess
import threading
import time
import psutil


def _get_test_cases(test_cases_dir):
    # 获取所有测试点文件夹
    case_dirs = [d for d in os.listdir(test_cases_dir)
                 if os.path.isdir(os.path.join(test_cases_dir, d))]

    test_cases = []
    for case_dir in sorted(case_dirs, key=lambda x: int(x)):
        case_path = os.path.join(test_cases_dir, case_dir)
        input_files = [f for f in os.listdir(case_path) if f.endswith('.in')]

        for input_file in input_files:
            base_name = input_file[:-3]
            output_file = base_name + '.out'

            if os.path.exists(os.path.join(case_path, output_file)):
                test_cases.append({
                    'input': os.path.join(case_path, input_file),
                    'output': os.path.join(case_path, output_file),
                    'case_id': f"{case_dir}_{base_name}"
                })

    return test_cases


def _compare_output(actual, expected):
    # 简单的逐行比较，可以根据需要增强（如忽略空格、大小写等）
    actual_lines = actual.splitlines()
    expected_lines = expected.splitlines()

    if len(actual_lines) != len(expected_lines):
        return False

    for a, e in zip(actual_lines, expected_lines):
        if a.strip() != e.strip():
            return False

    return True


def _run_test_case(command, input_file, output_file, time_limit, memory_limit):
    # 读取输入和预期输出
    with open(input_file, 'r') as f:
        input_data = f.read()

    with open(output_file, 'r') as f:
        expected_output = f.read().strip()

    # 启动进程
    start_time = time.time()
    max_memory = 0
    memory_monitor_running = True

    try:
        # 使用psutil来更好地控制子进程
        process = psutil.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,  # 必须设置为False才能准确监控目标进程
            text=True
        )

        # 内存监控函数
        def monitor_memory():
            nonlocal max_memory
            while memory_monitor_running:
                try:
                    # 获取进程及其所有子进程的内存使用
                    mem = process.memory_info().rss
                    for child in process.children(recursive=True):
                        try:
                            mem += child.memory_info().rss
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass

                    if mem > max_memory:
                        max_memory = mem

                    # 控制采样频率
                    time.sleep(0.01)  # 10ms采样间隔
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    break

        # 启动内存监控线程
        monitor_thread = threading.Thread(target=monitor_memory)
        monitor_thread.daemon = True
        monitor_thread.start()

        try:
            # 发送输入数据
            stdout, stderr = process.communicate(
                input=input_data,
                timeout=time_limit
            )

            # 计算执行时间
            execution_time = (time.time() - start_time) * 1000  # 毫秒

            # 停止内存监控
            memory_monitor_running = False
            monitor_thread.join(timeout=0.1)

            # 检查运行结果
            if process.returncode != 0:
                if "MemoryError" in stderr:
                    return {
                        'status': 'Memory Limit Exceeded',
                        'execution_time': execution_time,
                        'memory_used': max_memory / (1024 * 1024),  # MB
                        'case_id': os.path.basename(input_file)[:-3]
                    }
                else:
                    return {
                        'status': 'Runtime Error',
                        'message': stderr,
                        'execution_time': execution_time,
                        'memory_used': max_memory / (1024 * 1024),  # MB
                        'case_id': os.path.basename(input_file)[:-3]
                    }

            if execution_time > time_limit :  # 比较毫秒
                return {
                    'status': 'Time Limit Exceeded',
                    'execution_time': execution_time,
                    'memory_used': max_memory / (1024 * 1024),  # MB
                    'case_id': os.path.basename(input_file)[:-3]
                }

            if max_memory > memory_limit:
                return {
                    'status': 'Memory Limit Exceeded',
                    'execution_time': execution_time,
                    'memory_used': max_memory / (1024 * 1024),  # MB
                    'case_id': os.path.basename(input_file)[:-3]
                }

            # 比较输出
            if _compare_output(stdout.strip(), expected_output):
                return {
                    'status': 'Accepted',
                    'execution_time': execution_time,
                    'memory_used': max_memory / (1024 * 1024),  # MB
                    'case_id': os.path.basename(input_file)[:-3]
                }
            else:
                return {
                    'status': 'Wrong Answer',
                    'expected': expected_output,
                    'actual': stdout.strip(),
                    'execution_time': execution_time,
                    'memory_used': max_memory / (1024 * 1024),  # MB
                    'case_id': os.path.basename(input_file)[:-3]
                }

        except subprocess.TimeoutExpired:
            memory_monitor_running = False
            process.kill()
            monitor_thread.join(timeout=0.1)
            return {
                'status': 'Time Limit Exceeded',
                'execution_time': time_limit,
                'memory_used': max_memory / (1024 * 1024),  # MB
                'case_id': os.path.basename(input_file)[:-3]
            }

    except Exception as e:
        memory_monitor_running = False
        if 'monitor_thread' in locals():
            monitor_thread.join(timeout=0.1)
        return {
            'status': 'System Error',
            'message': str(e),
            'case_id': os.path.basename(input_file)[:-3]
        }


def _judge_cpp(code, test_cases_dir, time_limit, memory_limit):
    import tempfile
    import uuid

    # 创建唯一临时文件名
    temp_dir = tempfile.gettempdir()
    unique_id = str(uuid.uuid4())[:8]
    source_file = os.path.join(temp_dir, f"temp_{unique_id}.cpp")
    executable = os.path.join(temp_dir, f"temp_{unique_id}.exe" if os.name == 'nt' else f"temp_{unique_id}")

    try:
        # 保存代码到临时文件
        with open(source_file, 'w', encoding='utf-8') as f:
            f.write(code)

        # 编译C++代码
        compile_result = subprocess.run(
            ["g++", source_file, "-o", executable, "-O2", "-std=c++11"],
            stderr=subprocess.PIPE,
            cwd=temp_dir  # 在临时目录中编译
        )

        if compile_result.returncode != 0:
            return {
                "status": "Compile Error",
                "message": compile_result.stderr.decode('utf-8')
            }

        # 确保可执行文件存在
        if not os.path.exists(executable):
            return {
                "status": "System Error",
                "message": "可执行文件未生成"
            }

        # 遍历测试用例
        test_cases = _get_test_cases(test_cases_dir)
        results = []

        for case in test_cases:
            result = _run_test_case(
                executable,
                case['input'],
                case['output'],
                time_limit,
                memory_limit
            )
            results.append(result)

            if result['status'] != 'Accepted':
                break

        return {
            "status": results[-1]['status'] if results else 'No Test Cases',
            "details": results,
            "passed": sum(1 for r in results if r['status'] == 'Accepted'),
            "total": len(results)
        }

    finally:
        # 确保清理临时文件
        try:
            if os.path.exists(source_file):
                os.remove(source_file)
            if os.path.exists(executable):
                os.remove(executable)
        except Exception as e:
            print(f"清理临时文件时出错: {str(e)}")
