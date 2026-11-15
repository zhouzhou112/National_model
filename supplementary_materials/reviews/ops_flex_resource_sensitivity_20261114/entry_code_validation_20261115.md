## 2026-11-15 柔性资源量敏感性入口与回归完成（第一批，29e3782d）

源码提交29e3782d：只新增按列/状态容量界入口、双向定价及显式五轮测试控制；约束、目标、生产数值设置不改。新增44线程profile、两套作者输入路径/参与率覆盖及运行时四服务上界审计。原MPS关闭入口逐字节相同，旧定价JSON/CSV金样本一致。完整回归535项覆盖：T550/Gurobi13.0.2通过533项，2项本机原归档补测通过；提交blob与远端测试源码LF SHA一致。

输入保守11项/开放12项原件SHA及T550安装后1,357,800行demand_gw文本相等；云端独立暂存原包SHA核验PASS。中性/两OPS/零签约24h工程门禁通过；单调性原浮点反向最大相对1.493e-15，按既有Cross2/1e-8的1e-7比较口径等价，原值保留。D1仅释放642城市链路且1h/24h通过；LATE24h自身解恒等性目标相对差6.11e-16、容量最大差3.36e-13。C2050自身BarPi仅作参考定价，margin0.005得到4481自由/28846下界/3359上界，清单SHA1c54c2630c2fb2010129f309def39b4a3ae26fab8acd9d0007790efff779cb4a，不是新解证书。

已修正本轮新增profile遗漏physical_v1校验分支的入口登记错误并加回归；未改变模型缩放。完整失败记录保留，实际启动profile的1h复核尚在T550新目录进行。尚未提交云端作业；下一步取回本轮1h结果、汇报五项门禁，逐案云端冻结/preflight通过才提交并release。只授权第一批三解加一测试；测试前5轮终止，后两批必须等待作者确认。不建监听、不读取凭据、不改旧release或论文模块。

命令/路径：`resume_validation_v7.py`、`check_production_profiles_1h.py`、`stage_cloud_inputs.py --resume-uploaded`；证据均在`reviews/ops_flex_resource_sensitivity_20261114/`（supplementary_materials下）。远端为`/home/zz2/National_model_server/ops_flex_resource_sensitivity_20261114/validation_runtime_v7`。云端输入暂存`National_model_cloud/_staging/ops_resource_sensitivity_20261114`；首次提取因登录Python版本不支持Path.is_relative_to停止，改用等价父路径校验后仅解包已核SHA的原上传文件，未重复上传/重建数据。
