# V1.2-G FINAL ACCEPTANCE REPORT

日期：2026-10-10（Asia/Shanghai）。**V1.2-G BLOCKED / HUMAN REVIEW PENDING**。

核心链路在成功任务中通过，但同一核验素材本轮仍发生一次推理前 CFR 拒绝。后续通过没有解释首轮失败，不能宣布所有强制门禁已通过；本次保留发布阻塞 `G-CFR-01 / RISK-030`，不创建里程碑 Tag。

## G1：仓库、历史与冻结基线

Branch：`main`。Base HEAD / Current HEAD：`1d283dcbe37d853dab3240ebe4cc6084c7be9e42`。B/C/D/E/F 未提交改动保留；F 审核通过由本次 G 授权确认。没有 reset、clean、stash、pull/merge、提交、推送或 Tag 操作。

已审查 AGENTS、治理文档、B–F 报告与 P9-C.3i 资源生命周期结论。仓库不存在独立 V1.2-A 报告，未虚构其文件或审核结论。现有 V1.1 Tag 指向相同 HEAD，候选 `v1.2-offline-media-analysis-complete` 不存在；历史 Tag 未移动。

| 冻结文件 | SHA256（重验不变） |
| --- | --- |
| EXP-001/best.pt | 1c144eef0dfa06b984dde760ea5501a11746b99c1f8a9ae581790241c3871f61 |
| inference.yaml | 0195c5f703474d888f2a59729989fb760408657db850922031af7166d383f76c |
| tracker.yaml | 42ec753ee1511b9de652a750b2d67a384f4aea95d56b43a98d287c877121f10a |
| association.yaml | be32af654ab76e4d1dd7e82c1a3fb0ffbbed2026e9711bea73fcacfc703073a6 |
| rules.yaml | ecf291090f3bd64cbf755dad2d00f68105d9301ca3ae97c275399c39cd3a623c |

core/services/infra、冻结配置、模型、训练数据、V1/V1.1 锁与 npm 锁未变；G 未新增依赖或修改 SQLite Schema。禁止下载/训练边界保持。

## G2：实际界面修复 — PASS

- 图片与视频置信度显示三位小数，Tooltip 保留 API 原值，单行显示，不改变检测数值。
- 事件 ID 单行省略、完整 Tooltip、复制按钮。实际浏览器显示“已复制”；拒绝剪贴板权限时提供手动复制提示，组件测试验证完整 ID 与拒绝路径。
- 时间轴使用真实视频秒数；32px 点击区域，NO_HELMET 红色、NO_VEST 黄色、PPE_UNKNOWN 紫色；时间文本、原生悬停提示、焦点边框、选中环及 aria-pressed。570 帧事件位置 22.1053% / 77.7193%，没有均匀分布。
- Hover 浅色背景与 Active 蓝色分离；实际各页面仅一个 Active，折叠及固定导航保留。
- manifest 字节数自动显示 B/KB/MB/GB，小 JSON/CSV 不再显示 0.00 MB。
- 未选择文件禁用提交；加载、上传进度未知、排队、处理、编码、取消、失败、中断、旧 D 未执行事件分析、零确认事件、视频解码失败和证据错误沿用实际状态/明确提示，不用 Mock 回退。

G 修改 `front/src/utils/offline.js`、ImageDetectionPanel、VideoDetectionPanel、样式，新增 EventId 组件与显示/复制测试；API health 增加 `api_version=1.2.0`、OpenAPI 版本相同。版本元数据不表示已经发布。

## G3：图片真实模型链路 — PASS

在仓库外 pytest 临时 root，用冻结模型经 HTTP 上传、单 Worker、现有 YOLO/Renderer、产物下载完成八种输入。变体来自已有公开工地 JPG；空图为明确的白色测试输入，实际执行相同模型，没有假推理。

| 输入 | 标准化/输出尺寸 | 检测框 / 疑似项 |
| --- | --- | --- |
| JPG / JPEG | 1024×766 | 各 5 / 2 |
| RGB PNG / RGBA PNG | 1024×766 | 各 5 / 2 |
| 灰度 PNG | 1024×766 | 6 / 3 |
| 非标准宽高比 PNG | 1200×300 | 1 / 0 |
| EXIF orientation=6 JPG | 766×1024 | 1 / 1 |
| 无目标白图 PNG | 320×240 | 0 / 0 |

逐项复核原始输入字节与 SHA、PNG 解码/尺寸、JSON 计数、五类过滤、原尺寸框边界、四产物 SHA、ZIP 精确成员/CRC及历史重新查询。单帧不产生时序确认事件。透明白底策略另外由现有图片契约单元测试覆盖；RGBA 实测用 RGBA 模式公开图，不声称与灰度/方向变体检测数相同。坏图、空文件、类型伪装、字节/像素上限另由负向 API/Processor 测试覆盖。

