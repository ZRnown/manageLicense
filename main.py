import sqlite3
import uuid
import datetime
from fastapi import FastAPI, HTTPException, Request, Form, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional

# --- 配置 ---
ADMIN_PASSWORD = "your_secret_password"  # 【重要】请修改这个管理员密码
DB_FILE = "licenses.db"

app = FastAPI()

# --- 数据库初始化 ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # 创建表：密钥、是否已用、绑定的机器码、生成时间、过期时间(NULL代表永久)、备注
    c.execute('''CREATE TABLE IF NOT EXISTS licenses (
                    key_str TEXT PRIMARY KEY,
                    is_used INTEGER DEFAULT 0,
                    hwid TEXT,
                    created_at TEXT,
                    valid_days INTEGER,
                    activated_at TEXT,
                    note TEXT
                )''')
    conn.commit()
    conn.close()

init_db()

# --- 模型定义 ---
class ActivationRequest(BaseModel):
    key: str
    hwid: str

# --- 辅助函数 ---
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# --- 1. 管理后台 (HTML界面) ---
@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request):
    # 简单的内嵌 HTML 界面，方便你操作
    html_content = """
    <html>
    <head>
        <title>软件授权管理系统</title>
        <style>
            body { font-family: sans-serif; max-width: 800px; margin: 20px auto; padding: 20px; }
            .card { border: 1px solid #ddd; padding: 20px; margin-bottom: 20px; border-radius: 8px; }
            input, select, button { padding: 10px; margin: 5px 0; width: 100%; box-sizing: border-box; }
            button { background-color: #007bff; color: white; border: none; cursor: pointer; }
            button:hover { background-color: #0056b3; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            .used { color: red; font-weight: bold; }
            .unused { color: green; font-weight: bold; }
        </style>
    </head>
    <body>
        <h2>🔑 密钥生成中心</h2>

        <div class="card">
            <h3>生成新密钥</h3>
            <form action="/admin/generate" method="post">
                <label>管理员密码:</label>
                <input type="password" name="password" required placeholder="请输入管理员密码">

                <label>生成数量:</label>
                <input type="number" name="count" value="1" min="1" max="100">

                <label>有效期 (天):</label>
                <select name="days">
                    <option value="-1">永久有效</option>
                    <option value="30">30天</option>
                    <option value="365">1年</option>
                    <option value="7">7天试用</option>
                </select>

                <label>备注 (客户名/渠道):</label>
                <input type="text" name="note" placeholder="例如：张三的企业版">

                <button type="submit">生成密钥</button>
            </form>
        </div>

        <div class="card">
            <h3>最近生成的密钥 (最新的20条)</h3>
            <table>
                <tr>
                    <th>密钥 (Key)</th>
                    <th>状态</th>
                    <th>有效期</th>
                    <th>备注</th>
                    <th>绑定机器码</th>
                </tr>
                <!-- 这里由后端填充数据 -->
                {% for lic in licenses %}
                <tr>
                    <td>{{ lic.key_str }}</td>
                    <td class="{{ 'used' if lic.is_used else 'unused' }}">
                        {{ '已激活' if lic.is_used else '未激活' }}
                    </td>
                    <td>{{ '永久' if lic.valid_days == -1 else lic.valid_days ~ ' 天' }}</td>
                    <td>{{ lic.note }}</td>
                    <td style="font-size: 12px; color: #666;">{{ lic.hwid if lic.hwid else '-' }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </body>
    </html>
    """

    conn = get_db_connection()
    # 获取最近20条记录
    cur = conn.cursor()
    cur.execute("SELECT * FROM licenses ORDER BY created_at DESC LIMIT 20")
    rows = cur.fetchall()
    conn.close()

    from jinja2 import Template
    t = Template(html_content)
    return t.render(licenses=rows)

# --- 2. 生成密钥接口 (后台表单提交到这里) ---
@app.post("/admin/generate")
async def generate_license(password: str = Form(...), count: int = Form(...), days: int = Form(...), note: str = Form("")):
    if password != ADMIN_PASSWORD:
        return HTMLResponse(content="<h3>密码错误！</h3><a href='/admin'>返回</a>", status_code=403)

    conn = get_db_connection()
    c = conn.cursor()

    generated_keys = []
    for _ in range(count):
        # 生成格式如: XXXX-XXXX-XXXX-XXXX
        key = str(uuid.uuid4()).upper()
        now = datetime.datetime.now().isoformat()

        c.execute("INSERT INTO licenses (key_str, valid_days, created_at, note) VALUES (?, ?, ?, ?)",
                  (key, days, now, note))
        generated_keys.append(key)

    conn.commit()
    conn.close()

    # 生成完跳回首页
    return HTMLResponse(content=f"""
        <h3>成功生成 {count} 个密钥！</h3>
        <textarea style='width:100%; height:200px;'>{chr(10).join(generated_keys)}</textarea>
        <br><br>
        <a href='/admin'>返回管理页</a>
    """)

# --- 3. 客户端激活接口 ---
@app.post("/api/activate")
async def activate(req: ActivationRequest):
    conn = get_db_connection()
    c = conn.cursor()

    c.execute("SELECT * FROM licenses WHERE key_str=?", (req.key,))
    row = c.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="密钥不存在")

    # 转为字典方便操作
    license_data = dict(row)

    # 逻辑判断
    if license_data['is_used'] == 1:
        # 如果已被使用，判断是不是同一台机器
        if license_data['hwid'] == req.hwid:
            conn.close()
            # 计算过期时间 (如果不是永久)
            return {"status": "success", "msg": "欢迎回来", "days": license_data['valid_days']}
        else:
            conn.close()
            raise HTTPException(status_code=403, detail="该密钥已被其他设备激活，无法重复使用")

    # 如果未被使用，执行激活
    now = datetime.datetime.now().isoformat()
    c.execute("UPDATE licenses SET is_used=1, hwid=?, activated_at=? WHERE key_str=?",
              (req.hwid, now, req.key))
    conn.commit()
    conn.close()

    return {"status": "success", "msg": "激活成功", "days": license_data['valid_days']}

# 启动命令: uvicorn main:app --host 0.0.0.0 --port 8000
