# 固定事件类型缓存音频

Changed: infra/alerts/tts.py（播报内容）、api/windows_speech.py（预生成/受限短句/直接播放）、api/queued_tts.py（准备和缓存清理）、tests/unit/test_tts_alert.py、治理交接记录。
Reason: 三类固定内容无需每次合成；启动时生成约0.56秒，运行时只播放，可减少检测期间语音合成工作。Track ID/置信度仍保留事件记录，不再口播。
Validation: 20项语音/告警/API测试通过，实际三种WAV生成/校验/播放通过，compileall/diff通过。生成语音约0.555秒，缓存音频约2.5–2.6秒，播放进程CPU约0–0.016秒/条。未将单次测试推导为帧率提升。
Evidence: docs/reports/v1.2/TTS_CACHED_AUDIO_VALIDATION.json；tests/unit/test_tts_alert.py。
Risk: 缓存依赖本机Windows语音引擎；准备失败则明确不可用，不伪造成功；不播放任意用户指定路径。临时缓存限定本对象创建目录，关闭时清理。原生播放挂起和P9-C/G-CFR风险仍保留。
Not Verified: 本次方案的真实MP4与现场听音/流畅度未复验（上一版两次MP4记录不冒充缓存方案验证）。自动审批拒绝8775停止/重启命令，仅说明策略阻止，当前运行实例未加载本次修改。
Next Step: 人工重启8775加载后执行MP4听音/流畅度检查。未commit/push/tag。