真实浏览器 JPG Job：`9e0d177d7d38422d9de43ad20e8cb221`，原图/标注/历史入口正常。证据：[G_MEDIA_EVIDENCE.json](G_MEDIA_EVIDENCE.json)。

## G4：视频完整性 — 成功任务 PASS / CFR 准入 BLOCKED

重新运行原 D 与 E 真模型链路；E 对每个帧 ID 实际 infer_frame 调用进行观测，47/570 均逐帧一次，无跳帧、重复帧或二次推理。完整输出 FFprobe 解码、时间戳、帧数、JSONL、哈希和 ZIP 校验通过。

| 项目 | 47 帧 | 570 帧 |
| --- | --- | --- |
| 解码 / 推理 / 标注 / 写入 / 输出解码 | 均 47 | 均 570 |
| 原始输出分辨率 | 1280×720 | 1280×720 |
| 播放 FPS | 24000/1001 | 30 |
| 输出时长 | 1.960292 秒 | 19 秒 |
| 累计检测框 | 77 | 1829 |
| E 确认事件 | PPE_UNKNOWN 1 | NO_HELMET 1、NO_VEST 1 |
| 原图 + 标注证据 | 2 张 | 4 张 |
| MP4 SHA256 | c985a26ab6b7e1f17411ed9f1a33f8bdc6fac4110d84f075d911e3d56cac74f6 | c9a9e52644d122711ada73a4aeee68a24ca5fac4f66f26829b5034f5b5510488 |

H.264/libx264、CRF18、medium、yuv420p、faststart、无音轨；CRF18 为有损，原始证据 PNG 是未改动触发帧，输出视频不宣称像素无损。源含音轨时需明确确认移除。570 源容器时长 19.017211 秒与输出 19 秒差值小于 1/30 秒；以帧级容差及实际帧数验收，不要求元数据字符串完全相同。三次 G 资源输出的 FPS/像素格式/尺寸/音轨/时长还按证据 JSON 后置复核。

### G-CFR-01 首轮失败与后续检查

首轮真实集合 **6 PASS / 1 FAIL**（288.55 秒）。失败 Job `75d264ea365c427786e7da81f274e42b`：`UNSUPPORTED_TIMING`，frame488 间隔6000 ticks，预期3000，FPS30/time_base1/90000；processed_frames=0，输入 SHA `a734a43322442737da15979709f83d06819b9a94f9112cdf3ee0c7a1592d0695` 与已核验资源一致。没有发布假成功产物。

同素材随后十次独立严格 probe_cfr 均 570 帧通过，另行运行的三视频资源测试也通过。生产代码没有自动重试、没有放宽 CFR、没有重新编码输入或修改模型/规则。E 已记录相同现象，本轮复现仍未确认原因为媒体、探测器或运行环境；**后续 PASS 不抵消未解释的核心准入失败**，保留发布阻塞。

640×480 没有新增真实模型全链路证据；旋转元数据/非法时间戳/奇数尺寸有负向契约测试。1920×1080 仅现有纯编码三帧测试通过，**真实 FullHD YOLO：NOT_EXECUTED**；4K、长视频真实模型及长稳：**NOT_EXECUTED**。未用合成编码替代真实模型验收。

## G5：事件、证据与实时隔离 — PASS（测试覆盖范围）

复用冻结 ByteTrack、关联、Compliance/EventEngine 与 SQLiteRepository/EventIngest，双证据直接取同一触发帧。持续违规去重、不同 Track/类型、恢复/冷却、未知语义、空帧、轨迹丢失、跨 Job 隔离及失败不发布由现有 E 单元/API 回归覆盖。

真实 47/570 验证事件数量、原尺寸双 PNG SHA、事件与索引/CSV/ZIP链接；原图与源视频解码触发帧逐像素一致。570 轨迹 ID7、未知关联观测46，不将它们描述为独立人员数或未知事件。内部数据库 WAL checkpoint/关闭、迁移/完整性与发布关系经 E 契约测试验证，events_db 不可直接下载且不入 ZIP。

实时事件库总数在真实图片、视频及顺序执行前后相同；collector 不连接实时 Web/TTS 投递服务，源码边界与 E 测试保留，没有录音或远端告警投递验收。SQLite/证据/导出损坏有负向测试，不把异常标记 VERIFIED。

## G6：队列、取消、恢复与有限资源测试 — PARTIAL

混合真实 FIFO：47帧视频 → JPG → 47帧视频；另一个排队 JPG 取消，95 次真实推理，前三项顺序、同模型身份、校验下载及取消任务无产物通过（37.44秒）。处理/编码取消、并发领取、单实例锁、重启 INTERRUPTED/保留QUEUED/损坏输入隔离、准入互斥、阻塞编码超时及资源清理由 B–E API/单元契约测试覆盖。

