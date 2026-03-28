---
name: email-security-audit
description: "邮件安全审计工具 - 分析邮件头(SPF/DKIM/DMARC)、检测钓鱼邮件、验证发件人身份、审计企业邮件安全配置。Use when: (1) 分析可疑/钓鱼邮件, (2) 审计邮件认证配置, (3) 检查企业域名安全记录, (4) 调查邮件威胁, (5) 生成安全审计报告, (6) 解析邮件头追踪路由."
author: charlie_liu
tags: [CI/CD]
---

# 邮件安全审计 (Email Security Audit)

企业级邮件安全分析与审计工具，用于检测威胁、验证身份认证、审计安全配置。

## 快速开始

```
基本邮件头分析:
用户提供邮件头 → 解析 Received 链 → 验证 SPF/DKIM/DMARC → 生成风险评估

企业域名安全审计:
用户提供域名 → 检查 SPF/DKIM/DMARC/MTA-STS 配置 → 评估安全成熟度 → 提供优化建议
```

---

## 审计工作流程

```
┌─────────────────────────────────────────────────────────────┐
│                    邮件安全审计流程                           │
├─────────────────────────────────────────────────────────────┤
│  Step 1: 收集邮件数据 (完整邮件头 + 正文)                      │
│     ↓                                                        │
│  Step 2: 邮件头分析 (路由追踪、时间戳、发件人)                  │
│     ↓                                                        │
│  Step 3: 身份验证 (SPF/DKIM/DMARC)                           │
│     ↓                                                        │
│  Step 4: 威胁检测 (钓鱼特征、可疑链接、危险附件)               │
│     ↓                                                        │
│  Step 5: 生成审计报告                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. 邮件头分析

### 1.1 关键邮件头字段

| 字段 | 说明 | 安全关注点 |
|------|------|-----------|
| `From` | 发件人地址 | 伪造检测、显示名称欺骗 |
| `Reply-To` | 回复地址 | 与 From 不一致可能为钓鱼 |
| `Received` | 邮件路由链 | 追踪真实来源、分析跳数 |
| `Return-Path` | 退信地址 | 与 From 一致性检查 |
| `Message-ID` | 邮件唯一标识 | 格式异常检测 |
| `Date` | 发送时间 | 时间戳异常检测 |
| `X-Originating-IP` | 原始发送IP | 地理位置分析 |
| `Authentication-Results` | 认证结果汇总 | SPF/DKIM/DMARC 结果 |

### 1.2 邮件路由追踪

```
示例 Received 链 (从下往上读):

Received: from mail.example.com (192.168.1.1)
          by mx.receiver.com with ESMTPS id ABC123
          (version=TLS1.3 cipher=TLS_AES_256_GCM_SHA384);
          Thu, 28 Mar 2024 10:30:00 +0800

Received: from [10.0.0.1] (unknown [203.0.113.50])
          by mail.example.com with ESMTPSA id DEF456;
          Thu, 28 Mar 2024 10:29:55 +0800
          ↑ 最底部的 Received 是最早的，显示真实来源
```

**路由分析要点:**
- 从下往上读取 Received 链
- 验证每个跳转的 IP 和域名
- 检查 TLS 加密使用情况 (ESMTPS = TLS)
- 识别异常路由路径 (如绕过正常网关)
- 检查 IP 地理位置是否合理

### 1.3 时间戳分析

检查时间戳异常：
- 发送时间与接收时间差异过大 (>1小时可疑)
- 时区不一致或不合理
- 日期格式不规范

---

## 2. 发件人身份验证

### 2.1 SPF (Sender Policy Framework)

**检查邮件头中的 SPF 结果:**
```
Received-SPF: pass (example.com: domain of sender@example.com
              designates 192.168.1.1 as permitted sender)
```

**或查询域名 SPF 记录:**
```bash
dig TXT example.com +short
# 示例返回: "v=spf1 include:_spf.google.com ip4:192.168.1.0/24 -all"
```

**SPF 结果解读:**
| 结果 | 含义 | 风险等级 |
|------|------|---------|
| `+all` | 允许所有IP | 🔴 高风险 (严重配置错误) |
| `?all` | 中立/无策略 | 🟡 中风险 |
| `~all` | 软失败 | 🟢 较安全 |
| `-all` | 硬失败 | ✅ 最安全 |

### 2.2 DKIM (DomainKeys Identified Mail)

**检查 DKIM 签名头:**
```
DKIM-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed;
        d=example.com; s=selector1;
        h=from:to:subject:date:message-id;
        bh=base64hash==;
        b=signature==;
