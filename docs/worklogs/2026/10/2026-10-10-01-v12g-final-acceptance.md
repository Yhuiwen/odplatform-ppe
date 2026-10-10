# V1.2-G 最终集成验收交接 — 2026-10-10

Changed: 显示格式、EventId复制反馈、类型色/32px时间轴、导航Hover区分、API版本识别、G真模型与安全测试；新增报告/JSON/真实截图/用户指南，更新Phase9/状态/Changelog/门禁/风险。

Reason: 执行已授权G验收与实际界面缺陷修复；F审核已在G任务中确认。保留B–F和所有用户文件。

Validation: Vue34 PASS/build PASS；非模型API109 PASS；冻结819 PASS/12独立API文件SKIP；真实8用例分轮有PASS。首轮真实6 PASS/1 FAIL（CFR），随后严格十探测、三视频、混合FIFO通过但根因未证实。四桌面尺寸40独立组合通过；播放结尾、证据放大、复制反馈与实际下载SHA/ZIP CRC通过。文档治理/参考资产38 PASS与源码数据资产21 PASS，两个集合共59 PASS；最终Vue复验34 PASS/build PASS。

Evidence: docs/reports/v1.2/V12_G_FINAL_ACCEPTANCE_REPORT.md；G_MEDIA_EVIDENCE.json、G_RUNTIME_EVIDENCE.json、G_DOWNLOAD_EVIDENCE.json、screenshots/G_BROWSER_MEASUREMENTS.json、G_BROWSER_INTERACTIONS.json及g-*.jpg；测试完整日志保留仓库外Temp/v12g-*.log。

Risk: G-CFR-01/RISK-030核心准入偶发拒绝，发布BLOCKED；任务结束RSS有限增长，不宣称长时稳定；P9-C PARTIAL/FROZEN不变。内部表格滚动、原渲染标签重叠及可信本机缓存边界保持。

Not Verified: FullHD/4K/长视频真实YOLO、640×480模型链、超过30分钟长稳、125%/多浏览器；未新启Streamlit浏览器。正式8768没有重启。

Next Step: HUMAN REVIEW PENDING。人工审阅G失败和证据，处理CFR根因后再决定发布。不得自动commit/push/tag。独立8775保留供审核，root在仓库外Temp/odplatform-v12g-jobs-20261010；旧8774与正式8768保持。Base/Current HEAD均1d283dcbe37d853dab3240ebe4cc6084c7be9e42。