测试前已限定计划：同进程/持久 Worker/共享模型顺序三次 570 帧，目标在30分钟以内；0.1秒采样父 RSS、CPU、墙钟、产物/数据库/证据字节。判据：全部完整帧和基线结果、每任务释放准入、FFmpeg无残留、最终Worker退出；RSS仅观察趋势，不设置未经验证的长期稳定结论。实际三次共302.26秒，没有执行需要另行确认的超过30分钟长稳。

| 循环 | 墙钟秒 / 有效FPS | CPU秒 | 任务结束 RSS字节 | 产物字节（含ZIP） | DB / 双证据字节 |
| --- | --- | --- | --- | --- | --- |
| 1 | 108.968 / 5.231 | 52.594 | 454979584 | 11342949 | 106496 / 1521723 |
| 2 | 91.079 / 6.258 | 45.094 | 455790592 | 11342925 | 106496 / 1521723 |
| 3 | 98.578 / 5.782 | 53.375 | 460447744 | 11342937 | 106496 / 1521723 |

峰值 RSS **562679808 字节**；关闭后 **454774784 字节**。模型身份相同，Worker最终不存活、FFmpeg子进程0。第三任务结束RSS比首任务增加5468160字节；关闭后下降，**样本不足以判定平台或长时有界**。同机同期另有验证进程，速度不作为独占机器性能承诺。P9-C保持 PARTIAL/FROZEN，不能以这五分钟测试宣布修复。证据：[G_RUNTIME_EVIDENCE.json](G_RUNTIME_EVIDENCE.json)。

## G7：API 安全与传输 — PASS（本机应用边界）

字节/类型/文件名/路径/UUID/跨Job/未完成访问、Origin/Host/cross-site、上传中断、磁盘不足、写盘权限失败、缺少探测器、坏MP4、证据SQLite/PNG损坏、CSV公式和ZIP路径/CRC由独立 API 与既有单元测试覆盖。新增507/500/503验证不泄露私有路径或堆栈，暂存清理正确；旋转测试是元数据负向契约，不冒充真实旋转视频推理。

标准完整GET、HEAD无body、206闭区间/开放/后缀Range、416 Content-Range、非法Range400、同源访问、跨站403、no-store、有界哈希缓存失效均通过。大文件先完整 SHA 校验，再复用签名匹配缓存，避免每个 Range 全量扫描；本机恶意进程伪造stat/校验后并发篡改不在可信写一次产物的保证内。没有任意路径接口或新增API密钥；模型/RTSP秘密不进入前端持久化。

## G8：浏览器与交互 — PASS（四种桌面窗口）

独立同源实例 `127.0.0.1:8775`，root在仓库外 Temp，单Worker；正式8768没有重启。测试结束后只重启本次8775并确认原两完成任务保留，加载新增 API版本信息；原8774也未中断。

1920×1080、1600×900、1366×768、1280×720：原七页 + 离线图片/视频/历史共40独立组合，另一次重复测量共41条。document/main无横向溢出，内部表格可以滚动；header/aside y均0，单Active导航。保存真实运行截图 `screenshots/g-*.jpg` 与 [测量记录](screenshots/G_BROWSER_MEASUREMENTS.json)。没有使用设计参考图作为运行界面。

浏览器实际视频 Job `f723c3d654034baa92822f0e77a8396b`：570帧完成，1280×720，播放器从开始至19秒结束，ended=true/error=null；4.20秒时间轴定位、32px命中、双图证据及放大、事件ID复制反馈、历史/导航及刷新恢复可用，后端任务数仍2，无重新提交。无捕获的error日志。实际下载ZIP/MP4 SHA与manifest一致，ZIP CRC通过：[下载证据](G_DOWNLOAD_EVIDENCE.json)、[交互记录](screenshots/G_BROWSER_INTERACTIONS.json)。浏览器125%缩放与其他浏览器：NOT_EXECUTED。

## G9：测试命令与结果

| 环境 / 集合 | 结果 |
| --- | --- |
| front：npm test | 最终34 PASS，33.27秒；首轮33 PASS后新增复制反馈测试 |
| front：npm run build | PASS，18.08秒；已有大chunk提示保留 |
| 独立API B–F与新增安全测试 | 最终109 PASS，68.25秒；首轮106及中轮107 PASS |
| 原C/D/E真实模型5项 + G八图片变体 | 首轮6 PASS/1 G顺序视频 FAIL，288.55秒；未覆盖失败记录 |
| G三顺序真实视频重新验证 | 1 PASS，302.26秒；不称自动重试修复 |
| G真实混合FIFO/排队取消 | 1 PASS，37.44秒 |
| 冻结V1 Python全量 | 819 PASS/12独立API文件SKIP，236.93秒 |
| compileall api services web offline | PASS |
| git diff --check | PASS；仅已有LF/CRLF提示 |