```

**关键字段:**
- `d=` - 签名域名 (应与 From 域名一致)
- `s=` - 选择器 (用于查找公钥)
- `a=` - 签名算法 (推荐 rsa-sha256)
- `b=` - 签名值

**验证 DKIM 公钥:**
```bash
dig selector1._domainkey.example.com TXT +short
```

### 2.3 DMARC (Domain-based Message Authentication)

**查询 DMARC 策略:**
```bash
dig TXT _dmarc.example.com +short
# 示例: "v=DMARC1; p=reject; rua=mailto:dmarc@example.com; pct=100"
```

**DMARC 策略级别:**
| 策略 | 行为 | 安全级别 | 说明 |
|------|------|---------|------|
| `p=none` | 仅监控 | ⚠️ 基础 | 适合初期部署收集数据 |
| `p=quarantine` | 隔离可疑 | ✅ 中等 | 失败邮件送至垃圾箱 |
| `p=reject` | 拒绝失败 | ✅✅ 最高 | 强制执行，推荐生产环境 |

**检查邮件头中的 DMARC 结果:**
```
Authentication-Results: mx.google.com;
       dkim=pass header.i=@example.com;
       spf=pass (google.com: domain of sender@example.com
       designates 192.168.1.1 as permitted sender)
       smtp.mailfrom=sender@example.com;
       dmarc=pass (p=REJECT sp=REJECT dis=NONE) header.from=example.com
```

---

## 3. 钓鱼检测

### 3.1 发件人伪装检测

**常见伪装手法:**

1. **显示名称欺骗 (Display Name Deception)**
   ```
   From: "CEO 张伟" <attacker@evil-domain.com>
   ↑ 显示名称是可信的，但邮箱域名是恶意的
   ```

2. **相似域名欺骗 (Typosquatting/Homograph)**
   ```
   来自: support@paypa1.com (数字1代替字母l)
   来自: support@micr0soft.com (数字0代替字母o)
   来自: support@аррӏе.com (西里尔字母，视觉上类似)
   ```

3. **子域名欺骗**
   ```
   来自: security@account.gmail.phishing.com
   ↑ 真实域名是 phishing.com，前面都是伪装
   ```

4. **Reply-To 不一致**
   ```
   From: support@legitimate-company.com
   Reply-To: attacker@evil.com
   ↑ 回复会发送到攻击者邮箱
   ```

### 3.2 可疑链接检测

**链接安全检查清单:**
```
□ URL 与显示文本不匹配
□ 使用短链接服务 (bit.ly, tinyurl, t.cn 等)
□ 包含可疑参数 (?redirect=, &url=, &next=)
□ 域名拼写错误或使用相似字符
□ 使用 IP 地址代替域名
□ 新注册域名 (注册时间 < 30天)
□ 缺少 HTTPS (纯 HTTP)
□ 域名包含合法品牌名但不是官方域名
```

**危险链接模式:**
```
# 凭证窃取 - 模仿登录页面
https://evil-site.com/login?service=office365

# 开放重定向攻击
https://legitimate.com/redirect?url=https://evil.com

# 子域名欺骗
https://login.microsoftonline.com.evil-phishing.com/

# 数据收集
https://evil.com/steal?email=victim@company.com
```

### 3.3 内容钓鱼特征

**社会工程学特征 (Social Engineering):**

| 特征 | 示例 | 风险 |
|------|------|------|
| 紧急性 | "立即行动!", "24小时内", "限时" | ⚠️ 高 |
| 威胁性 | "账户将被冻结", "法律行动" | ⚠️ 高 |
| 利益诱惑 | "您已中奖", "退税通知", "退款" | ⚠️ 中 |
| 权威伪装 | "CEO要求", "IT部门通知", "法务部" | ⚠️ 高 |
| 保密要求 | "请勿告诉他人", "内部机密" | ⚠️ 高 |

**要求敏感信息:**
- 密码或凭证
- 银行卡号/CVV
- 验证码/OTP
- 身份证号
- 社保号

**危险附件类型:**
- `.exe`, `.scr`, `.pif` - 可执行文件
- `.zip`/`.rar` 内含 `.exe` - 压缩包藏木马
- `.doc`, `.xls` 要求启用宏 - 宏病毒
- `.js`, `.vbs`, `.hta` - 脚本文件
- `.iso`, `.img` - 磁盘镜像 (绕过安全检测)
- 双扩展名: `invoice.pdf.exe`, `report.docx.scr`

### 3.4 常见钓鱼攻击类型

**商务邮件入侵 (BEC - Business Email Compromise):**
```
特征:
- 伪装成高管/财务人员
- 要求紧急转账/购买礼品卡
- "保密处理，不要告诉其他人"
- 通常没有恶意链接/附件 (纯社会工程学)
```

**凭证收集 (Credential Harvesting):**
```
特征:
- 模仿登录页面 (Microsoft 365, Google, 银行)
- "您的账户需要验证"
- "密码即将过期"
- URL 与官方略有不同
```

**恶意软件投递:**
```
特征:
- 伪装成发票、快递通知、简历
- 附件要求"启用内容"或"运行宏"
- 压缩包密码保护 (绕过安全扫描)
```

---

## 4. 企业邮件安全配置审计

### 4.1 企业域名必备安全记录

**完整的安全 DNS 记录配置:**

```bash
# 1. SPF - 授权发送服务器
example.com. IN TXT "v=spf1 include:spf.protection.outlook.com include:_spf.google.com ip4:192.168.1.0/24 -all"

# 2. DKIM - 邮件签名
selector1._domainkey.example.com. IN TXT "v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQ..."

