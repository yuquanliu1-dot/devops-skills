---
name: web-auto-testing
description: Web 应用自动化测试工具，基于 Playwright 生成和执行端到端测试，支持数据驱动测试、复杂场景、认证登录、CI/CD 集成。触发词："测试"、"全面测试"、"测试XX应用"、"测试XX功能"、"验证XX"、"e2e测试"、"端到端测试"、"playwright测试"、"生成测试用例"、"测试报告"。用户同时提供文档路径（.md/.pdf等）或URL时表明测试意图。不触发：爬虫/数据抓取、非测试目的的自动化脚本。
version: 1.3.0
author: lujing2026
tags: [web-testing, e2e-testing, playwright, test-automation, data-driven-testing]
---
# Web 自动化测试

## 核心规则（执行前必读）

### 用户意图判断

| 用户说                 | 执行        | 产物                                                      |
| ---------------------- | ----------- | --------------------------------------------------------- |
| 测试XX、验证XX、检查XX | **步骤1-5** | <项目名>_测试计划_<日期>.md + <项目名>_测试报告_<日期>.md |
| 生成脚本、写测试代码   | **步骤1-6** | + XXX.spec.js                                             |

> **核心规则**：用户没明确说"生成脚本"=只执行步骤1-5

### 可选步骤触发条件

| 步骤        | 触发条件                             |
| ----------- | ------------------------------------ |
| 6 脚本生成  | 用户明确说"生成脚本"、"写测试代码" |
| 7 CI/CD集成 | 用户明确说"配置CI/CD"、"Jenkins"     |

### 执行方式选择

**默认：MCP 工具交互验证**（使用 browser_navigate、browser_click 等）

**脚本方式**（仅以下情况）：
- 用户明确说"使用脚本验证"、"运行 playwright test"
- 用户明确要求生成 .spec.js 文件
- 需要批量执行大量测试用例

---

##  核心概念

### AAA 测试模式

业界标准的测试用例结构：

```
Given (Arrange)  - 准备测试数据和前置条件
When (Act)       - 执行被测试的操作
Then (Assert)    - 验证结果是否符合预期
```

**每个测试用例应遵循此结构，确保清晰可维护。**

### 测试用例命名规范

```
格式：feature_scenario_expectedResult
示例：
- login_validCredentials_success
- login_invalidPassword_showError
- search_withResults_displayResults
```

### 测试隔离原则

**每个测试用例必须独立**：
- 不依赖其他测试用例的执行顺序
- 不共享状态数据
- 独立准备和清理测试数据

### ref 属性陷阱

 **MCP 快照中的 `ref` 属性在实际页面中不存在，禁止使用 `[ref="e7"]`**

正确做法：使用浏览器开发者工具 (F12) 检查元素，优先使用 id、name、role

### 选择器规则

**优先级**：getByRole > getByLabel > getByPlaceholder > getByText + .first() > locator

**强制规则**：`getByText()` 和 `locator()` 必须加 `.first()`

### 禁止模式

 ref 属性、固定延迟 (`waitForTimeout`)、同步 API

### 测试类型定义

**5种测试类型**：

| 类型 | 定义 | 场景覆盖 | 数据验证 |
|------|------|---------|---------|
| **Smoke** | 快速验证核心功能可用 | 仅正向 | L1（存在性） |
| **单功能** | 完整测试指定功能 | 正向+异常+边界 | L2（准确性） |
| **回归** | 验证代码变更影响 | 正向+已知问题 | L1+L2（重点） |
| **E2E** | 端到端跨系统流程 | 跨系统+数据一致性 | L2（一致性） |
| **完整** | 全面验证所有功能（含跨系统） | 正向+异常+边界+跨系统 | L2（全面） |

**使用场景**：
- Smoke：用户说"冒烟"、"快速验证"、"快速测试"
- 单功能：用户说"测试XX功能"
- 回归：用户说"回归测试"或代码变更后
- E2E：用户说"端到端"或跨系统验证
- 完整：用户说"全面测试"、"测试XX应用"

**验证级别**：
- **L1（存在性验证）**：验证元素存在、可点击、基本显示
- **L2（准确性验证）**：验证数值正确、数据完整、状态准确

---

##  工作流程

