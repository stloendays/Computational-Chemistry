# A CI-NEB 待审输入（尚未提交）
来源：已收敛的普通 NEB 1535023。00/07 为原端点，01–06 POSCAR 来自各像收敛 CONTCAR。
物理设置、k 点、6 个中间像、EDIFFG=-0.05 eV/Å 保持不变。
改变：LCLIMB=.TRUE.；ISTART=1 / ICHARG=0，读取每个像自己的收敛 WAVECAR。
提交前在 Vanda 独立目录 neb_3x3/A_cineb 中补齐 POTCAR、00/07 OUTCAR、01–06 各自 WAVECAR（不传到本地）。
提交前再确认无重复作业、dist.pl 端点和逐像间距、WAVECAR 全部可用，并刷新 CFP04-CF-046 额度。
PBS：2节点72核，72 h，看门狗250200 s。不跑stage A。
未执行 qsub；需用户决定后才启动 CI-NEB。收敛后另做 TS 振动验证，不能只凭CI-NEB称为已验证TS。