# 3. DMARC - 认证策略
_dmarc.example.com. IN TXT "v=DMARC1; p=reject; rua=mailto:dmarc-reports@example.com; ruf=mailto:forensic@example.com; pct=100; adkim=s; aspf=s"

# 4. MTA-STS - TLS 强制
_mta-sts.example.com. IN TXT "v=STSv1; id=2024032801"

# 5. TLS-RPT - TLS 报告
_smtp._tls.example.com. IN TXT "v=TLSRPTv1; rua=mailto:tls-reports@example.com"

# 6. BIMI - 品牌标识 (可选)
default._bimi.example.com. IN TXT "v=BIMI1; l=https://example.com/logo.svg; a=https://example.com/vmc.pem"
```

### 4.2 企业邮件安全配置检查表

```
邮件网关配置:
□ SPF 验证已启用 (reject 失败邮件)
□ DKIM 签名验证已启用
□ DMARC 策略执行已启用 (p=reject)
□ 入站恶意软件扫描已启用
□ 出站恶意软件扫描已启用
□ URL 重写/安全链接已启用
□ 附件类型限制已配置 (阻止危险类型)
□ 外部邮件警告标记已配置
□ 反垃圾邮件过滤已启用
□ TLS 加密强制 (入站/出站)

身份保护:
□ 员工安全意识培训
□ 模拟钓鱼演练
□ 多因素认证 (MFA) 已启用
□ 高管账户额外保护
□ 外部转发规则监控

监控与响应:
□ 钓鱼报告渠道畅通
□ 邮件日志留存 (>90天)
□ 异常发送行为告警
□ 事件响应流程明确
```

### 4.3 安全成熟度评估

| 级别 | SPF | DKIM | DMARC | MTA-STS | 评估 |
|------|-----|------|-------|---------|------|
| 基础 | ✓ | ✓ | p=none | ✗ | ⚠️ 仅监控 |
| 中等 | ✓ | ✓ | p=quarantine | ✓ | ✅ 部分保护 |
| 高级 | ✓ | ✓ | p=reject | ✓ | ✅✅ 推荐 |
| 最高 | ✓ | ✓ | p=reject | ✓ + BIMI | ✅✅✅ 最佳 |

---

## 5. 审计报告模板

```markdown
# 邮件安全审计报告

## 基本信息
- **审计日期**: YYYY-MM-DD HH:MM
- **邮件主题**: [Subject]
- **发件人**: [From: 显示名称 <email@domain.com>]
- **收件人**: [To]
- **邮件ID**: [Message-ID]

## 风险评估摘要

| 检查项 | 状态 | 风险等级 | 说明 |
|--------|------|----------|------|
| SPF 验证 | ✓/✗ | 🟢/🟡/🔴 | 详细结果 |
| DKIM 签名 | ✓/✗ | 🟢/🟡/🔴 | 详细结果 |
| DMARC 策略 | ✓/✗ | 🟢/🟡/🔴 | 详细结果 |
| 发件人一致性 | ✓/✗ | 🟢/🟡/🔴 | 详细结果 |
| 链接安全 | ✓/✗ | 🟢/🟡/🔴 | 详细结果 |
| 附件安全 | ✓/✗/N/A | 🟢/🟡/🔴 | 详细结果 |

## 总体风险评级
🔴 **高风险** / 🟡 **中风险** / 🟢 **低风险**

## 详细发现

### 1. 邮件路由分析
[Received 链分析，IP 地理位置追踪]

### 2. 身份验证详情
[SPF/DKIM/DMARC 详细检查结果]

### 3. 威胁指标
[发现的钓鱼特征、可疑链接、危险附件]

### 4. 内容分析
[社会工程学特征、语言模式]

## 建议措施
1. [针对发现问题的具体修复建议]
2. [...]
3. [...]

## 技术附录
[完整的邮件头、URL 列表、附件哈希等]
```

---

## 使用示例

### 示例 1: 分析可疑邮件

```
用户输入:
请帮我分析这封邮件是否安全：

From: "Microsoft Security" <security@micros0ft-alert.com>
Subject: Urgent: Your account will be suspended
[邮件完整内容...]

审计过程:
1. 解析邮件头，识别发件人域名 micros0ft-alert.com
2. 检查 SPF/DKIM/DMARC 配置
3. 识别域名拼写欺骗 (0 代替 o)
4. 检测紧急性语言
5. 分析链接目标
6. 生成风险评估报告
```

### 示例 2: 企业域名安全审计

```
用户输入:
审计我们公司 example.com 的邮件安全配置

审计过程:
1. dig TXT example.com → 检查 SPF
2. dig TXT _dmarc.example.com → 检查 DMARC
3. dig TXT selector._domainkey.example.com → 检查 DKIM
4. dig TXT _mta-sts.example.com → 检查 MTA-STS
5. 评估整体安全成熟度
6. 提供优化建议
```

---

## 资源

### references/
- `security_standards.md` - RFC 规范和安全最佳实践
- `threat_indicators.md` - 钓鱼和威胁指标数据库

### scripts/
- `analyze_email.py` - 邮件头解析脚本
- `check_dns_records.py` - DNS 安全记录检查
- `check_url.py` - URL 安全检测
