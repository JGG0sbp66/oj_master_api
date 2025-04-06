# run.py
from app import create_app

app = create_app()
app.json.ensure_ascii = False

# 添加调试输出
print("当前配置:")
print(f"SQLALCHEMY_DATABASE_URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
print(f"所有配置项: {app.config}")

if __name__ == '__main__':
    app.run(debug=True)