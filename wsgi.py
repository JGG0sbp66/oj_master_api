from app import create_app

app = create_app()
app.json.ensure_ascii = False
app.config.update(DEBUG=False)  # 强制关闭调试模式
