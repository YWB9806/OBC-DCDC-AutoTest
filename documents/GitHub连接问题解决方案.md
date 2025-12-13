# GitHub连接问题解决方案

## 🔍 问题说明

错误信息：`Failed to connect to github.com port 443`

这是网络连接问题，可能的原因：
1. 网络防火墙阻止
2. 需要使用代理
3. DNS解析问题
4. GitHub服务暂时不可用

---

## 🔧 解决方案

### 方案1: 配置Git代理（如果你有代理）

如果你使用了代理软件（如Clash、V2Ray等）：

```bash
# 查看代理端口（通常是7890或10809）
# 在代理软件中查看HTTP代理端口

# 配置Git使用代理
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890

# 或者使用socks5代理
git config --global http.proxy socks5://127.0.0.1:7890
git config --global https.proxy socks5://127.0.0.1:7890

# 然后重试推送
git push -u origin main
```

**取消代理配置**（如果不需要）：
```bash
git config --global --unset http.proxy
git config --global --unset https.proxy
```

---

### 方案2: 使用SSH连接（推荐）

SSH连接通常更稳定，不容易被防火墙阻止。

#### 步骤1: 生成SSH密钥

```bash
# 生成SSH密钥
ssh-keygen -t ed25519 -C "1020678136@qq.com"

# 按Enter使用默认路径
# 按Enter跳过密码（或设置密码）
```

#### 步骤2: 复制公钥

```bash
# 显示公钥内容
cat ~/.ssh/id_ed25519.pub

# 或者在Windows上
type %USERPROFILE%\.ssh\id_ed25519.pub
```

#### 步骤3: 添加到GitHub

1. 访问：https://github.com/settings/keys
2. 点击 "New SSH key"
3. Title: `My Computer`
4. Key: 粘贴刚才复制的公钥内容
5. 点击 "Add SSH key"

#### 步骤4: 修改远程仓库URL

```bash
# 修改为SSH URL
git remote set-url origin git@github.com:YWB9806/OBC-DCDC-AutoTest.git

# 验证
git remote -v

# 测试SSH连接
ssh -T git@github.com

# 推送
git push -u origin main
```

---

### 方案3: 修改hosts文件（DNS问题）

如果是DNS解析问题，可以修改hosts文件。

#### Windows系统

1. 以管理员身份打开记事本
2. 打开文件：`C:\Windows\System32\drivers\etc\hosts`
3. 添加以下内容：

```
140.82.113.4 github.com
140.82.114.9 nodeload.github.com
140.82.112.5 api.github.com
140.82.112.10 codeload.github.com
185.199.108.133 raw.githubusercontent.com
185.199.108.153 training.github.com
185.199.108.153 assets-cdn.github.com
185.199.108.153 documentcloud.github.com
140.82.114.17 help.github.com
```

4. 保存文件
5. 刷新DNS缓存：

```bash
ipconfig /flushdns
```

6. 重试推送

---

### 方案4: 使用GitHub Desktop（最简单）

如果以上方法都不行，使用GitHub Desktop是最简单的方案。

#### 步骤1: 下载安装

访问：https://desktop.github.com/

#### 步骤2: 登录GitHub账号

打开GitHub Desktop，登录你的GitHub账号。

#### 步骤3: 添加本地仓库

1. File -> Add local repository
2. 选择项目目录：`D:\AI\Projects\Python脚本批量执行工具`
3. 点击 "Add repository"

#### 步骤4: 推送

1. 在GitHub Desktop中可以看到所有更改
2. 点击 "Publish repository"
3. 选择仓库名称：`OBC-DCDC-AutoTest`
4. 点击 "Publish repository"

#### 步骤5: 创建Release

1. 在GitHub Desktop中，点击 "Repository" -> "Create tag"
2. Tag name: `v1.0.0`
3. Description: `Release version 1.0.0`
4. 点击 "Create tag"
5. 点击 "Push origin" 推送标签

---

### 方案5: 临时使用Gitee镜像（备选）

如果GitHub一直连接不上，可以先推送到Gitee（国内）。

```bash
# 添加Gitee远程仓库
git remote add gitee https://gitee.com/YWB9806/OBC-DCDC-AutoTest.git

# 推送到Gitee
git push -u gitee main
git push gitee v1.0.0
```

---

## 🧪 测试网络连接

### 测试GitHub连接

```bash
# 测试HTTPS连接
curl -I https://github.com

# 测试SSH连接
ssh -T git@github.com

# 测试DNS解析
nslookup github.com
```

### 检查代理设置

```bash
# 查看当前Git代理配置
git config --global --get http.proxy
git config --global --get https.proxy

# 查看系统代理
echo %HTTP_PROXY%
echo %HTTPS_PROXY%
```

---

## 📊 推荐方案优先级

1. **方案2: 使用SSH**（最稳定，推荐）
2. **方案4: GitHub Desktop**（最简单）
3. **方案1: 配置代理**（如果有代理）
4. **方案3: 修改hosts**（DNS问题）
5. **方案5: 使用Gitee**（备选）

---

## 🎯 快速决策

### 如果你有代理软件
→ 使用**方案1**（配置代理）

### 如果你不熟悉命令行
→ 使用**方案4**（GitHub Desktop）

### 如果你想要最稳定的方案
→ 使用**方案2**（SSH连接）

### 如果GitHub完全连不上
→ 使用**方案5**（Gitee镜像）

---

## 💡 我的建议

**推荐使用方案2（SSH）+ 方案4（GitHub Desktop）的组合**：

1. 先安装GitHub Desktop（处理身份验证）
2. 配置SSH密钥（更稳定的连接）
3. 使用GitHub Desktop进行日常操作

这样既简单又稳定！

---

## 📞 需要帮助？

请告诉我：
1. 你是否使用了代理软件？
2. 你更倾向于哪个方案？
3. 是否愿意安装GitHub Desktop？

我会根据你的情况提供更具体的指导。

---

**创建时间**: 2025-12-13