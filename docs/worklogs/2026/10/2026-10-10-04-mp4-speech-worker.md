# MP4语音工作线程及会话冷却隔离

Changed: api/queued_tts.py、api/windows_speech.py、api/main.py；EventsView.vue；tests/integration/test_queued_tts.py；阶段/状态/变更/门禁及真实媒体JSON。
Reason: 同步播音阻塞逐帧检测；原语音引擎跨监控线程复用；冷却键仅track/type导致不同视频Track ID冲突。
Validation: 后端20 PASS（队列非阻塞、跨会话隔离、会话内冷却保留、失败/满队列、线程一致性、敏感异常不外泄）；前端35 PASS和详情单项复验；build/compileall/diff PASS。真实指定MP4最终两次各570帧/2事件/6投递，语音4条均SAPI完成后delivered；独立SQLite/离线目录，无正式数据变更。
Evidence: docs/reports/v1.2/TTS_TWO_MP4_VALIDATION.json；docs/reports/v1.2/TTS_TWO_MP4_COOLDOWN_DIAGNOSIS.json；tests/integration/test_queued_tts.py。
Risk: 队列32、回执2048上限；满队列明确失败，不阻塞检测；停机最多等待5秒，原生播音永久挂起风险仍未证明关闭，P9-C保持。Windows原生SAPI速率换算至-10..10；使用已有PyWin32，无新增安装。核心AlertStatus仍保留原三状态，排队返回skipped/TTS_QUEUED，UI标为等待播报，最终回执由API覆盖；不伪报delivered。
Not Verified: 实际声音可听性/浏览器主观流畅度/长期压力；正式8775运行实例仍是前一版，先前自动审批拒绝重启，未绕过。冻结检测与规则不修改。
Next Step: 手动重启8775加载后进行人工听音和流畅度复核。无commit/push/tag，人工审核待定。
