# 客户端激活集成指南

本文档详细说明如何在客户端软件中集成许可证激活功能。

## 📋 目录

- [激活流程](#激活流程)
- [硬件ID生成](#硬件id生成)
- [代码示例](#代码示例)
  - [Python](#python)
  - [JavaScript/Node.js](#javascriptnodejs)
  - [C#](#c)
  - [Java](#java)
  - [Go](#go)
- [错误处理](#错误处理)
- [最佳实践](#最佳实践)

## 激活流程

```
┌─────────────┐
│  用户输入   │
│  License Key │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 生成硬件ID  │
│   (HWID)    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 调用激活API │
│ POST请求    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  处理响应   │
│  成功/失败  │
└─────────────┘
```

## 硬件ID生成

硬件ID应该基于以下唯一标识符的组合：
- CPU序列号
- 主板序列号
- MAC地址
- 硬盘序列号

### 为什么需要硬件ID？
- 一机一码：每个密钥只能在一台设备上使用
- 防止盗版：防止密钥被共享
- 可追溯：知道哪个设备激活了密钥

## 代码示例

### Python

#### 1. 安装依赖
```bash
pip install requests
```

#### 2. 完整实现
```python
import requests
import hashlib
import platform
import uuid
import json
from typing import Optional, Tuple

class LicenseManager:
    def __init__(self, server_url: str = "http://107.172.1.7:8888"):
        self.server_url = server_url
        self.license_key = None
        self.is_activated = False

    def generate_hwid(self) -> str:
        """
        生成唯一硬件ID
        """
        try:
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff)
                            for i in range(0, 48, 8)])[0:17]

            system_info = f"{platform.machine()}-{platform.system()}-{mac}"
            hwid = hashlib.sha256(system_info.encode()).hexdigest()[:32].upper()

            return hwid
        except Exception as e:
            # 降级方案：使用随机UUID
            return str(uuid.uuid4()).replace('-', '').upper()[:32]

    def activate(self, license_key: str) -> Tuple[bool, str, Optional[dict]]:
        """
        激活许可证

        Args:
            license_key: 用户输入的许可证密钥

        Returns:
            (成功状态, 消息, 响应数据)
        """
        self.license_key = license_key
        hwid = self.generate_hwid()

        try:
            response = requests.post(
                f"{self.server_url}/api/activate",
                json={
                    "key": license_key,
                    "hwid": hwid
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    self.is_activated = True
                    return True, data.get("msg", "激活成功"), data
                else:
                    return False, data.get("detail", "激活失败"), None
            elif response.status_code == 403:
                return False, "该密钥已被其他设备激活，无法重复使用", None
            elif response.status_code == 404:
                return False, "密钥不存在或已失效", None
            else:
                return False, f"服务器错误: {response.status_code}", None

        except requests.exceptions.Timeout:
            return False, "连接服务器超时，请检查网络", None
        except requests.exceptions.ConnectionError:
            return False, "无法连接到服务器，请检查网络", None
        except Exception as e:
            return False, f"激活失败: {str(e)}", None

    def save_license(self, filepath: str = "license.json") -> bool:
        """
        保存许可证到本地
        """
        try:
            data = {
                "license_key": self.license_key,
                "hwid": self.generate_hwid(),
                "activated_at": str(datetime.datetime.now())
            }
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"保存许可证失败: {e}")
            return False

    def load_license(self, filepath: str = "license.json") -> bool:
        """
        从本地加载许可证
        """
        try:
            if not os.path.exists(filepath):
                return False

            with open(filepath, 'r') as f:
                data = json.load(f)

            saved_hwid = data.get("hwid")
            current_hwid = self.generate_hwid()

            if saved_hwid == current_hwid:
                self.license_key = data.get("license_key")
                self.is_activated = True
                return True
            else:
                print("许可证与当前设备不匹配")
                return False

        except Exception as e:
            print(f"加载许可证失败: {e}")
            return False

# 使用示例
if __name__ == "__main__":
    import os
    import datetime

    license_mgr = LicenseManager()

    # 1. 尝试从本地加载
    if license_mgr.load_license():
        print("✅ 许可证验证通过，软件已激活")
        print(f"密钥: {license_mgr.license_key}")
    else:
        # 2. 让用户输入密钥
        license_key = input("请输入许可证密钥: ").strip()

        # 3. 调用激活API
        success, message, data = license_mgr.activate(license_key)

        if success:
            print(f"✅ {message}")
            print(f"有效期: {'永久' if data.get('days') == -1 else f'{data.get("days")}天'}")

            # 4. 保存到本地
            if license_mgr.save_license():
                print("✅ 许可证已保存到本地")
        else:
            print(f"❌ {message}")
            exit(1)
```

### JavaScript/Node.js

#### 1. 安装依赖
```bash
npm install axios node-machine-id
```

#### 2. 完整实现
```javascript
const axios = require('axios');
const { machineIdSync } = require('node-machine-id');
const crypto = require('crypto');
const fs = require('fs').promises;
const path = require('path');

class LicenseManager {
    constructor(serverUrl = 'http://107.172.1.7:8888') {
        this.serverUrl = serverUrl;
        this.licenseKey = null;
        this.isActivated = false;
    }

    /**
     * 生成硬件ID
     */
    async generateHWID() {
        try {
            const machineId = machineIdSync({ original: true });
            const platform = process.platform;
            const arch = process.arch;

            const hwidString = `${platform}-${arch}-${machineId}`;
            const hwid = crypto
                .createHash('sha256')
                .update(hwidString)
                .digest('hex')
                .substring(0, 32)
                .toUpperCase();

            return hwid;
        } catch (error) {
            // 降级方案：生成随机ID
            return crypto.randomBytes(16).toString('hex').substring(0, 32).toUpperCase();
        }
    }

    /**
     * 激活许可证
     */
    async activate(licenseKey) {
        this.licenseKey = licenseKey;
        const hwid = await this.generateHWID();

        try {
            const response = await axios.post(
                `${this.serverUrl}/api/activate`,
                {
                    key: licenseKey,
                    hwid: hwid
                },
                {
                    timeout: 10000,
                    headers: {
                        'Content-Type': 'application/json'
                    }
                }
            );

            if (response.data.status === 'success') {
                this.isActivated = true;
                return {
                    success: true,
                    message: response.data.msg,
                    data: response.data
                };
            } else {
                return {
                    success: false,
                    message: response.data.detail || '激活失败'
                };
            }

        } catch (error) {
            if (error.response) {
                if (error.response.status === 403) {
                    return {
                        success: false,
                        message: '该密钥已被其他设备激活，无法重复使用'
                    };
                } else if (error.response.status === 404) {
                    return {
                        success: false,
                        message: '密钥不存在或已失效'
                    };
                }
                return {
                    success: false,
                    message: `服务器错误: ${error.response.status}`
                };
            } else if (error.code === 'ECONNABORTED') {
                return {
                    success: false,
                    message: '连接服务器超时，请检查网络'
                };
            } else {
                return {
                    success: false,
                    message: `激活失败: ${error.message}`
                };
            }
        }
    }

    /**
     * 保存许可证到本地
     */
    async saveLicense(filepath = path.join(__dirname, 'license.json')) {
        try {
            const data = {
                licenseKey: this.licenseKey,
                hwid: await this.generateHWID(),
                activatedAt: new Date().toISOString()
            };

            await fs.writeFile(filepath, JSON.stringify(data, null, 2), 'utf8');
            return true;
        } catch (error) {
            console.error('保存许可证失败:', error.message);
            return false;
        }
    }

    /**
     * 从本地加载许可证
     */
    async loadLicense(filepath = path.join(__dirname, 'license.json')) {
        try {
            const data = await fs.readFile(filepath, 'utf8');
            const licenseData = JSON.parse(data);

            const savedHWID = licenseData.hwid;
            const currentHWID = await this.generateHWID();

            if (savedHWID === currentHWID) {
                this.licenseKey = licenseData.licenseKey;
                this.isActivated = true;
                return true;
            } else {
                console.log('许可证与当前设备不匹配');
                return false;
            }

        } catch (error) {
            if (error.code === 'ENOENT') {
                // 文件不存在，不是错误
                return false;
            }
            console.error('加载许可证失败:', error.message);
            return false;
        }
    }
}

// 使用示例
(async () => {
    const readline = require('readline');

    const licenseMgr = new LicenseManager();

    // 1. 尝试从本地加载
    if (await licenseMgr.loadLicense()) {
        console.log('✅ 许可证验证通过，软件已激活');
        console.log(`密钥: ${licenseMgr.licenseKey}`);
        return;
    }

    // 2. 让用户输入密钥
    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout
    });

    rl.question('请输入许可证密钥: ', async (licenseKey) => {
        rl.close();

        licenseKey = licenseKey.trim();

        // 3. 调用激活API
        const result = await licenseMgr.activate(licenseKey);

        if (result.success) {
            console.log(`✅ ${result.message}`);
            const days = result.data.days;
            console.log(`有效期: ${days === -1 ? '永久' : `${days}天`}`);

            // 4. 保存到本地
            if (await licenseMgr.saveLicense()) {
                console.log('✅ 许可证已保存到本地');
            }
        } else {
            console.log(`❌ ${result.message}`);
            process.exit(1);
        }
    });
})();
```

### C# (.NET)

#### 1. NuGet包
```xml
<PackageReference Include="System.Management" Version="7.0.0" />
<PackageReference Include="Newtonsoft.Json" Version="13.0.3" />
```

#### 2. 完整实现
```csharp
using System;
using System.IO;
using System.Management;
using System.Net.Http;
using System.Security.Cryptography;
using System.Text;
using System.Threading.Tasks;
using Newtonsoft.Json;

public class LicenseManager
{
    private readonly string _serverUrl;
    private string _licenseKey;
    private bool _isActivated;

    public LicenseManager(string serverUrl = "http://107.172.1.7:8888")
    {
        _serverUrl = serverUrl;
    }

    /// <summary>
    /// 生成硬件ID
    /// </summary>
    public string GenerateHWID()
    {
        try
        {
            string machineInfo = string.Empty;

            // 获取CPU序列号
            try
            {
                using (var searcher = new ManagementObjectSearcher("SELECT ProcessorId FROM Win32_Processor"))
                {
                    foreach (ManagementObject obj in searcher.Get())
                    {
                        machineInfo += obj["ProcessorId"]?.ToString() ?? "UNKNOWN";
                        break;
                    }
                }
            }
            catch { }

            // 获取主板序列号
            try
            {
                using (var searcher = new ManagementObjectSearcher("SELECT SerialNumber FROM Win32_BaseBoard"))
                {
                    foreach (ManagementObject obj in searcher.Get())
                    {
                        machineInfo += obj["SerialNumber"]?.ToString() ?? "UNKNOWN";
                        break;
                    }
                }
            }
            catch { }

            // 获取MAC地址
            try
            {
                using (var searcher = new ManagementObjectSearcher("SELECT MacAddress FROM Win32_NetworkAdapter WHERE PhysicalAdapter = TRUE"))
                {
                    foreach (ManagementObject obj in searcher.Get())
                    {
                        string mac = obj["MacAddress"]?.ToString()?.Replace(":", "");
                        if (!string.IsNullOrEmpty(mac))
                        {
                            machineInfo += mac;
                            break;
                        }
                    }
                }
            }
            catch { }

            // SHA256哈希
            using (var sha256 = SHA256.Create())
            {
                byte[] bytes = sha256.ComputeHash(Encoding.UTF8.GetBytes(machineInfo));
                StringBuilder sb = new StringBuilder();
                for (int i = 0; i < 16; i++) // 取前32字符
                {
                    sb.Append(bytes[i].ToString("X2"));
                }
                return sb.ToString();
            }
        }
        catch
        {
            // 降级方案
            return Guid.NewGuid().ToString().Replace("-", "").Substring(0, 32).ToUpper();
        }
    }

    /// <summary>
    /// 激活许可证
    /// </summary>
    public async Task<(bool Success, string Message, dynamic Data)> ActivateAsync(string licenseKey)
    {
        _licenseKey = licenseKey;
        string hwid = GenerateHWID();

        try
        {
            using (var httpClient = new HttpClient())
            {
                httpClient.Timeout = TimeSpan.FromSeconds(10);

                var payload = new
                {
                    key = licenseKey,
                    hwid = hwid
                };

                var json = JsonConvert.SerializeObject(payload);
                var content = new StringContent(json, Encoding.UTF8, "application/json");

                var response = await httpClient.PostAsync($"{_serverUrl}/api/activate", content);

                var responseContent = await response.Content.ReadAsStringAsync();

                if (response.StatusCode == System.Net.HttpStatusCode.OK)
                {
                    dynamic data = JsonConvert.DeserializeObject(responseContent);
                    if (data.status == "success")
                    {
                        _isActivated = true;
                        return (true, data.msg.ToString(), data);
                    }
                    return (false, data.detail?.ToString() ?? "激活失败", null);
                }
                else if (response.StatusCode == System.Net.HttpStatusCode.Forbidden)
                {
                    return (false, "该密钥已被其他设备激活，无法重复使用", null);
                }
                else if (response.StatusCode == System.Net.HttpStatusCode.NotFound)
                {
                    return (false, "密钥不存在或已失效", null);
                }
                else
                {
                    return (false, $"服务器错误: {(int)response.StatusCode}", null);
                }
            }
        }
        catch (TaskCanceledException)
        {
            return (false, "连接服务器超时，请检查网络", null);
        }
        catch (Exception ex)
        {
            return (false, $"激活失败: {ex.Message}", null);
        }
    }

    /// <summary>
    /// 保存许可证到本地
    /// </summary>
    public bool SaveLicense(string filepath = "license.json")
    {
        try
        {
            var data = new
            {
                licenseKey = _licenseKey,
                hwid = GenerateHWID(),
                activatedAt = DateTime.Now.ToString("o")
            };

            string json = JsonConvert.SerializeObject(data, Formatting.Indented);
            File.WriteAllText(filepath, json, Encoding.UTF8);
            return true;
        }
        catch (Exception ex)
        {
            Console.WriteLine($"保存许可证失败: {ex.Message}");
            return false;
        }
    }

    /// <summary>
    /// 从本地加载许可证
    /// </summary>
    public bool LoadLicense(string filepath = "license.json")
    {
        try
        {
            if (!File.Exists(filepath))
                return false;

            string json = File.ReadAllText(filepath, Encoding.UTF8);
            dynamic data = JsonConvert.DeserializeObject(json);

            string savedHWID = data.hwid?.ToString();
            string currentHWID = GenerateHWID();

            if (savedHWID == currentHWID)
            {
                _licenseKey = data.licenseKey?.ToString();
                _isActivated = true;
                return true;
            }
            else
            {
                Console.WriteLine("许可证与当前设备不匹配");
                return false;
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"加载许可证失败: {ex.Message}");
            return false;
        }
    }
}

// 使用示例
class Program
{
    static async Task Main(string[] args)
    {
        var licenseMgr = new LicenseManager();

        // 1. 尝试从本地加载
        if (licenseMgr.LoadLicense())
        {
            Console.WriteLine("✅ 许可证验证通过，软件已激活");
            return;
        }

        // 2. 让用户输入密钥
        Console.Write("请输入许可证密钥: ");
        string licenseKey = Console.ReadLine()?.Trim();

        // 3. 调用激活API
        var result = await licenseMgr.ActivateAsync(licenseKey);

        if (result.Success)
        {
            Console.WriteLine($"✅ {result.Message}");

            dynamic data = result.Data;
            int days = data.days;
            Console.WriteLine($"有效期: {(days == -1 ? "永久" : $"{days}天")}");

            // 4. 保存到本地
            if (licenseMgr.SaveLicense())
            {
                Console.WriteLine("✅ 许可证已保存到本地");
            }
        }
        else
        {
            Console.WriteLine($"❌ {result.Message}");
            Environment.Exit(1);
        }
    }
}
```

### Java

```java
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HashMap;
import java.util.Map;
import java.util.Scanner;

public class LicenseManager {
    private final String serverUrl;
    private String licenseKey;
    private boolean isActivated;

    public LicenseManager(String serverUrl) {
        this.serverUrl = serverUrl;
        this.isActivated = false;
    }

    /**
     * 生成硬件ID
     */
    public String generateHWID() {
        try {
            String os = System.getProperty("os.name");
            String arch = System.getProperty("os.arch");
            String userName = System.getProperty("user.name");

            String machineInfo = os + "-" + arch + "-" + userName;

            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(machineInfo.getBytes(StandardCharsets.UTF_8));

            StringBuilder sb = new StringBuilder();
            for (int i = 0; i < 16; i++) { // 取前32字符
                sb.append(String.format("%02X", hash[i]));
            }

            return sb.toString();
        } catch (NoSuchAlgorithmException e) {
            // 降级方案
            return java.util.UUID.randomUUID().toString()
                    .replace("-", "")
                    .substring(0, 32)
                    .toUpperCase();
        }
    }

    /**
     * 激活许可证
     */
    public Map<String, Object> activate(String licenseKey) throws Exception {
        this.licenseKey = licenseKey;
        String hwid = generateHWID();

        HttpURLConnection connection = null;
        try {
            URL url = new URL(serverUrl + "/api/activate");
            connection = (HttpURLConnection) url.openConnection();
            connection.setRequestMethod("POST");
            connection.setRequestProperty("Content-Type", "application/json");
            connection.setConnectTimeout(10000);
            connection.setDoOutput(true);

            // 构建请求体
            Map<String, String> requestBody = new HashMap<>();
            requestBody.put("key", licenseKey);
            requestBody.put("hwid", hwid);

            ObjectMapper mapper = new ObjectMapper();
            String jsonInput = mapper.writeValueAsString(requestBody);

            try (OutputStream os = connection.getOutputStream()) {
                byte[] input = jsonInput.getBytes(StandardCharsets.UTF_8);
                os.write(input, 0, input.length);
            }

            int responseCode = connection.getResponseCode();
            Map<String, Object> responseMap;

            if (responseCode == HttpURLConnection.HTTP_OK) {
                try (BufferedReader br = new BufferedReader(
                        new InputStreamReader(connection.getInputStream(), StandardCharsets.UTF_8))) {
                    StringBuilder response = new StringBuilder();
                    String responseLine;
                    while ((responseLine = br.readLine()) != null) {
                        response.append(responseLine.trim());
                    }
                    responseMap = mapper.readValue(response.toString(), Map.class);
                }

                if ("success".equals(responseMap.get("status"))) {
                    isActivated = true;
                    return Map.of(
                            "success", true,
                            "message", responseMap.get("msg"),
                            "data", responseMap
                    );
                } else {
                    return Map.of(
                            "success", false,
                            "message", responseMap.getOrDefault("detail", "激活失败")
                    );
                }
            } else if (responseCode == HttpURLConnection.HTTP_FORBIDDEN) {
                return Map.of(
                        "success", false,
                        "message", "该密钥已被其他设备激活，无法重复使用"
                );
            } else if (responseCode == HttpURLConnection.HTTP_NOT_FOUND) {
                return Map.of(
                        "success", false,
                        "message", "密钥不存在或已失效"
                );
            } else {
                return Map.of(
                        "success", false,
                        "message", "服务器错误: " + responseCode
                );
            }
        } finally {
            if (connection != null) {
                connection.disconnect();
            }
        }
    }

    /**
     * 保存许可证到本地
     */
    public boolean saveLicense(String filepath) {
        try {
            Map<String, Object> data = new HashMap<>();
            data.put("licenseKey", licenseKey);
            data.put("hwid", generateHWID());
            data.put("activatedAt", new java.util.Date().toString());

            ObjectMapper mapper = new ObjectMapper();
            mapper.writerWithDefaultPrettyPrinter()
                    .writeValue(new File(filepath), data);
            return true;
        } catch (Exception e) {
            System.err.println("保存许可证失败: " + e.getMessage());
            return false;
        }
    }

    /**
     * 从本地加载许可证
     */
    public boolean loadLicense(String filepath) {
        try {
            File file = new File(filepath);
            if (!file.exists()) {
                return false;
            }

            ObjectMapper mapper = new ObjectMapper();
            Map<String, Object> data = mapper.readValue(file, Map.class);

            String savedHWID = (String) data.get("hwid");
            String currentHWID = generateHWID();

            if (savedHWID.equals(currentHWID)) {
                licenseKey = (String) data.get("licenseKey");
                isActivated = true;
                return true;
            } else {
                System.out.println("许可证与当前设备不匹配");
                return false;
            }
        } catch (Exception e) {
            System.err.println("加载许可证失败: " + e.getMessage());
            return false;
        }
    }

    // 使用示例
    public static void main(String[] args) {
        LicenseManager licenseMgr = new LicenseManager("http://107.172.1.7:8888");
        String licenseFile = "license.json";

        // 1. 尝试从本地加载
        if (licenseMgr.loadLicense(licenseFile)) {
            System.out.println("✅ 许可证验证通过，软件已激活");
            return;
        }

        // 2. 让用户输入密钥
        Scanner scanner = new Scanner(System.in);
        System.out.print("请输入许可证密钥: ");
        String licenseKey = scanner.nextLine().trim();

        // 3. 调用激活API
        try {
            Map<String, Object> result = licenseMgr.activate(licenseKey);

            if ((Boolean) result.get("success")) {
                System.out.println("✅ " + result.get("message"));

                @SuppressWarnings("unchecked")
                Map<String, Object> data = (Map<String, Object>) result.get("data");
                int days = (int) data.get("days");
                System.out.println("有效期: " + (days == -1 ? "永久" : days + "天"));

                // 4. 保存到本地
                if (licenseMgr.saveLicense(licenseFile)) {
                    System.out.println("✅ 许可证已保存到本地");
                }
            } else {
                System.out.println("❌ " + result.get("message"));
                System.exit(1);
            }
        } catch (Exception e) {
            System.err.println("激活失败: " + e.getMessage());
            System.exit(1);
        }
    }
}
```

### Go

```go
package main

import (
    "crypto/sha256"
    "encoding/hex"
    "encoding/json"
    "fmt"
    "io"
    "io/ioutil"
    "net/http"
    "os"
    "os/user"
    "runtime"
    "strings"
    "time"
)

type LicenseManager struct {
    serverUrl    string
    licenseKey   string
    isActivated  bool
}

type ActivationRequest struct {
    Key  string `json:"key"`
    HWID string `json:"hwid"`
}

type ActivationResponse struct {
    Status string `json:"status"`
    Msg    string `json:"msg"`
    Days   int    `json:"days"`
    Detail string `json:"detail,omitempty"`
}

type LicenseData struct {
    LicenseKey  string    `json:"licenseKey"`
    HWID        string    `json:"hwid"`
    ActivatedAt time.Time `json:"activatedAt"`
}

type ActivationResult struct {
    Success bool
    Message string
    Data    *ActivationResponse
}

func NewLicenseManager(serverUrl string) *LicenseManager {
    return &LicenseManager{
        serverUrl: serverUrl,
    }
}

// 生成硬件ID
func (lm *LicenseManager) GenerateHWID() string {
    osType := runtime.GOOS
    arch := runtime.GOARCH

    currentUser, err := user.Current()
    userName := "unknown"
    if err == nil {
        userName = currentUser.Username
    }

    machineInfo := fmt.Sprintf("%s-%s-%s", osType, arch, userName)

    hash := sha256.Sum256([]byte(machineInfo))
    hwid := hex.EncodeToString(hash[:])[:32]

    return strings.ToUpper(hwid)
}

// 激活许可证
func (lm *LicenseManager) Activate(licenseKey string) (ActivationResult, error) {
    lm.licenseKey = licenseKey
    hwid := lm.GenerateHWID()

    request := ActivationRequest{
        Key:  licenseKey,
        HWID: hwid,
    }

    jsonData, err := json.Marshal(request)
    if err != nil {
        return ActivationResult{}, fmt.Errorf("序列化请求失败: %v", err)
    }

    resp, err := http.Post(lm.serverUrl+"/api/activate", "application/json", strings.NewReader(string(jsonData)))
    if err != nil {
        return ActivationResult{}, fmt.Errorf("连接服务器失败: %v", err)
    }
    defer resp.Body.Close()

    body, err := ioutil.ReadAll(resp.Body)
    if err != nil {
        return ActivationResult{}, fmt.Errorf("读取响应失败: %v", err)
    }

    var activationResp ActivationResponse
    err = json.Unmarshal(body, &activationResp)
    if err != nil {
        return ActivationResult{}, fmt.Errorf("解析响应失败: %v", err)
    }

    switch resp.StatusCode {
    case http.StatusOK:
        if activationResp.Status == "success" {
            lm.isActivated = true
            return ActivationResult{
                Success: true,
                Message: activationResp.Msg,
                Data:    &activationResp,
            }, nil
        }
        return ActivationResult{
            Success: false,
            Message: activationResp.Detail,
        }, nil

    case http.StatusForbidden:
        return ActivationResult{
            Success: false,
            Message: "该密钥已被其他设备激活，无法重复使用",
        }, nil

    case http.StatusNotFound:
        return ActivationResult{
            Success: false,
            Message: "密钥不存在或已失效",
        }, nil

    default:
        return ActivationResult{
            Success: false,
            Message: fmt.Sprintf("服务器错误: %d", resp.StatusCode),
        }, nil
    }
}

// 保存许可证到本地
func (lm *LicenseManager) SaveLicense(filepath string) error {
    data := LicenseData{
        LicenseKey:  lm.licenseKey,
        HWID:        lm.GenerateHWID(),
        ActivatedAt: time.Now(),
    }

    jsonData, err := json.MarshalIndent(data, "", "  ")
    if err != nil {
        return fmt.Errorf("序列化许可证失败: %v", err)
    }

    return ioutil.WriteFile(filepath, jsonData, 0644)
}

// 从本地加载许可证
func (lm *LicenseManager) LoadLicense(filepath string) (bool, error) {
    data, err := ioutil.ReadFile(filepath)
    if os.IsNotExist(err) {
        return false, nil
    }
    if err != nil {
        return false, fmt.Errorf("读取许可证文件失败: %v", err)
    }

    var licenseData LicenseData
    err = json.Unmarshal(data, &licenseData)
    if err != nil {
        return false, fmt.Errorf("解析许可证文件失败: %v", err)
    }

    if licenseData.HWID == lm.GenerateHWID() {
        lm.licenseKey = licenseData.LicenseKey
        lm.isActivated = true
        return true, nil
    }

    return false, fmt.Errorf("许可证与当前设备不匹配")
}

func main() {
    licenseMgr := NewLicenseManager("http://107.172.1.7:8888")
    licenseFile := "license.json"

    // 1. 尝试从本地加载
    if loaded, err := licenseMgr.LoadLicense(licenseFile); err == nil && loaded {
        fmt.Println("✅ 许可证验证通过，软件已激活")
        return
    }

    // 2. 让用户输入密钥
    var licenseKey string
    fmt.Print("请输入许可证密钥: ")
    fmt.Scanln(&licenseKey)
    licenseKey = strings.TrimSpace(licenseKey)

    // 3. 调用激活API
    result, err := licenseMgr.Activate(licenseKey)
    if err != nil {
        fmt.Printf("❌ 激活失败: %v\n", err)
        os.Exit(1)
    }

    if result.Success {
        fmt.Printf("✅ %s\n", result.Message)
        days := result.Data.Days
        if days == -1 {
            fmt.Println("有效期: 永久")
        } else {
            fmt.Printf("有效期: %d天\n", days)
        }

        // 4. 保存到本地
        if err := licenseMgr.SaveLicense(licenseFile); err == nil {
            fmt.Println("✅ 许可证已保存到本地")
        }
    } else {
        fmt.Printf("❌ %s\n", result.Message)
        os.Exit(1)
    }
}
```

## 错误处理

### 常见错误码

| HTTP状态码 | 错误信息 | 处理方式 |
|-----------|---------|---------|
| 200 | 激活成功 | 继续使用软件 |
| 403 | 已被其他设备激活 | 提示用户联系管理员 |
| 404 | 密钥不存在 | 提示用户检查密钥 |
| 超时 | 连接超时 | 提示检查网络，提供重试选项 |
| 网络错误 | 无法连接 | 提示检查网络，提供离线验证选项 |

### 错误处理最佳实践

```python
# Python示例：带重试机制的错误处理
import time
from typing import Tuple

def activate_with_retry(license_mgr, license_key: str, max_retries: int = 3) -> bool:
    """
    带重试机制的激活
    """
    for attempt in range(1, max_retries + 1):
        success, message, data = license_mgr.activate(license_key)

        if success:
            return True

        print(f"激活失败 (尝试 {attempt}/{max_retries}): {message}")

        # 如果是密钥错误，不要重试
        if "密钥不存在" in message or "已被其他设备激活" in message:
            return False

        # 如果是网络错误，等待后重试
        if attempt < max_retries:
            wait_time = attempt * 2  # 2秒, 4秒, 6秒
            print(f"{wait_time}秒后重试...")
            time.sleep(wait_time)

    return False
```

## 最佳实践

### 1. 安全性

```python
# ✅ 好的做法：加密本地存储的许可证
from cryptography.fernet import Fernet

class SecureLicenseManager(LicenseManager):
    def __init__(self, encryption_key: bytes):
        super().__init__()
        self.cipher = Fernet(encryption_key)

    def save_license(self, filepath: str) -> bool:
        data = {
            "license_key": self.license_key,
            "hwid": self.generate_hwid(),
            "activated_at": str(datetime.datetime.now())
        }

        json_str = json.dumps(data)
        encrypted = self.cipher.encrypt(json_str.encode())

        with open(filepath, 'wb') as f:
            f.write(encrypted)
        return True
```

### 2. 离线验证

```python
class OfflineLicenseManager(LicenseManager):
    def verify_offline(self, filepath: str = "license.json") -> bool:
        """
        离线验证许可证（适用于网络不可用的情况）
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            # 验证HWID匹配
            if data.get('hwid') != self.generate_hwid():
                return False

            # 验证是否过期（如果有期限）
            if data.get('valid_days', -1) > 0:
                activated_at = datetime.fromisoformat(data['activated_at'])
                expires_at = activated_at + timedelta(days=data['valid_days'])

                if datetime.now() > expires_at:
                    return False

            return True
        except:
            return False
```

### 3. 自动激活流程

```python
def auto_activate(license_mgr: LicenseManager, license_key: str):
    """
    完整的自动激活流程
    """
    # 1. 检查本地许可证
    if license_mgr.load_license():
        print("✅ 本地许可证有效")
        return

    # 2. 尝试在线激活
    print("正在验证许可证...")
    if activate_with_retry(license_mgr, license_key):
        license_mgr.save_license()
        print("✅ 激活成功")
        return

    # 3. 激活失败，询问用户
    print("❌ 无法验证许可证")
    print("请检查：")
    print("  1. 网络连接是否正常")
    print("  2. 许可证密钥是否正确")
    print("  3. 许可证是否已被其他设备使用")

    choice = input("是否继续试用模式？(y/n): ")
    if choice.lower() != 'y':
        exit(1)
```

### 4. 定期验证

```python
import threading
import time

def background_verification(license_mgr: LicenseManager, interval_hours: int = 24):
    """
    后台定期验证许可证
    """
    def verify():
        while True:
            time.sleep(interval_hours * 3600)
            if license_mgr.is_activated:
                success, _, _ = license_mgr.activate(license_mgr.license_key)
                if not success:
                    print("⚠️ 许可证验证失败，软件可能需要重新激活")

    thread = threading.Thread(target=verify, daemon=True)
    thread.start()
```

### 5. 用户体验

```python
def show_activation_ui():
    """
    友好的激活界面
    """
    print("\n" + "="*50)
    print("       软件许可证激活向导")
    print("="*50 + "\n")

    print("请输入您的许可证密钥激活软件")
    print("如果您没有许可证密钥，请联系购买\n")

    license_key = input("许可证密钥: ").strip()

    # 验证密钥格式
    if not is_valid_license_format(license_key):
        print("❌ 密钥格式不正确")
        return False

    # 激活
    license_mgr = LicenseManager()
    result = license_mgr.activate(license_key)

    if result[0]:
        print("\n✅ 激活成功！")
        print(f"密钥: {license_key}")
        print(f"有效期: {'永久' if result[2]['days'] == -1 else f'{result[2][\"days\"]}天'}")
        license_mgr.save_license()
        return True
    else:
        print(f"\n❌ {result[1]}")
        return False

def is_valid_license_format(key: str) -> bool:
    """
    验证密钥格式（示例）
    """
    # 假设密钥格式为：XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
    import re
    pattern = r'^[A-F0-9]{8}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{12}$'
    return bool(re.match(pattern, key.upper()))
```

## 总结

集成许可证激活系统的关键步骤：

1. ✅ 生成唯一的硬件ID（HWID）
2. ✅ 调用激活API发送密钥和HWID
3. ✅ 处理响应（成功/失败/错误）
4. ✅ 将激活信息保存到本地
5. ✅ 下次启动时先验证本地许可证
6. ✅ 提供友好的错误提示和重试机制
7. ✅ 考虑离线验证和安全加密

## 技术支持

- 服务器地址：`http://107.172.1.7:8888`
- API端点：`POST /api/activate`
- 问题反馈：联系管理员

---

**注意**：请确保在生产环境中使用HTTPS加密传输，并对本地存储的许可证进行加密。
