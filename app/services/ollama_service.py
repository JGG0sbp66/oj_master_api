import requests
import json

# 基础初始化设置
base_url = "http://192.168.13.191:11434/api"
headers = {"Content-Type": "application/json"}


def generate_completion_stream(prompt, model="gemma3:27b"):
    """
    流式生成AI回复（生成器函数）
    """
    url = f"{base_url}/generate"
    data = {
        "model": model,
        "prompt": prompt,
        "stream": True,
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=data,
            stream=True,
            timeout=(10, 300)  # 连接超时10秒，读取超时5分钟
        )
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                try:
                    chunk = json.loads(line.decode('utf-8'))
                    if 'response' in chunk:
                        # SSE格式：data: {json}\n\n
                        yield f"data: {json.dumps({'text': chunk['response']})}\n\n"
                    if chunk.get('done'):
                        break
                except json.JSONDecodeError:
                    continue

    except requests.exceptions.RequestException as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
