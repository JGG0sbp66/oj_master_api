import os
import shutil


def process_test_cases(testcase_dir):
    """
    处理提取的测试用例，验证每个测试点的文件结构
    """
    # 初始化结果字典
    result = {
        'count': 0,
        'files': [],
        'errors': []
    }

    # 遍历测试用例目录
    for testcase_id in os.listdir(testcase_dir):
        testcase_path = os.path.join(testcase_dir, testcase_id)
        if not os.path.isdir(testcase_path):
            continue

        # 检查目录名称是否只包含数字
        if not testcase_id.isdigit():
            result['errors'].append(f'Testcase {testcase_id} 只能以数字命名')
            continue

        # 构造对应的 input 和 output 文件名
        input_file = os.path.join(testcase_path, f'{testcase_id}.in')
        output_file = os.path.join(testcase_path, f'{testcase_id}.out')

        # 检查文件是否存在
        if not os.path.exists(input_file) or not os.path.exists(output_file):
            result['errors'].append(f'Testcase {testcase_id} 缺失 {testcase_id}.in 或者 {testcase_id}.out')
            continue

        # 如果文件存在，增加计数并记录文件名
        result['count'] += 1
        result['files'].append(testcase_id)

    return result

def move_test_cases(testcase_dir, target_dir):
    """
    将处理后的测试用例移动到目标目录
    """
    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)  # 添加exist_ok参数避免目录已存在时报错

    for testcase_id in os.listdir(testcase_dir):
        testcase_path = os.path.join(testcase_dir, testcase_id)
        if os.path.isdir(testcase_path):
            target_path = os.path.join(target_dir, testcase_id)
            if os.path.exists(target_path):  # 如果目标目录已存在，先删除
                shutil.rmtree(target_path)
            shutil.move(testcase_path, target_path)