### 测试目标类型

- **新建测试** → [新建测试流程](#新建测试流程)
- **现有测试优化** → [优化测试流程](#优化测试流程)
- **仅生成报告** → [报告生成流程](#报告生成流程)

---

### 新建测试流程

#### 步骤1：智能需求分析（必需）

**核心原则**：分析优先，询问兜底。先分析已有信息，只对不清楚的地方询问。

##### 1.1 收集需求信息

**优先从用户输入中提取：**

| 输入项 | 提取方式 | 示例 |
|-------|---------|------|
| 需求文档 | 正则匹配 `\.(md|txt|docx?|pdf)` | `D:\docs\REQUIREMENTS.md` |
| 测试 URL | 正则匹配 `https?://` | `http://localhost:5000` |
| 测试类型 | 关键词识别 | "全面测试"、"测试XX功能" |

**已提供信息的处理：**
- 用户已提供需求文档 → 读取并分析，跳过询问
- 用户已提供 URL → 直接使用，跳过询问
- 用户已说明测试类型 → 直接推断，跳过询问

##### 1.2 推断测试类型

**先分析用户的初始描述，提取明确信息：**

关键词识别规则：
- "测试XX功能"/"验证XX" → **单功能**（跳过范围询问）
- "全面测试"/"测试XX应用"/"基于需求文档测试" → **完整**（需要代码库分析）
- "冒烟"/"快速验证"/"快速测试" → **Smoke**（跳过类型询问）
- "回归" → **回归**（跳过类型询问）
- "端到端"/"E2E" → **E2E**（跳过类型询问）

##### 1.3 深度需求分析

**根据收集的输入，按以下优先级分析：**

```
优先级：需求文档 > 代码库分析 > 用户描述 > 询问用户
```

**分析内容：**

| 分析项 | 来源 | 提取方法 |
|-------|------|---------|
| 功能模块 | 需求文档/代码库 | 文档解析、路由分析、组件扫描 |
| 测试类型 | 关键词识别 | "全面/完整"→完整，"冒烟/快速"→Smoke，"回归"→回归，"端到端"→E2E，"测试XX功能"→**完整测试该功能** |
| 认证需求 | 代码库分析 | 搜索 login/auth 相关代码 |
| API 接口 | 代码库分析 | 扫描 API 路由、控制器 |
| 数据流 | 代码库分析 | 追踪 API 调用链 |

**代码库分析重点：**

```
扫描以下位置：
- /routes 或 /api - API 路由定义
- /components 或 /pages - 页面组件
- /src/auth 或 /lib/auth - 认证相关代码
- package.json - 依赖和技术栈
```

##### 1.4 分析结果确认

**展示分析摘要（调用 AskUserQuestion）：**

```javascript
AskUserQuestion({
  questions: [{
    question: `我分析出以下内容：

**功能模块**：${提取的功能列表}
**测试类型**：${推断的类型}
**需要认证**：${是/否}
**预估用例数**：${XX}个

这样对吗？`,
    header: "确认分析",
    options: [
      { label: "确认，继续侦测", description: "进入步骤2进行应用侦测" },
      { label: "需要调整", description: "修改功能范围或测试类型" },
      { label: "补充信息", description: "提供更多输入信息" }
    ],
    multiSelect: false
  }]
})
```

##### 1.5 补充需求询问

**询问优先级（按顺序询问，前一个满足就停止）：**

1. **测试 URL**（P0 - 必需）
   - 触发：URL未提供且无法从文档中提取
   - 询问："请提供测试应用的 URL"
   - 工具：直接对话

2. **认证信息**（P1 - 功能需要时）
   - 触发：用户明确说测试登录功能，或代码库发现login/auth
   - 询问："请提供测试账号信息：\n- 有效账号和密码（正向测试）\n- 错误密码/无效账号（异常测试，可选）"
   - 工具：直接对话

3. **测试类型**（P2 - 无法推断时）
   - 触发：用户描述无"全面/冒烟/回归/E2E"等关键词，且非单一功能
   - 询问：使用AskUserQuestion选择
   - 工具：AskUserQuestion

4. **功能范围**（P3 - 完全不清楚时）
   - 触发：无法识别任何具体功能，且用户未明确描述
   - 询问："请描述需要测试的核心功能"
   - 工具：直接对话

5. **测试数据**（P4 - 涉及数据时）
   - 触发：测试涉及数据输入/查询/列表展示
   - 询问：参考 `test-analysis-guide.md §10.3` 与用户交互
   - 工具：AskUserQuestion（数据来源确认时）

**跳过询问的条件：**
- 需求文档已明确说明
- 代码库分析结果清晰
- 用户描述完整且明确

**快速测试模式：**

当用户明确描述单一功能时（如"测试登录功能"、"验证搜索"），自动使用单功能模式：

```
测试类型：完整测试该功能（非Smoke）
测试范围：
- 基本功能（正向场景）
- 错误处理（异常场景）
- 边界场景（空值、超长等）

用例规模：根据功能复杂度决定（简单功能5-8个，复杂功能15+个）

如需调整，用户可主动说明。
```

**说明**：业界实践中，用户说"测试XX功能"通常期望完整覆盖该功能，而非快速冒烟验证。Smoke测试只在用户明确说"冒烟"、"快速验证"时使用。

#### 步骤2：应用侦测（必需）

**目标**：使用 Playwright MCP 工具侦测应用结构

**方式1：使用 MCP 工具（交互式）**

- `mcp__plugin_playwright_playwright__browser_navigate` - 导航到应用
- `mcp__plugin_playwright_playwright__browser_snapshot` - 获取页面快照
- `mcp__plugin_playwright_playwright__browser_evaluate` - 分析 DOM 结构

**方式2：使用 element_discovery.py 脚本（自动化）**

```bash
# 发现页面元素（按钮、链接、输入框）
python scripts/element_discovery.py

# 注意：脚本默认连接 http://localhost:5173
# 需确保目标应用服务器正在运行
```

**侦测策略**：

- **基础快照**（必须）
- **多轮快照**：滚动后、展开后、异步加载后
- **特殊元素**：iframe内部、弹窗触发后、动态加载完成后

**侦测内容**：页面结构（DOM）、交互元素（按钮/表单/链接）、数据流（API 调用）、特殊元素（iframe/弹窗）

**重点识别：需要数据验证的功能**（步骤3中会详细说明验证要求）

| 功能类型 | 识别特征 | 关注点 |
|---------|---------|--------|
| 统计卡片 | 显示数字、百分比、趋势图标 | 数值变化 |
| 数据表格 | 列表、分页、排序 | 行数、分页 |
| 搜索功能 | 搜索框、搜索按钮 | 结果匹配 |
| 筛选功能 | 下拉筛选、复选框筛选 | 条件过滤 |
| 图表组件 | ECharts/Chart.js/SVG 图表 | 数据点展示 |
| 导出功能 | 导出按钮、下载链接 | 文件生成 |

**自动提取交互元素**：


| 快照中的元素         | 提取方式                           | 示例       |
| -------------------- | ---------------------------------- | ---------- |
| `button "搜索"`      | getByRole('button', {name:'搜索'}) | 搜索按钮   |
| `link "导出"`        | getByRole('link', {name:'导出'})   | 导出链接   |
| `textbox "输入姓名"` | getByPlaceholder('输入姓名')       | 姓名输入框 |
| `combobox`           | getByRole('combobox')              | 部门下拉框 |

**内部产出**：交互元素清单（用于步骤3）

**必须向用户展示**：
1. 发现的交互元素摘要（按钮、链接、输入框、下拉框等数量和类型）
2. **识别的数据验证功能**（统计卡片、数据表格、图表、导出功能清单）
3. 元素侦测覆盖率（使用 element_coverage_analyzer.py 计算）
4. 询问"是否需要补充侦测某些区域"

**验证**：快照成功获取，元素识别完成

>  **重要**：步骤2完成后，**必须执行步骤3生成测试计划文档**，才能进入步骤4测试执行。禁止跳过步骤3！

#### 步骤3：测试规划（必需）

**目标**：根据测试类型，生成差异化的测试计划

**根据测试类型调整规划深度：**

详见上文 [核心概念 > 测试类型定义](#测试类型定义)

**关键差异**：
- **Smoke**：仅正向，失败即停
- **单功能**：正向+异常+边界场景全覆盖
- **回归**：关注变更区域+高频功能
- **E2E**：跨系统流程验证
- **完整**：正向+异常+边界+跨系统场景，全面覆盖

**用例规模**：由识别的功能点数量和场景覆盖决定（功能点 × 场景类型），详见 test-analysis-guide.md §3

**你必须做的**：

1. **阅读参考资料**（必须先执行）
   - 打开 `references/test-analysis-guide.md`，根据测试类型阅读 §2 对应的设计要点
   - 打开 `references/test-coverage-checklist.md`，逐项检查确保不遗漏

2. **确定覆盖范围**
   - **元素覆盖验证**（必须）：对照步骤2的交互元素清单，每种元素类型至少1个用例
   - **数据验证覆盖**（必须）：对照步骤2识别的数据验证功能清单，每个功能必须包含 L2 级验证用例
   - 包含：高频回归功能、核心业务流程、复杂场景、集成点

3. **明确排除范围**
   - 一次性功能、UI 频繁变更、探索性测试、性能压力测试

4. **设计测试用例**

   **4.1 场景覆盖要求**
   - 正向场景（必须）：验证基本功能流程
   - 异常场景（必须）：验证错误处理
   - 边界场景（必须）：验证极限条件
   - 数据驱动（测试涉及输入/筛选时）：多组数据验证同一逻辑

   **4.2 数据验证要求（必须检查）**

   对照步骤2识别的数据验证功能，确保每种功能都有对应的验证用例：

   | 功能类型 | 必须验证 | 验证级别 | 详见 |
   |---------|---------|---------|------|
   | 统计卡片 | 数值准确性 | L2 | [指南](references/test-analysis-guide.md) §6.2 |
   | 数据表格 | 行数、字段值、分页 | L2 | [指南](references/test-analysis-guide.md) §6.3 |
   | 搜索/筛选 | 结果包含/符合条件 | L2 | [指南](references/test-analysis-guide.md) §6.4 |
   | 图表组件 | 数据点、系列值 | L2 | [指南](references/test-analysis-guide.md) §6.5 |
   | 导出功能 | 文件内容准确性 | L2 | [指南](references/test-analysis-guide.md) §6.6 |

   **4.3 用例设计检查清单**

   每个测试用例必须包含：
   - [ ] 明确的测试目标（验证什么）
   - [ ] 具体的前置条件（页面状态、数据准备）
   - [ ] 可执行的测试步骤（操作+对象+数据）
   - [ ] 可验证的预期结果（状态/数值/文本/错误提示）

   **测试数据检查**（步骤5确认前必检）：
   - [ ] 每个用例都有对应的测试数据（输入值/操作值）
   - [ ] L2 级验证用例有明确的预期结果数据
   - [ ] 边界场景有对应的边界值数据（min/max/空值）
   - [ ] 异常场景有对应的异常数据（空值/超长/特殊字符）

   **业界最佳实践**：
   - **单一职责**：每个用例只验证一个功能点
   - **独立性**：用例之间无依赖，可单独执行
   - **可重复性**：多次执行结果一致
   - **合理超时**：每个用例设置超时时间（默认30秒）
   - **清理机制**：测试后清理数据（afterEach）

   **4.4 优先级分配**
   - P0：核心业务流程、数据准确性验证
   - P1：重要功能、常见交互
   - P2：辅助功能、边缘情况

5. **向用户展示测试计划摘要**（测试范围、优先级、用例清单）
   - 确保覆盖范围明确、排除范围有说明、用例完整

6. **请求用户确认**（**调用 AskUserQuestion**）
   - 调用格式：
     ```javascript
     // 根据数据检查结果动态构建问题
     const dataGaps = 检查数据缺口(); // 返回 { userRequired: [], smartGeneratable: [] }
     const hasUserRequiredData = dataGaps.userRequired.length > 0;
     const hasSmartGeneratableData = dataGaps.smartGeneratable.length > 0;

     // 构建问题描述
     let questionText = "请确认测试计划并选择后续操作";
     if (hasUserRequiredData || hasSmartGeneratableData) {
       const parts = [];
       if (hasUserRequiredData) {
         parts.push(`**需您提供**（认证/业务数据）：\n${dataGaps.userRequired.map(g => "- " + g).join("\n")}`);
       }
       if (hasSmartGeneratableData) {
         parts.push(`**可智能生成**（基础/边界/异常数据）：${dataGaps.smartGeneratable.length}项`);
       }
       questionText = `检测到测试数据缺口：\n\n${parts.join("\n\n")}`;
     }

     AskUserQuestion({
       questions: [{
         question: questionText,
         header: "确认计划",
         options: [
           { label: "智能生成并执行", description: hasSmartGeneratableData ? "智能分析生成缺失数据，立即执行测试" : "执行测试并生成报告" },
           { label: hasUserRequiredData ? "提供必要数据" : "查看测试数据", description: hasUserRequiredData ? "提供认证/业务数据（其余智能生成）" : "查看或修改测试数据" },
           { label: "生成计划文档", description: "保存测试计划后再执行" }
         ].filter(opt => {
           // 无缺口时显示全部选项
           if (!hasUserRequiredData && !hasSmartGeneratableData) return true;
           // 有缺口时隐藏"生成计划文档"
           return opt.label !== "生成计划文档";
         }),
         multiSelect: false
       }]
     })
     ```

7. **根据用户选择执行**：
   - 确认执行 → 进入步骤4
   - 生成文档 → 生成 `test-artifacts/plans/<项目名>_测试计划_<日期>.md`，然后进入步骤4
   - 需要调整/补充 → 返回修改计划

#### 步骤4：测试执行（必需）

**⚠️ 重要提醒**：请勿在测试执行完成前生成报告。不完整报告将导致：
- 无法准确评估测试覆盖率
- 部署决策可能基于不完整数据
- 未执行的用例无法追踪

**目标**：根据测试类型，执行对应的测试策略

**根据测试类型差异化执行：**

| 测试类型 | 执行策略 | 失败处理 | 完整性要求 |
|---------|---------|---------|-----------|
| **Smoke** | 快速执行，失败即停 | 立即报告，阻塞部署 | 核心路径 100% |
| **单功能** | 完整执行该功能 | 记录并继续 | 该功能 95%+ |
| **回归** | 顺序执行，记录继续 | 记录但继续执行 | 变更区域 95%+ |
| **E2E** | 串行执行（依赖流程） | 流程中断需分析 | 端到端 100% |
| **完整** | **执行所有用例（P0+P1+P2）** | 详细记录所有失败 | 全部用例 100% |

> **重要说明**：
> - **完整测试必须执行所有计划用例**，包括 P0、P1、P2 优先级的所有用例
> - 90%+ 是最低覆盖率标准，不是停止执行的依据
> - 完整测试只有在以下情况才能停止：
>   1. 所有计划用例已执行完成
>   2. 用户明确要求停止
>   3. 应用无法访问且重试失败
> - 不得在 P0 用例执行完成后就停止，必须继续执行 P1 和 P2 用例

> **注意**：MCP 模式下默认为顺序执行。"并行执行"仅适用于脚本模式（npx playwright test）。

**执行方式选择**：

```
用例数 < 20 → 当前会话执行（默认）
用例数 ≥ 20 → 询问用户 → 子代理执行（推荐，避免上下文压缩）
```

> **核心原则**：子代理拥有独立上下文，大量用例时避免主会话多次压缩。

**询问格式**（用例数 ≥ 20 时）：
```javascript
AskUserQuestion({
  questions: [{
    question: `检测到 ${用例数} 个测试用例，请选择执行方式：`,
    header: "执行方式",
    options: [
      { label: "当前会话执行", description: "在当前会话中逐个执行，实时反馈进度" },
      { label: "子代理执行", description: "启动独立子代理执行，避免上下文压缩（推荐）" }
    ],
    multiSelect: false
  }]
})
```

**子代理执行模式**：

使用 `Agent` 工具派发独立子代理，参考 `agents/test-executor.md`。

**子代理输出**：`test-artifacts/results/test_results.json`

**监控**：`TaskOutput` 检查进度，完成后读取 JSON 继续步骤5。

**执行流程**：

1. **初始化执行跟踪**：
   ```javascript
   执行跟踪对象 = {
     总用例数: 15,           // 计划执行的用例总数
     已执行: 0,              // 已执行完成的用例数
     通过: 0,                // 执行通过的用例数
     失败: 0,                // 执行失败的用例数
     跳过: 0,                // 跳过的用例数
     失败用例列表: [         // 失败用例详情
       { 用例名: "登录-错误密码", 截图: "login-failed.png" }
     ],
     开始时间: timestamp,    // 执行开始时间
     状态: "执行中" | "已完成" | "部分执行",  // 当前执行状态
     测试类型: "完整" | "单功能" | "回归" | "E2E" | "Smoke"  // 测试类型
   }
   ```

   **关键规则：**
   - 每执行完一个用例，必须更新 `已执行` 计数
   - 测试失败时，必须截图并记录到 `失败用例列表`
   - 状态变化：执行中 → 已完成/部分执行

2. **逐个执行用例**：
   - 每执行完一个用例，更新计数
   - 失败时截图保存

   **⚠️ 完整测试特殊规则**：
   - **必须执行所有计划用例**（P0 + P1 + P2）
   - 不得在某个优先级完成后停止
   - 只有在 `已执行 == 总用例数` 时才能标记为"已完成"
   - 如果测试类型为"完整"且 `已执行 < 总用例数`，状态必须保持"执行中"

3. **进度显示规范**：

   - 每个用例执行前：显示 `"正在执行：[${已执行+1}/${总用例数}] ${用例名称}"`
   - 每 5 个用例：显示汇总统计
   - **执行某个优先级完成后**（如 P0 完成）：显示 `"P0 用例已完成，继续执行 P1 用例..."`
   - 执行完成：显示最终统计

4. **必须向用户展示**：
   - 实时执行进度（已执行/总数）
   - 每个测试用例的执行结果（通过/失败）
   - 执行完成确认

**默认：MCP 工具交互验证**

`browser_navigate` → `browser_click` → `browser_snapshot` → 记录结果

**失败处理**：测试失败时调用 `browser_take_screenshot`，保存至 `test-artifacts/screenshots/{feature}-{case}-failed.png`，记录文件名用于报告

**脚本方式**：`npx playwright test`（触发条件见"执行方式选择"）

#### 步骤5：报告生成（必需）

**目标**：生成测试结果摘要和报告

**报告生成前检查（强制执行）：**

```javascript
IF 执行跟踪.已执行 < 执行跟踪.总用例数:
  IF 执行跟踪.测试类型 == "完整":
    ── 完整测试不允许生成部分报告 ──
    ── 必须执行剩余用例 ──
    "⚠️ 完整测试必须执行所有用例（已执行 ${执行跟踪.已执行}/${执行跟踪.总用例数}）"
    "请继续执行剩余用例以获得完整的测试报告"
    → 返回步骤 4 继续执行
  ELSE:
    ── 其他测试类型可选择生成部分报告 ──
    ── 调用 AskUserQuestion ──
    "⚠️ 测试未执行完整（已执行 ${执行跟踪.已执行}/${执行跟踪.总用例数}）"

    ⚠️ **警告**：生成不完整报告将：
    - 标记为[部分执行]，影响可信度
    - 未执行用例将无法追踪
    - 不建议用于部署决策

    选项：
    A. 执行剩余用例 → 返回步骤 4（推荐）
    B. 生成不完整报告 → 报告标记"部分执行"
  END IF
ELSE:
  ── 生成完整报告 ──
END IF
```

**不完整报告标记：**

- 报告标题添加 `[部分执行]` 标记
- 执行摘要中明确说明：`执行状态：部分执行（已执行 X/Y）`
- 失败测试详情中标注未执行的用例列表

**你必须做的**：

1. **收集测试产物**

   | 产物 | MCP 模式 | 脚本模式 |
   |------|----------|----------|
   | 失败截图 | 手动 `browser_take_screenshot` | 自动 |
   | 失败视频 | - | 自动 |
   | 追踪文件 | - | 自动 |

2. **使用测试报告模板**：
   - 使用 templates/test-report-template.md 模板
   - 自动填充覆盖率指标

3. **生成测试报告**

   **输出目录**：默认使用当前工作目录（被测试项目）的 `test-artifacts/` 子目录

**目录结构**：
```
<当前项目>/
├── test-artifacts/
│   ├── plans/          # 测试计划
│   ├── reports/         # 测试报告
│   ├── screenshots/     # 失败截图
│   └── results/         # 测试结果（JSON）
```

**MCP 模式**：手动生成 `test-artifacts/reports/<项目名>_测试报告_YYYY-MM-DD.md`

   **脚本模式**：`npx playwright test --reporter=html,json,junit`

4. **MCP 报告内容要点**

   - 执行摘要（总数、通过、失败、通过率）
   - 覆盖率指标：
     - 功能覆盖率（已测试功能数 / 识别功能总数）
     - 元素覆盖率（已测试元素数 / 识别元素总数）
     - 场景覆盖率（正向/异常/边界/数据验证）
   - 按模块分类的测试结果
   - 失败测试详情（错误、截图链接、重现步骤、修复建议）
   - 部署决策 → 参考「成功指标」判断是否可以部署
   - 使用 test-coverage-checklist.md 生成覆盖率检查项

5. **验证**

   - MCP 模式：报告包含失败截图链接
   - 脚本模式：HTML 报告可打开

---

#### 步骤6：脚本生成 ⚪ 可选

> 触发条件参见「可选步骤触发条件」

**目标**：生成可复用的 Playwright 测试脚本（.spec.js）

**确定脚本生成方式**：

| 场景 | 推荐方式 |
|------|----------|
| 简单页面 | 方式1 自动化生成 |
| 需要认证 | 方式1 + 保存认证 |
| 复杂交互 | 方式2 手动编写 |
| 大型项目 | 方式2 + POM 模式 |

**脚本结构选择**（手动编写时）：

| 项目特征 | 脚本结构 | 说明 |
|----------|----------|------|
| 单页面/简单流程 | 单文件脚本 | 直接在 .spec.js 中编写 |
| 多页面/重复操作 | POM 模式 | 使用页面对象封装，参考 [test-patterns.md](references/test-patterns.md) |
| 10+ 测试用例 | POM 模式 | 提高可维护性，参考 POM 模板 |

**方式1：自动化生成（推荐）**

使用 `scripts/generate_test_with_auth.py --interactive` 自动生成测试（含认证）

**方式2：手动编写**

**流程**：
1. 使用 `scripts/element_discovery.py` 发现页面元素
2. **阅读必读文档**：
   - [Playwright API 参考](references/playwright-api.md)（定位器、断言规则、等待机制）
   - [脚本模板](templates/spec-script.template.js)（脚本骨架）
3. 编写脚本 → 遇到问题参考下方「按需参考」
4. 使用 `scripts/verify_selectors.py` 验证选择器正确性

**测试配置模板**：

```javascript
// playwright.config.js
module.exports = {
  timeout: 30000,
  retries: process.env.CI ? 2 : 0,
  use: {
    actionTimeout: 10000,
    video: 'retain-on-failure'
  }
}

// 测试用例模板（AAA模式）
test('login_validCredentials_success', async ({ page }) => {
  // Arrange - 准备
  const testData = { username: 'test', password: '123456' };
  // Act - 执行
  await page.goto('/login');
  await page.fill('[name=username]', testData.username);
  await page.click('button[type=submit]');
  // Assert - 验证
  await expect(page).toHaveURL('/dashboard');
});
```

**按需参考**（遇到问题时查阅）：

| 场景 | 资源 |
|------|------|
| 元素等待、点击、下拉框 | [code-snippets.template.js](templates/code-snippets.template.js) |
| 需要页面对象封装（POM模式） | [pom-project-structure.md](templates/pom-project-structure.md) + [page-object.template.js](templates/page-object.template.js) |
| 登录页/列表页/详情页 POM | [pages/](templates/pages/) 目录下模板 |
| iframe、弹窗、AJAX | [complex-scenarios.md](references/complex-scenarios.md) |
| 多组输入数据验证同一功能 | [data-driven-testing.md](references/data-driven-testing.md) |
| 选择器不稳定 | [best-practices.md](references/best-practices.md) |
| 测试偶发失败 | [unstable-tests.md](references/unstable-tests.md) |

**验证（必须）**

使用 `scripts/verify_selectors.py` 验证选择器正确性

**输出**

- `[feature].spec.js` - 测试脚本
- `auth.json` - 认证状态（如需登录）

#### 步骤7：CI/CD 集成 ⚪ 可选

> 触发条件参见上方「可选步骤触发条件」

**目标**：配置 CI/CD 流程

**CI/CD 最佳实践**：

| 实践 | 说明 | 配置示例 |
|------|------|----------|
| 失败重试 | CI环境网络不稳定，重试2-3次 | `retries: process.env.CI ? 2 : 0` |
| 并行执行 | 分片运行，缩短执行时间 | `--workers=4` 或分片配置 |
| 视频录制 | 失败时录制视频便于调试 | `use: { video: 'retain-on-failure' }` |
| HTML报告 | 生成可视化报告 | `--reporter=html` |
| 测试超时 | 避免无限等待 | `test.setTimeout(30000)` |
| 环境变量 | 敏感信息不硬编码 | `.env` 文件或 CI Secrets |

**GitHub Actions 示例**：

```yaml
name: Playwright Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npx playwright test
      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
```

**选择平台**：

- GitHub Actions
- Jenkins
- GitLab CI

**输出**：

- `Jenkinsfile` - Jenkins Pipeline 配置
- `.github/workflows/playwright-tests.yml` - GitHub Actions 配置
- `.gitlab-ci.yml` - GitLab CI 配置

 **完整配置**：[CI/CD 集成](references/ci-cd-integration.md) - Jenkins、GitHub Actions、GitLab CI 详细配置

---

### 优化测试流程

**适用场景**：用户已有测试，需要改进或修复

**执行步骤**：返回步骤4-5（测试执行和报告生成）→ （可选）步骤6（脚本生成）

**与新建测试的区别**：

- 跳过需求分析和应用侦测
- 直接运行现有测试
- 基于报告结果进行优化

---

### 报告生成流程

**适用场景**：用户仅需要测试报告，不执行测试

**执行步骤**：仅步骤5（报告生成）

**前置条件**：

- 测试已执行完成
- 测试结果文件已生成（test-results.json、junit-results.xml）
- 测试产物已收集（截图、视频、追踪）

**操作**：

1. 解析现有测试结果文件
2. 生成 HTML 报告（如果尚未生成）
3. 生成 <项目名>_测试报告_YYYY-MM-DD.md 摘要报告

---

## 参考文档

### 快速参考

| 主题 | 文档 |
|------|------|
| 测试规则与最佳实践 | [test-rules.md](references/test-rules.md) |
| 测试产物管理 | [artifacts-management.md](references/artifacts-management.md) |
| 测试成功指标 | [success-metrics.md](references/success-metrics.md) |
| 常见问题排查 | [troubleshooting.md](references/troubleshooting.md) |

### 核心参考（必须阅读）

| 参考 | 何时使用 |
|------|------|
| [测试分析指南](references/test-analysis-guide.md) | **重要**：测试设计前必读（测试类型选择、设计要点、功能分类、边界测试、数据验证） |
| [测试覆盖率检查清单](references/test-coverage-checklist.md) | **重要**：测试计划完成后，自检覆盖率 |
| [Playwright API 参考](references/playwright-api.md) | 编写测试脚本前必读（定位器、断言、等待） |
| [复杂场景处理](references/complex-scenarios.md) | iframe、弹窗、AJAX、登录、多窗口 |
| [数据驱动测试](references/data-driven-testing.md) | 多组输入数据验证同一功能 |
| [测试模式](references/test-patterns.md) | POM 模式、并行测试、参数化 |

### 扩展参考

| 参考 | 何时使用 |
|------|----------|
| [最佳实践](references/best-practices.md) | 选择器不稳定、需要组件库策略、代码审查 |
| [常见陷阱](references/common-pitfalls.md) | 脚本报错时排查常见问题 |
| [CI/CD 集成](references/ci-cd-integration.md) | 配置 Jenkins、GitHub Actions、GitLab CI |
| [不稳定测试管理](references/unstable-tests.md) | 测试偶发失败、需要识别和修复策略 |
| [测试产物管理](references/artifacts-management.md) | 管理截图、视频、追踪文件 |

---
