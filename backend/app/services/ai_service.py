import random

MOCK_CONTENTS = {
    "marketing": """# {title}

## 产品概述

{product_name} 是一款面向 {target_audience} 的创新产品。它采用了先进的技术架构，为用户提供了卓越的使用体验。

## 核心优势

1. **高效性能**：处理速度提升 300%，大幅降低等待时间
2. **智能适配**：自动识别用户需求，提供个性化推荐
3. **安全可靠**：企业级数据加密，保障信息安全

## 使用场景

- 日常办公效率提升
- 团队协作优化
- 数据分析与决策支持

## 总结

{product_name} 将成为您工作中不可或缺的得力助手。""",

    "tech_doc": """# {title}

## 1. 概述

本文档描述了 {product_name} 系统的技术架构和实现细节。

## 2. 系统架构

### 2.1 前端层
- Vue 3 + TypeScript
- Element Plus UI 组件库
- Pinia 状态管理

### 2.2 后端层
- Python FastAPI 异步框架
- SQLAlchemy 2.0 ORM
- PostgreSQL 数据库

### 2.3 部署架构
- Docker 容器化部署
- Nginx 反向代理
- 数据持久化存储

## 3. API 接口

所有接口遵循 RESTful 规范，统一前缀 `/api/v1/`。

## 4. 安全设计

- JWT Token 认证
- bcrypt 密码哈希
- RBAC 角色权限控制""",

    "social_media": """🚀 {product_name} 正式上线！

还在为 {target_audience} 的痛点烦恼吗？试试我们的全新解决方案：

✅ 操作简单，5 分钟上手
✅ 效率提升 300%
✅ 安全可靠，数据加密

立即体验 → [链接]

#效率工具 #创新产品 #{target_audience}""",

    "default": """# {title}

## 背景

在当今快速发展的数字化时代，{target_audience} 面临着前所未有的挑战和机遇。

## 解决方案

{product_name} 提供了一套完整的解决方案：

1. **需求分析**：深入了解用户痛点
2. **方案设计**：量身定制最优方案
3. **实施落地**：高效执行，快速见效

## 预期效果

- 效率提升：预计提升 200-500%
- 成本降低：平均节省 30% 运营成本
- 满意度：用户满意度达 95% 以上

## 下一步

联系我们获取更多详情，开启效率革命之旅。""",
}


def mock_generate(category: str | None, variables: dict | None, title: str = "AI 生成内容") -> dict:
    template_key = category if category in MOCK_CONTENTS else "default"
    template = MOCK_CONTENTS[template_key]

    vars_used = variables or {}
    vars_used.setdefault("title", title)
    vars_used.setdefault("product_name", "智能助手")
    vars_used.setdefault("target_audience", "企业用户")

    text = template
    for key, value in vars_used.items():
        text = text.replace(f"{{{key}}}", str(value))

    token_usage = random.randint(500, 2000)
    generation_time_ms = random.randint(800, 3000)

    return {
        "generated_text": text,
        "token_usage": token_usage,
        "generation_time_ms": generation_time_ms,
    }
