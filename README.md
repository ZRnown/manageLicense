# License Server (软件授权管理系统)

基于 FastAPI 的轻量级软件授权管理系统，支持一机一码验证、有效期设置、Web管理后台。

## 功能特性

- 📋 **Web管理后台**: 可视化界面生成和管理授权密钥
- 🔐 **一机一码**: 每个密钥只能绑定一台设备
- ⏰ **有效期控制**: 支持永久有效或指定天数
- 📊 **实时监控**: 查看密钥使用状态和绑定信息
- 🚀 **PM2管理**: 使用PM2进行进程守护和自动重启

## 技术栈

- **后端**: FastAPI + Python
- **数据库**: SQLite
- **进程管理**: PM2
- **Web服务**: Uvicorn

## 快速开始

### 1. 环境要求

- Python 3.8+
- Node.js (用于PM2)
- Git

### 2. 安装依赖

```bash
# 克隆项目
git clone https://github.com/your-username/license-server.git
cd license-server

# 安装Python依赖
pip install -r requirements.txt

# 安装PM2
npm install -g pm2
```

### 3. 配置

编辑 `main.py` 文件，修改管理员密码：

```python
ADMIN_PASSWORD = "your_secret_password"  # 修改为你的密码
```

### 4. 启动服务

**方式一：使用PM2（推荐）**

```bash
# 创建日志目录
mkdir -p logs

# 使用PM2启动
pm2 start ecosystem.config.js

# 查看状态
pm2 status

# 查看日志
pm2 logs license-server

# 停止服务
pm2 stop license-server

# 重启服务
pm2 restart license-server
```

**方式二：直接启动（开发环境）**

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 5. 访问管理后台

打开浏览器访问：`http://your-server-ip:8000/admin`

输入管理员密码即可开始生成和管理密钥。

## API 接口

### 客户端激活

**请求**

```bash
POST /api/activate
Content-Type: application/json

{
  "key": "YOUR_LICENSE_KEY",
  "hwid": "DEVICE_HARDWARE_ID"
}
```

**响应**

```json
{
  "status": "success",
  "msg": "激活成功",
  "days": -1
}
```

## 使用说明

### 生成密钥

1. 访问管理后台 `/admin`
2. 输入管理员密码
3. 设置生成数量（1-100）
4. 选择有效期：
   - 永久有效
   - 30天
   - 1年（365天）
   - 7天试用
5. 添加备注信息（可选）
6. 点击"生成密钥"按钮

### 激活流程

1. 客户端获取设备唯一标识（HWID）
2. 向服务器发送激活请求（包含密钥和HWID）
3. 服务器验证密钥：
   - 检查密钥是否存在
   - 检查是否已绑定其他设备
   - 如果未使用，则绑定当前设备
4. 返回激活结果

## 项目结构

```
license-server/
├── main.py                 # 主程序文件
├── requirements.txt        # Python依赖
├── ecosystem.config.js     # PM2配置
├── .gitignore             # Git忽略文件
└── README.md              # 说明文档
```

## PM2 常用命令

```bash
# 启动应用
pm2 start ecosystem.config.js

# 停止应用
pm2 stop license-server

# 重启应用
pm2 restart license-server

# 删除应用
pm2 delete license-server

# 查看应用信息
pm2 show license-server

# 查看日志
pm2 logs license-server

# 监控
pm2 monit

# 开机自启
pm2 startup
pm2 save
```

## 安全建议

1. **修改管理员密码**: 部署前务必修改默认密码
2. **使用HTTPS**: 生产环境建议使用反向代理（如Nginx）配置SSL
3. **防火墙设置**: 仅开放必要端口
4. **定期备份**: 定期备份SQLite数据库文件

## 注意事项

- SQLite数据库文件 (`licenses.db`) 不会上传到Git
- 日志文件存储在 `logs/` 目录
- PM2配置文件已设置内存限制（1G）和自动重启

## 许可证

MIT License

## 作者

Your Name
