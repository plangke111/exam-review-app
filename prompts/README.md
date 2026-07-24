# 批改系统提示词目录

## 如何使用

### 方式一：使用官方提示词

将你的提示词文件放到此目录，文件名对应如下：

| 文件名 | 对应任务 |
|--------|----------|
| `english_big.md` | 英语大作文（20分） |
| `english_small.md` | 英语小作文（10分） |
| `politics.md` | 政治分析题（10分/题） |

### 方式二：从示例模板创建

```bash
cp english_big.md.sample english_big.md
cp english_small.md.sample english_small.md
cp politics.md.sample politics.md
```

然后编辑 `.md` 文件，替换为你自己的评分标准。

### 提示词要求

每个提示词文件必须：
1. 描述阅卷专家角色和评分标准
2. 说明输入 JSON 字段
3. 明确输出 JSON 格式（程序解析 JSON 展示结果）

### 安全提醒

- `*.md` 文件不会被提交到 git（已在 `.gitignore` 中排除）
- `*.sample` 文件是示例模板，可以提交
- 不要把包含敏感评分策略的提示词提交到公开仓库

## 自定义提示词

你可以为不同题型创建不同的提示词文件，只需：
1. 在此目录创建 `xxx.md` 文件
2. 在 `src/essay_grader/config.py` 的 `PROMPT_FILES` 中添加映射