非模型API集合包含四份offline unit、test_frontend_api、test_offline_api、test_offline_video_recovery、test_offline_events_api、test_offline_frontend_api。真实集合：test_offline_g_acceptance、test_offline_image_real、test_offline_video_real、test_offline_events_real。独立真实测试有8个不同用例的通过证据，分轮执行，不描述为“同一轮117全PASS”；初轮失败仍是 G 阻塞。冻结环境不安装API依赖，12个文件级SKIP由独立API环境覆盖，不计作通过。

最初新增G测试收集报 psutil缺失，是在 api.main 附加冻结runtime之前导入psutil；按现有real测试导入顺序修正，没有安装/改变依赖。初始记录中的仅非零事件类型字典按已有稀疏契约读取，零值用get(key,0)；生产契约未改。测试输出在仓库外Temp保存，关键数据归档为本目录JSON。

## G10：文档与部署 — 已同步

新增 [离线用户指南](../../V1_2_OFFLINE_USER_GUIDE.md)：图片/视频/取消/历史/证据/下载流程、默认限额、准确类别语义、CRF18有损/无音轨、有限规格与长稳、单实例、资源隔离、环境禁用回退、PowerShell启动/Ctrl+C停止。README、部署文档、Phase9、状态、Changelog、门禁与风险记录同步。旧Streamlit保留并由冻结业务/页面回归覆盖；本轮未另开实际Streamlit浏览器服务器。

## G11：发布准备 — 完成检查，发布阻塞

累积文件清单：[G_CHANGED_FILES.txt](G_CHANGED_FILES.txt)。G代码仅限显示优化、API版本识别及验收测试；其余为B–F积累实现和文档。没有新依赖/锁漂移；新增独立V1.2锁属于B，不修改冻结演示锁。dist、运行root、SQLite、视频/原始输入、模型与私有配置未加入Git；没有超过1MiB的新增候选文件。截图为报告证据，原始设计图不是运行资源。敏感模式扫描没有真实密钥/RTSP凭据匹配，候选Tag未创建。

### 未决与发布判定

- **G-CFR-01/RISK-030：BLOCKING**。已核验570帧素材偶发CFR拒绝，本轮复现，根因未证实。需要保留失败输入指纹/探测输出并调查；禁止通过放宽验收、隐藏失败或自动重试获得PASS。
- P9-C原生产资源边界仍PARTIAL/FROZEN；五分钟顺序视频不证明长期平台，原实时fresh-worker问题未改。
- FullHD/4K/长视频真实模型与长期资源、640×480模型链、125%及多浏览器尚未执行；不能宣称全规格通过。
- 视频标签局部重叠为原Renderer限制；相邻时间轴事件仍可能靠近，可从列表定位。首次大文件哈希、可信本机缓存边界、跨root资源互斥缺失保持记录。
- 标准运行root在仓库内时生成ZIP仍可能触发旧P1源码资产扫描；本次验证root全部在仓库外，没有放宽该门禁或删除用户数据。

**Final Status：HUMAN REVIEW PENDING。Commit：NOT EXECUTED。Push：NOT EXECUTED。Tag：NOT CREATED。**

不得把本报告当作完整发布许可。人工审核后先处理准入阻塞，再决定是否授权发布；不自动执行 Git 操作。


## 最终后置复核

- 文档治理/参考资产38 PASS（57.64秒）与源码数据资产21 PASS（35.13秒），两个不同集合共59 PASS。没有为运行ZIP放宽训练/源资产门禁。
- 最后增加表格行切换时复位复制反馈，避免新ID沿用旧“已复制”；Vue全量再次34 PASS（33.27秒），build PASS（18.08秒）。
- 最终累积138个变动候选文件（含B–G及报告截图），无单文件超过1MiB；候选源文本敏感模式扫描0匹配，dist/任务root/私有配置被忽略，模型仅占位目录跟踪。完整清单已更新。
- frozen模型/四配置指纹、core/services/infra/冻结锁无diff、git diff --check、HEAD/tag状态复核通过。正式8768 PID22792与原8774 PID16720不变；本次8775 PID14488重启后health版本1.2.0、原两完成Job保留，供审核。
- 仍不关闭G-CFR-01/RISK-030或P9-C，不执行commit/push/tag。最终BLOCKED / HUMAN REVIEW PENDING。


## 2026-10-10 发布例外补充

原始BLOCKED判定及失败记录保留。用户随后明确授权暂缓G-CFR-01/RISK-030及P9-C发布阻塞，在版本统一与缓存音频/助手真实联调补齐后发布V1.2。见ADR-029和V12_RELEASE_CHECK.md。本授权不等于根因修复、完整规格PASS或长期稳定PASS。
