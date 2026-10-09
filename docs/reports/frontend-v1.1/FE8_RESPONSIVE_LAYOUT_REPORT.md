# FE-8 全站响应式布局与固定导航优化报告

日期：2026-10-09。状态：HUMAN REVIEW PENDING。
Git Branch：main；Base / Current HEAD：5356e763b1de0cdab74e9ed3233d121e5a2d98b0。

## 根本原因与实现

原 shell 使用 flex + min-height:100vh，文档随内容增长；侧栏和顶栏处于文档滚动流。双栏部分使用不受约束的 fr，证据页内联宽度阻止断点生效，助手 min-height:530px 与 max-height:65vh 叠加，图表仅监听窗口 resize。

改为 100dvh Grid：250/64px 导航、64px 顶栏、minmax(0,1fr) 主内容。html/body/#app 不滚动，main 独立纵向滚动。侧栏品牌和底部环境固定，仅菜单滚动。没有对所有元素统一隐藏溢出。路由变化后主内容归顶。

统一尺寸变量、clamp 间距及图表高度；1600/1200/768/480 断点。表格自身水平和纵向滚动，ID 单行省略、完整 tooltip 和复制。证据列表独立滚动，分页保留，图片 contain 且高度随视口。聊天采用剩余视口高度，消息独立滚动，输入框在底部，侧面板独立滚动。小屏上下布局。

图表监听 ResizeObserver，并在卸载时 disconnect/dispose；主题变化重绘，不重新创建实例。环形图取消容易越界的外部标签，完整中文图例及悬停数量/比例保留；趋势关闭 smooth，数据不变。刷新调用当前页服务，不重建监控、不清空报告或聊天。

## 修改文件

- front/src/layouts/MainLayout.vue
- front/src/styles/main.scss
- front/src/components/charts/EChart.vue、EChart.test.js
- front/src/utils/charts.js
- front/src/views/OverviewView.vue、MonitoringView.vue、EventsView.vue、EvidenceView.vue、StatisticsView.vue、AIReportView.vue、AIAssistantView.vue
- 本报告、测量 JSON、screenshots/fe8-*.png、治理状态文档及本次 worklog

新增依赖：无。API、Python 服务、SQLite schema、检测/跟踪、权重、规则和 Agent 权限均无修改。

## 实际浏览器验收

运行地址：http://127.0.0.1:8765，FastAPI 提供真实 Vue 构建资源与 API。

| 视口 | 页面数 | DOM 宽度及主内容溢出 |
|---|---:|---|
| 1920×1080 | 7 | PASS |
| 1600×900 | 7 | PASS |
| 1440×900 | 7 | PASS |
| 1366×768 | 7 | PASS |
| 1280×720 | 7 | PASS |
| 1024×576（1280×720 的 125% 等效 CSS 视口） | 7 | PASS |
| 390×844 | 7 | PASS |

49 次检查全部满足 documentElement.scrollWidth == clientWidth、body.scrollWidth == clientWidth、main.scrollWidth == main.clientWidth。宽页面表格内部溢出允许，记录其他具体越界元素，最终无未解释越界。数据见 FE8_BROWSER_MEASUREMENTS.json。手机检查发现日期筛选条最小宽度撑开父项，修复后主内容 311/311px。

总览 1280×720：main 滚动到 317.33px，文档 scrollTop=0；header y=0/h=64，sidebar y=0/h=720，brand y=0/h=76，footer y=664/h=56，滚动前后相同。

统计页折叠导航：图表宽度由 650/304/477/477 变为 774/366/570/570，canvas 与容器等宽，每个图表始终一个 canvas。浅/深主题和真实刷新入口已操作检查。

35 张最终真实桌面截图：screenshots/fe8-{overview,monitoring,events,evidence,statistics,ai-report,ai-assistant}-{1920,1600,1440,1366,1280}.png。原设计图未用作运行时页面。

## 测试与功能回归

- npm --prefix front run build：PASS；仍有既有 >500kB bundle 提示。
- npm --prefix front run test：4 PASS（路由/API边界 3，容器 resize/释放生命周期 1）。
- .venv-frontend-api/Scripts/python.exe -m pytest tests/integration/test_frontend_api.py -q：2 PASS，1 个第三方弃用提示。覆盖 SQLite 汇总、分页筛选、状态持久化、证据正确/损坏、受限图像读取、停止接口、报告模板降级、只读助手。
- .venv-frontend-api/Scripts/python.exe -m scripts.frontend_mp4_smoke：PASS，隔离临时 SQLite/证据目录，真实冻结资源完成47帧、74次检测观测、1个PPE_UNKNOWN事件、2次通道告警，has_preview=True。
- 七页真实路由、真实 SQLite 数据显示、表格 ID 省略与详情入口、证据列表与元数据、统计图表、折叠导航、主题与刷新检查完成。
- git diff --check：PASS（已有 LF/CRLF 提示，无空白错误）。

## 限制及门禁

实际浏览器125%缩放：NOT_EXECUTED。内置浏览器 ctrl+plus / ctrl+equal 未改变 devicePixelRatio 或 CSS 视口；没有将等效视口冒充实际缩放。需要人工在支持浏览器缩放的窗口补验。

实际配置的助手 Provider 在浏览器请求超过既有15秒客户端超时，错误正常展示；现场 Provider 成功回答不记 PASS。无 Provider 的本地降级由真实 API 集成测试通过。长报告/长聊天压力及 USB/RTSP 设备本轮未重测。状态更新仅在隔离测试库验证，没有修改用户现有事件。

本轮未重新跑全部旧 Streamlit 测试；上一轮完整回归记录保留。本轮无后端改动。P9-C 资源生命周期风险仍为 PARTIAL，不宣称修复。

回退：人工保留/还原本次前端布局改动后重新 npm run build；旧 Streamlit 入口仍保留。部署构建更新后浏览器须刷新，避免旧页面引用被替换的 hash chunk。

Commit：NOT EXECUTED；Push：NOT EXECUTED；Tag：NOT CREATED。
Final Status：HUMAN REVIEW PENDING（真实125%缩放与现场Provider成功仍待验）。
