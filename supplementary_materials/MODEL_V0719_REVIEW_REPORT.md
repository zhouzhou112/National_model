# CISPO 浼樺寲妯″瀷 V0719 鍏ㄩ潰瀹℃煡鎶ュ憡

**瀹℃煡鏃ユ湡锛?* 2026-07-19
**鎶ュ憡鐗堟湰锛?* V0719
**鏈湴浠撳簱锛?* `D:\codeenv\pycharmproject\National_RL\National_model`
**鏈湴 Git HEAD锛?* `f84143a`锛堟枃妗ｅ悓姝ユ彁浜わ級
**褰撳墠妯″瀷瀹炵幇鍩虹嚎锛?* `5a9f4ab`锛堝寘鍚?`1b6da28` 鐨勭渷闄呰緭鐢典慨姝ｏ級
**瀵圭収鏂囩尞锛?* `supplementary_materials/CISPO.pdf`锛?29 椤碉紝SHA256 `21B19A2065FF4F627413E89FD113E0DBCE0EA718BD1F760BD36EC233B1CF6A81`
**涓昏浠ｇ爜锛?* `cispo_model/master.py`銆乣cispo_model/monolithic.py`銆乣cispo_model/load_center.py`銆乣cispo_model/hydro.py`
**鎶ュ憡鎬ц川锛?* 浠ｇ爜涓庡叕寮忓鏌ワ紝骞朵簬 2026-07-19 缁啓 V0719 鏍℃瀹炴柦涓庨獙璇佽褰曘€傛姤鍛婂墠 1-10 鑺備繚鐣欏疄鏂藉墠瀹℃煡蹇収锛岀 11 鑺備负褰撳墠鏍℃鍚庣殑鏉冨▉鐘舵€併€?
---

## 1. 鎵ц鎽樿

### 1.1 鎬讳綋鍒ゅ畾

褰撳墠鐗堟湰涓嶆槸瀵?`CISPO.pdf` 鐨勯€愬紡绛変环澶嶇幇锛岃€屾槸涓€涓互 CISPO S4 涓烘牳蹇冦€佸湪鏁版嵁杈圭晫銆佺┖闂村垎鍖恒€佹按鐢点€佽法骞寸姸鎬佸拰鐪佸唴缃戠粶鏂归潰缁忚繃杈冨ぇ閫傞厤鐨勬墿灞曟ā鍨嬨€傚缓璁鏂囦腑浣跨敤浠ヤ笅琛ㄨ堪锛?
> **CISPO-inspired / CISPO-adapted China power-system planning model**锛岃€屼笉鏄湭缁忛檺瀹氱殑 **CISPO replication**銆?
涓嶈兘绠€鍗曞垽瀹氣€滃綋鍓嶄唬鐮佲€濇垨鈥淐ISPO.pdf鈥濇暣浣撲笂鍝竴涓粷瀵规洿鍚堢悊锛?
- 褰撳墠浠ｇ爜鍦ㄤ弗鏍煎姛鐜囧钩琛°€佽緭鐢垫柟鍚戙€佺粨鏋?QC銆佽法骞村閲?cohort銆佹暟鍊肩缉鏀俱€佹绾ф按閲忎紶鎾拰鑻ュ共鏁板绛変环绋€鐤忓寲鏂归潰鏇翠弗璋ㄣ€?- `CISPO.pdf` 鍦ㄦ牳鐢典笂鐣屻€佺敓鐗╄川瑁呮満涓婄晫銆?030 鐢垫睜涓嬬晫銆?2 涓數缃戝尯鍩熴€丆SP銆佸巻鍙叉皵璞″嘲鍊煎拰璁烘枃鍏紡闂悎鏂归潰鏇村畬鏁淬€?- 褰撳墠鏈€鍚堢悊鐨勭爺绌剁増鏈簲鏄簩鑰呯殑鈥滄牎姝ｈ瀺鍚堢増鈥濓細淇濈暀褰撳墠浠ｇ爜鐨勫伐绋嬪拰鏁板€兼敼杩涳紝鍚屾椂琛ュ洖璁烘枃涓閬楁紡鐨勫閲忚竟鐣岋紝骞跺皢鍋忕璁烘枃鐨勫亣璁炬樉寮忓垎灞備负 `replication`銆乣adapted` 鍜?`enhanced` 涓夌粍鎯呮櫙銆?
### 1.2 瀹℃煡鏃跺彂鐜般€佺幇宸插畬鎴愪慨姝ｇ殑鍥涢」闂

> **2026-07-19 鐘舵€佹洿鏂帮細** 浠ヤ笅鍥涢」宸插湪鏈湴 V0719 working tree 涓疄鐜板苟閫氳繃 24h 涓ユ牸姹傝В鍙婃暟鎹寘 smoke test锛涘叿浣撴暟鎹€佸叕寮忋€佸彲琛屾€т繚鎶ゅ拰楠岃瘉璇佹嵁瑙佺 11 鑺傘€備互涓嬫枃瀛椾繚鐣欎负鈥滀慨姝ｅ墠闂瀹氫箟鈥濓紝涓嶅啀浠ｈ〃褰撳墠浠ｇ爜缂哄彛銆?
1. **缂哄皯鏍哥數瀹归噺涓婄晫锛圫4-36锛?*
   `master.py:443-502` 鍙鍙?`nuclear_capacity_floor_by_year.csv` 骞跺缓绔嬩笅鐣?鏂板瀹归噺璐︽埛锛沗thermal_new[:, nuclear]` 娌℃湁鐪佺骇娼滃姏涓婄晫銆傚綋鍓嶇洰鏍囨垚鏈负姝ｏ紝鎵€浠ユā鍨嬩竴鑸笉浼氭暟瀛︽棤鐣岋紝浣嗗彲鑳藉湪鍐呴檰鐪佷唤鎴栭潪瑙勫垝鐪佷唤鏃犻檺鍒堕€夋嫨鏂版牳鐢碉紝鏀瑰彉瀹归噺缁勫悎鍜岀┖闂寸粨璁恒€?
2. **缂哄皯鐢熺墿璐ㄤ笌 BECCS 鍚堣瑁呮満涓婄晫锛圫4-34锛?*
   褰撳墠浠呮湁骞村害鐕冩枡绾︽潫 `master.py:716-721` 鍜?50% 鏈€浣庡湪绾跨害鏉?`monolithic.py:249-255`锛屾病鏈夎鏂囨牴鎹?`thermcal`銆佹晥鐜囧拰 6,132 绛夋晥灏忔椂鎺ㄥ鐨勭渷绾у閲忎笂闄愩€傜噧鏂欑害鏉熶笉鑳戒弗鏍兼浛浠ｈ鏈轰笂闄愶紝妯″瀷浠嶅彲鑳戒负浜嗗閲忚搴︽垨鎯噺寤鸿浣庡埄鐢ㄧ巼鐢熺墿璐ㄥ閲忋€?
3. **2030 鐢垫睜鏃㈡湁/鏀跨瓥涓嬬晫缂哄け**
   `master.py:567-589` 鐨?`storage_exogenous_floor` 鍒濆涓?0锛屽彧缁?PHS 鍐欏叆涓嬬晫锛?030 battery 涓嬬晫浠嶄负 0銆侰ISPO Table S16/S17 灏嗗凡鏈夌數姹犲強 2025 鐪佺骇鐩爣浣滀负 2030 涓嬬晫銆傚綋鍓嶅鐞嗕細浣庝及閿佸畾鐨勭數姹犲閲忥紝骞跺彲鑳介珮浼版ā鍨嬧€滆嚜涓婚€夋嫨涓嶅缓璁剧數姹犫€濈殑鑷敱搴︺€?
4. **DC 鍙嶅悜鍥哄畾闆跺彉閲忓簲浠庡彉閲忔灦鏋勪腑鍒犻櫎**
   `monolithic.py:511-520` 瀵瑰叏閮?411 鏉¤蛋寤婂垱寤?`flow_reverse`锛岄殢鍚庢妸 363 鏉?DC 璧板粖鐨勫弽鍚戝彉閲?UB 璁句负 0銆傚叏骞村洜姝ゅ寤猴細

   ```text
   363 DC edges 脳 8760 h = 3,179,880 fixed-zero variables
   ```

   杩欐槸褰撳墠鏈€鏄庣‘銆佽妯℃渶澶х殑鍙畨鍏ㄥ垹闄ゅ彉閲忓潡锛屽崰鍏ㄥ勾 `44,091,176` 涓彉閲忕殑绾?`7.21%`銆傚簲鍙 48 鏉?AC 璧板粖鍒涘缓鍙嶅悜鍙橀噺銆?
### 1.3 褰撳墠鍙В鎬х粨璁?
- 褰撳墠鍏ㄥ勾鎶曞奖锛氱害 `44,091,176 variables / 68,188,384 constraints / 515-524 million nonzeros`銆?- 涓ユ牸鏈湴 24h锛歚350,024 / 261,249 / 1,812,454`锛孏urobi `OPTIMAL`锛?2.00 s锛宍solution_qc=PASS`锛?9/29 鍗曞厓娴嬭瘯閫氳繃銆?- 涓ユ牸鏈嶅姟鍣?168h锛歚1,071,032 / 1,392,960 / 10,100,058`锛宍OPTIMAL`锛?66.45 s锛宍solution_qc=PASS`銆?- 2026-07-19 16:01锛圲TC+8锛夌幇鍦烘牳楠岋細鏈嶅姟鍣?HEAD `5a9f4ab`锛涙柊鐗?744h 姝ｅ湪杩愯锛屽凡瀹屾垚鏋勫缓锛歚3,955,064 variables / 5,919,746 constraints / 43,707,940 nonzeros`锛屾瀯寤哄嘲鍊?RSS `5.069 GiB`锛沚arrier 浠嶅湪杩唬锛屽皻鏃?`solve_report.json` 鎴?`solution_qc.json`銆?- 鍗充娇 744h 閫氳繃锛屽畠浠嶅彧鏄眰瑙ｅ櫒宸ョ▼闂ㄦ锛涚敱浜庝笂杩板閲忚竟鐣岀己鍙ｏ紝涓嶈兘鎶婂綋鍓?744h 缁撴灉瑙嗕负鏈€缁堢瀛︽ā鍨嬮獙鏀讹紝涔熶笉搴旂珛鍗冲惎鍔?8760 浼樺寲銆?
---

## 2. 瀹℃煡杈圭晫涓庤瘉鎹瓑绾?
鏈姤鍛婃寜浠ヤ笅浼樺厛绾у垽鏂ā鍨嬩簨瀹烇細

1. 褰撳墠 Git 宸ヤ綔鏍戝拰鐢熶骇鍏ュ彛瀹為檯璇诲彇鐨勪唬鐮侊紱
2. `CODEX_HANDOFF.md` 鐨?`Current validated snapshot`锛?3. 鏈湴鍜屾湇鍔″櫒 `build_report.json`銆乣solve_report.json`銆乣solution_qc.json`锛?4. `CISPO.pdf` S4 鍘熷鍏紡椤碉紝骞跺鍏抽敭鍏紡椤佃繘琛屼簡 PNG 娓叉煋鏍搁獙锛?5. `cispo_full_lp_model_spec.md` 浠呬綔涓烘湰鍦拌В閲婃枃妗ｏ紝涓嶄唬鏇?PDF 鎴栦唬鐮佷簨瀹炪€?
鏈閲嶇偣鏍搁獙鐨?PDF 鑼冨洿鏄枃浠剁 70-93 椤碉紙姝ｆ枃椤?63-86锛夛紝瑕嗙洊鍙橀噺銆佺洰鏍囧嚱鏁?S4-1a-o銆佺害鏉?S4-2 鑷?S4-77锛涘彟鏍搁獙浜嗘按鐢点€佸偍鑳姐€丷UC 鍜岃緭鐢佃緭鍏ョ珷鑺傘€?
---

## 3. 褰撳墠浼樺寲鍙橀噺鏋舵瀯

### 3.1 鎬讳綋灞傜骇

```text
瑙勫垝骞村閲忓彉閲忥紙2030/2040/2050/2060锛?鈹溾攢 0.25掳 VRE site-technology capacity
鈹溾攢 province-technology thermal/nuclear capacity and CCS retrofit
鈹溾攢 station-level hydro capacity
鈹溾攢 province-technology storage capacity
鈹溾攢 interprovincial corridor capacity
鈹溾攢 spur/trunk/intra-load-center network augmentation
鈹斺攢 province-technology DAC capacity and annual CO2 allocation

灏忔椂杩愯鍙橀噺锛圚=8760锛?鈹溾攢 province-technology VRE dispatch and availability
鈹溾攢 continuous capacity-based thermal RUC
鈹溾攢 storage charge/discharge/SOC/reserve
鈹溾攢 province ROR dispatch and station reservoir water balance
鈹斺攢 corridor forward/reverse flow

骞村害鑰﹀悎鍙橀噺
鈹溾攢 biomass/carbon/capture/source-sink accounts
鈹斺攢 278 load centers + 517 intraprovincial annual energy edges
```

### 3.2 鍙橀噺鍧楁竻鍗?
| 妯″潡 | 浠ｇ爜鍙橀噺 | 缁村害 | 鍗曚綅 | 鎬ц川 |
|---|---|---:|---|---|
| VRE 瀹归噺 | `vre_capacity`, `vre_new` | 36,686 脳 2 | GW | 瀹归噺鍐崇瓥涓庨噸澶嶈处鎴峰彉閲?|
| VRE 杩愯 | `vre_generation`, `vre_available` | 31 脳 4 脳 H 脳 2 | GW | 鐪佺骇骞剁綉鍑哄姏锛泂ite CF 绋€鐤忚仛鍚堣緟鍔╅噺 |
| 鐏數/鏍哥數瀹归噺 | `thermal_capacity`, `thermal_new` | 31 脳 11 脳 2 | GW | 瀹归噺鍐崇瓥涓庢柊澧炶处鎴?|
| CCS 鏀归€?| `thermal_retrofit_to_ccs` | 31 脳 5 | GW | 闈?CCS 杞?CCS |
| RUC | `online`, `startup`, `shutdown`, `thermal_gross_generation`, `ramp_magnitude` | 31 脳 11 脳 H 脳 5 | GW | 杩炵画 clustered RUC |
| 姘寸數瀹归噺 | `hydro_capacity`, `hydro_new` | 2,030 脳 2 | GW | 绔欑偣瀹归噺鍐崇瓥涓庢柊澧炶处鎴?|
| ROR | `ror_available`, `ror_generation` | 31 脳 H 脳 2 | GW | 绔欑偣 CF 鑱氬悎銆佺渷绾ц皟搴?|
| 姘村簱姘寸數 | `reservoir_turbine_flow`, `reservoir_spill_flow`, `reservoir_volume` | 620 脳 H 脳 3 | `10^3 m3/s`銆乣10^6 m3` | 绔欑偣姘撮噺鐘舵€佷笌鎺у埗 |
| 鍌ㄨ兘瀹归噺 | `storage_capacity`, `storage_new` | 31 脳 2 脳 2 | GW | battery/PHS 鍔熺巼瀹归噺 |
| 鍌ㄨ兘杩愯 | `storage_charge`, `storage_discharge`, `storage_soc`, `storage_reserve_up`, `storage_reserve_down` | 31 脳 2 脳 H 脳 5 | GW/GWh | SOC 涓庡鐢ㄦ姇褰?|
| 鐪侀檯杈撶數瀹归噺 | `line_capacity`, `line_new` | 411 脳 2 | GW | 璧板粖瀹归噺 |
| 鐪侀檯娼祦 | `flow_forward`, `flow_reverse_ac` | `411 脳 H + 48 脳 H` | GW | AC 鍙屽悜銆丏C 浠呮鍚戯紱杈撳嚭闃舵鍐嶉噸寤?411 琛岀瀵嗗弽鍚戠煩闃典互淇濇寔鎺ュ彛鍏煎 |
| VRE spur | `spur_augmentation` | 36,686 | GW | 鍏朵腑 15,378 涓?DPV 鍙橀噺鍥哄畾涓?0 |
| hydro spur | `hydro_spur_augmentation` | 2,030 | GW | 姘寸數绔欐帴鍏ュ寮?|
| trunk | `trunk_augmentation` | 6,294 | GW | 鍏朵腑绾?3,650 涓彉鐢电珯鏃?VRE/hydro 璺敱 |
| 鐪佸唴涓績绾胯矾 | `intra_load_center_capacity/new`, `flow_forward/reverse` | 517 脳 4 | GW/GWh | 骞村害浠ｇ悊缃戠粶 |
| DAC | `dac_capacity`, `dac_new`, `dac_capture` | 31 脳 4 脳 3 | MtCO2/yr銆丮tCO2 | 瀹归噺銆佹崟闆嗕笌鏂板璐︽埛 |
| CO2 婧愭眹 | `co2_ship` | 31 脳 3,241 | MtCO2 | 鐪佺骇婧愬埌鐐圭骇姹囪繍杈?|
| 骞村害涓績鍒嗛厤 | 11 涓彉閲忔棌 | 4,725 variables | GWh | 278 涓績骞村害绌洪棿闂悎 |

### 3.3 褰撳墠 8760 鍙橀噺瑙勬ā璐＄尞

| 妯″潡 | 8760 variables | 鍗犳瘮 |
|---|---:|---:|
| 姘寸數 | 16,842,810 | 38.20% |
| Thermal RUC | 14,936,637 | 33.88% |
| 鐪侀檯杈撶數 | 7,201,542 | 16.33% |
| 鍌ㄨ兘 | 2,715,724 | 6.16% |
| VRE | 2,245,852 | 5.09% |
| Carbon/CCS/DAC | 100,906 | 0.23% |
| Spur/trunk | 42,980 | 0.10% |
| 骞村害璐熻嵎涓績 | 4,725 | 0.01% |
| **鍚堣** | **44,091,176** | **100%** |

杩欓噷鈥滃彉閲忓皯鈥濅笉绛変簬鈥滄眰瑙ｅ奖鍝嶅皬鈥濄€傚勾搴﹁礋鑽蜂腑蹇冨眰鍙湁 4,725 涓彉閲忓拰绾?3,506 鏉＄害鏉燂紝鍗撮€氳繃灏戦噺瓒呴暱骞村害姹傚拰琛岃础鐚害 45 million nonzeros锛屾槸 barrier fill-in 鐨勯噸瑕佸€欓€夋潵婧愩€?
---

## 4. 涓?CISPO.pdf 鐨勯€愭ā鍧楀樊寮傚拰鍚堢悊鎬у垽鏂?
### 4.1 妯″瀷杈圭晫銆佹椂绌哄垎杈ㄧ巼涓庤鍒掓灦鏋?
| 浜嬮」 | CISPO.pdf | 褰撳墠 V0719 | 鍒ゆ柇 |
|---|---|---|---|
| 鐢电綉鍖哄煙 | 32 涓?grid锛屽唴钂欏彜鎷嗗垎 Mengdong/Mengxi | 31 鐪侊紝鍐呰挋鍙ゅ悎骞?| 瀵逛弗鏍煎鐜帮紝PDF 鏇村悎鐞嗭紱瀵瑰綋鍓嶇粺涓€鐪佺骇鏁版嵁锛?1 鐪佹洿涓€鑷淬€傝鏂囧繀椤诲０鏄庝负閫傞厤妯″瀷銆?|
| 鍩哄噯杈圭晫 | 2022 鏃㈡湁瀹归噺锛?030 棣栨浼樺寲 | 2025 杈撳叆杈圭晫锛?030 棣栨浼樺寲 | 褰撳墠鏇磋创杩戞渶鏂板瓨閲忥紝浣嗕笌璁烘枃缁撴灉涓嶈兘鐩存帴涓€涓€澶嶇幇銆?|
| 鏃堕棿 | 8760h锛涢€愭湡鍒?2060 | 8760h锛?030鈫?040鈫?050鈫?060 cohort 浼犻€?| 鏍稿績涓€鑷达紱褰撳墠 checksummed cohort 鏇村彲杩芥函銆備簩鑰呴兘鏄?myopic sequential锛屼笉鏄?perfect foresight銆?|
| VRE 绌洪棿 | 0.25掳 缃戞牸 | 36,686 technology-site rows锛?.25掳 | 涓€鑷淬€?|
| 姘旇薄骞?| 璁烘枃杩愯骞村強 1980-2019 鍘嗗彶宄板€?| 杩愯 CF 涓?2023锛宻pur/trunk max 涔熸潵鑷?2023 | PDF 鐨勯暱鏈熷嘲鍊肩敤浜庣綉缁滆璁℃洿绋冲仴锛涘綋鍓嶅崟澶╂皵骞翠笉瓒充互鏀拺绋冲仴缃戠粶缁撹銆?|
| 姘存枃 | 2019 GRFR锛?980-2019 discharge 10th percentile 鐜娴?| 2019 GRFR锛?019 鍗曞勾 monthly P30 proxy | 褰撳墠浠ｇ悊涓嶆槸璁烘枃鐜娴侊紝涔熶笉鏄寮忓骞?P30锛涢渶鍗曠嫭鍛藉悕鎯呮櫙銆?|
| CSP | 鍚敤 cell-level CSP + thermal storage | 鏄庣‘绂佺敤锛屽閲忓浐瀹?0 | PDF 鏇村畬鏁达紱褰撳墠鍥犵己鏁版嵁鑰岀鐢ㄦ槸璇氬疄澶勭悊锛屼絾璁烘枃涓嶅緱澹扮О瑕嗙洊瀹屾暣鎶€鏈泦銆?|

### 4.2 VRE 涓?CSP锛圫4-2 鑷?S4-7锛?
褰撳墠 VRE 瀹归噺涓婁笅鐣屼笌骞剁綉鍑哄姏绾︽潫蹇犲疄瀹炵幇 S4-2/S4-3銆俙vre_available` 鏄?site-CF 鑱氬悎杈呭姪鍙橀噺锛宍vre_generation <= vre_available` 鍐冲畾寮冮寮冨厜銆?
鍚堢悊鎬у垽鏂細

- 绾︽潫閫昏緫涓庤鏂囦竴鑷淬€?- 褰撳墠 `vre_available` 铏芥暟瀛︿笂鍙唬鍏ュ垹闄わ紝浣嗙洿鎺ヤ唬鍏ヤ細鎶婂悓涓€澶у潡 CF 绯绘暟澶嶅埗鍒?dispatch 鍜?reserve 涓ょ粍绾︽潫銆傛棦鏈夎瘯楠岃〃鏄庨潪闆跺厓鍙嶈€屽鍔狅紝鍥犳瀹冧笉鏄綋鍓嶉瑕佸啑浣欏彉閲忥紝搴斾繚鐣欎綔涓虹█鐤忓寲杈呭姪閲忋€?- 褰撳墠涓烘墍鏈?`31脳4=124` 涓渷-鎶€鏈粍鍚堝缓鍙橀噺锛岃€屽疄闄呭彧鏈?104 涓粍鍚堝瓨鍦ㄣ€傛敼涓?active-pair 绱㈠紩鍙畨鍏ㄥ垹闄?`350,400` 涓叏骞村彉閲忓強绾?`175,200` 鏉″浐瀹氶浂绾︽潫銆?- CSP S4-4 鑷?S4-7 瀹屽叏鏈疄鐜帮紝灞炰簬鏁版嵁缂哄彛鑰屼笉鏄叕寮忎紭鍖栥€?
### 4.3 姘寸數锛圫4-8 鑷?S4-17锛?
褰撳墠瀹炵幇锛?
- ROR 淇濈暀绔欑偣瀹归噺锛屾寜绔欑偣 CF 鑱氬悎涓虹渷绾?`ror_available`锛屽啀鐢?`ror_generation` 鍐冲畾寮冩按銆?- 620 涓按搴撶珯鏄惧紡寤?turbine flow銆乻pill 鍜?active storage銆?- 146 涓牳蹇冩绾х珯閫氳繃 124 鏉¤竟鍔犲叆涓婃父 release 寤惰繜浼犳挱锛涘叾浣欐按搴撶嫭绔嬭繍琛屻€?- 鍐呴儴鍙橀噺鍋?`10^3 m3/s` 鍜?`10^6 m3` 缂╂斁锛岀墿鐞嗗鍑轰粛浣跨敤 m3/s 鍜?m3銆?
涓?PDF 鐨勫樊寮傦細

- PDF 鐨?S4-17 鏄悇绔欑嫭绔嬭嚜鐒跺叆娴侊紱褰撳墠澧炲姞鏍稿績姊骇璐ㄩ噺浼犳挱锛岀墿鐞嗕笂閫氬父鏇村悎鐞嗭紝浣嗙粨鏋滀緷璧?4 鏉′綆鐩稿叧鍜?18 鏉¤揪鍒?168h 鎼滅储涓婇檺鐨勬椂婊炶竟銆?- PDF 灏嗗巻鍙?10th percentile 鐜娴佷粠 2019 inflow 涓墸闄わ紱褰撳墠浣跨敤 2019 鍗曞勾 monthly P30 proxy銆?- 褰撳墠鐢?active storage `0 <= v_active <= Vmax-Vmin` 鏇夸唬缁濆搴撳涓婁笅鐣岋紝鍜?S4-12 鏁板绛変环銆?- 褰撳墠棣栧皬鏃跺姩鎬佷笌鏈皬鏃剁浉杩烇紝闅愬惈 cyclic closure锛屼笉闇€瑕佸啀澧炲姞涓€鏉￠噸澶嶇殑 `v_start=v_end`銆?- PDF S4-63 鐨?ROR reserve 鍏紡鍦ㄥ浘鍍忎腑娣风敤浜?`or/resvor` 绗﹀彿锛屽睘浜庡師鏂囨帓鐗堥敊璇紱褰撳墠鎸?`ROR available - ROR dispatch` 澶勭悊鏇村悎鐞嗐€?
缁撹锛氬綋鍓嶆按鐢靛湪鐗╃悊缁撴瀯鍜屾暟鍊煎昂搴︿笂浼樹簬 PDF 鐨勭嫭绔嬬珯鐐瑰紡绠€鍖栵紝浣嗘按鏂囪瘉鎹皻涓嶈冻浠ユ敮鎸佲€滄洿鍑嗙‘鈥濈殑寮虹粨璁恒€傚簲灏?`independent_reservoir` 涓?`core_cascade` 鍋氭垚璁烘枃娑堣瀺鎯呮櫙锛屽苟琛ラ綈姝ｅ紡澶氬勾鐜娴併€?
### 4.4 Spur/trunk 涓庣渷鍐呯綉缁滐紙S4-18 鑷?S4-21锛?
鍏抽敭宸紓锛?
1. Spur 瀵归潪 DPV 浣跨敤 `site max CF 脳 capacity`锛岀粨鏋勪笌 S4-18 涓€鑷达紝浣嗗綋鍓?max CF 鍙彇 2023锛岃€屼笉鏄?1980-2019銆?2. PDF S4-19 鐨?trunk 鏄€滃悓涓€鍙樼數绔欎笅椋庡厜缁勫悎鐨勫巻鍙插悓鏃跺嘲鍊尖€濓紱褰撳墠 `master.py:890-900` 浣跨敤 `sum(site max CF 脳 site capacity)`銆傝繖浼氫涪澶遍鍏変簰琛ユ€э紝绯荤粺鎬ч珮浼?trunk 闇€姹傘€?3. 褰撳墠鏂板 278 涓?Natural Earth 璐熻嵎涓績銆?17 鏉＄渷鍐?AC500 骞村害浠ｇ悊杈癸紱璇ュ勾搴﹁兘閲忕綉缁滀笉鍦?CISPO S4-18 鑷?S4-21 涓紝鏄澶栨墿灞曘€?4. 褰撳墠骞村害鐪佸唴灞備笉寤?`center脳hour` 鍙橀噺锛屾崯鑰楀浐瀹氫负 0锛屽閲忕敱 `0.5脳8760` 璁捐鍒╃敤灏忔椂鎹㈢畻銆傚畠鍙敤浜庡勾搴︾綉缁滃帇鍔涗唬鐞嗭紝浣嗕笉鑳借В閲婁负灏忔椂 AC 娼祦鎴?N-1 瀹夊叏缃戠粶銆?
鍚堢悊鎬у垽鏂細

- PDF 鐨?coincident peak trunk 鍏紡鐗╃悊涓婃洿鍚堢悊锛涘綋鍓?sum-of-site-peaks 鏄繚瀹堜笂鐣岋紝涓嶅簲绉颁负绛変环澶嶇幇銆?- 鐩存帴涓烘墍鏈?substation-hour 鍔?S4-19 绾︽潫浼氭樉钁楁斁澶фā鍨嬨€傛帹鑽愪娇鐢?**constraint generation**锛氬厛鍔犲叆灏戦噺宄板€煎皬鏃讹紝姹傝В鍚庢壂鎻?1980-2019 鍏ㄦ椂娈碉紝鍙坊鍔犺繚鍙?trunk envelope 鐨勫皬鏃讹紝杩唬鍒版棤杩濆弽銆傝鏂规硶瀵规湁闄愬巻鍙叉椂娈垫槸绮剧‘鐨勶紝骞惰兘淇濈暀浜掕ˉ鎬с€?- 278 涓績骞村害灞傝嫢浣滀负璁烘枃璐＄尞锛屽簲鍗曠嫭鎶ュ憡鍏朵唬鐞嗘€ц川锛屽苟瀵?`design_utilization_fraction={0.3,0.5,0.7}`銆? 鎹熻€椼€佹嫇鎵戝拰闀胯窛绂昏竟鍋氭晱鎰熸€у垎鏋愩€?
### 4.5 Thermal/nuclear RUC锛圫4-22 鑷?S4-39锛?
褰撳墠鎶婅鏂囩殑杩炵画鈥滄満缁勬暟 脳 鍏稿瀷鍗曟満瀹归噺鈥濆彉閲忕瓑浠风缉鏀句负 GW 瀹归噺鍙橀噺銆傚彧瑕佸惎鍔ㄦ垚鏈瓑鍙傛暟涔熸寜 MW/GW 缂╂斁锛岃繖涓€鍙樻崲鍚堢悊涓旀洿鏄撹В閲娿€?
宸叉纭繚鐣欙細

- online/startup/shutdown 杞Щ锛?- S4-24/S4-25 鏈€灏忓紑鍋滄満鏃堕棿锛?- S4-26 鍑哄姏鑼冨洿锛?- S4-27/S4-28/S4-29 鍘熷叕寮忥紱
- CHP 鍐鍏ㄥ湪绾匡紱
- biomass 50% 鏈€浣庡湪绾匡紱
- 浜旂粍 CCS retrofit 閰嶅銆?
涓昏宸紓鍜岄闄╋細

- 褰撳墠瀵瑰叏鍛ㄦ湡浣跨敤 modular cyclic RUC 绐楀彛锛汸DF 瀵?`t=0` 鐨勬渶灏忓紑鍋滄満姹傚拰璁句负 0銆傚綋鍓嶅鐞嗗彲閬垮厤骞村垵/骞存湯鍏嶈垂鍚仠锛屾洿閫傚悎閲嶅骞村害锛屼絾涓嶆槸閫愬瓧澶嶇幇銆?- PDF 鏈?`f_load脳u_load + f_on脳u_on` 涓ゆ鐕冩枡椤癸紱褰撳墠缂哄皯 `f_on`锛屽彧鎸?gross generation 鏀惰垂锛坄config/optimization_2030.json:44`锛夈€傝繖浼氬急鍖栦繚鎸佸湪绾跨殑鏃犺礋鑽风噧鏂欐垚鏈€?- 褰撳墠灏?ramp-up/down 涓ょ粍鍙橀噺鎶曞奖涓轰竴涓?`ramp_magnitude=|螖P|`銆傚湪涓娿€佷笅鐖潯鎴愭湰鐩稿悓涓斿潎涓烘鏃朵弗鏍肩瓑浠凤紝骞惰妭鐪佺害 2.99 million 鍏ㄥ勾鍙橀噺锛涜嫢鏈潵閲囩敤闈炲绉版垚鏈紝鍒欓渶鎭㈠涓ょ粍鍙橀噺銆?- `ruc_formula_variant="CISPO_original"` 鍙瓨鍦ㄤ簬閰嶇疆鍜岃鏄庢枃妗ｏ紝鐢熶骇浠ｇ爜娌℃湁璇诲彇璇ュ紑鍏筹紝涔熸病鏈?`standard_clustered_RUC` 鍒嗘敮銆傝瀛楁鐩墠鏄€滄棤鏁堥厤缃€濓紝搴斾慨澶嶆垨鍒犻櫎锛岄伩鍏嶄娇鐢ㄨ€呰浠ヤ负宸叉敮鎸佸叕寮忓垏鎹€?- S4-28 鐨勫師鏂囩储寮曞拰绗﹀彿鍏锋湁浜夎銆傚綋鍓嶅繝瀹炲疄鐜板師寮忛€傚悎浣滀负 replication baseline锛屼絾璁烘枃搴斿鍔犳爣鍑?clustered-RUC 瀵圭収锛屾楠屽閲忋€佸惎鍋溿€佺埇鍧″拰鎴愭湰鏁忔劅鎬с€?- **S4-34 鐢熺墿璐ㄥ閲忎笂鐣屽拰 S4-36 鏍哥數瀹归噺涓婄晫缂哄け**锛屾槸鏈ā鍧楁渶閲嶈鐨勭瀛︾己鍙ｃ€?
### 4.6 鍌ㄨ兘锛圫4-40 鑷?S4-50锛?
褰撳墠灏嗚鏂囧洓缁?`reserve 脳 charge/discharge` 鍙橀噺鎶曞奖鎴?`storage_reserve_up/down` 涓ょ粍鍙橀噺锛屽苟淇濈暀鍔熺巼銆丼OC 鑳介噺鍜屾€诲鐢ㄨ竟鐣屻€傚鈥滃鐢ㄦ棤鍗曠嫭鎴愭湰銆佺郴缁熷彧浣跨敤鑱氬悎涓婁笅澶囩敤鈥濈殑褰撳墠妯″瀷锛岃繖涓€鎶曞奖淇濇寔鍙闆嗗悎锛屼紭浜庡師濮嬪彉閲忔灦鏋勩€?
宸紓锛?
- 褰撳墠 PHS 閲囩敤 GHT 2026 鏁版嵁锛?030 floor/upper 涓?`65.940/249.191 GW`锛涜鏂?Table S15/S18 涓?2030 lower `86.43 GW`銆侀暱鏈?upper `765.5 GW`锛?2 grid锛夈€備簩鑰呮潵婧愬拰鏃堕棿杈圭晫涓嶅悓锛屼笉鑳芥贩绉板鐜般€?- 褰撳墠 PHS 鏄渷绾?8h 鍌ㄨ兘锛屾病鏈?open-loop/closed-loop 姘村簱閰嶅锛屽拰璁烘枃鐨勭渷绾т唬琛ㄦ妧鏈帴杩戙€?- 褰撳墠 2030 battery floor 涓?0锛屽急浜庤鏂?Table S16/S17銆?- 褰撳墠鍜?PDF 閮芥病鏈変簩杩涘埗 charge/discharge 浜掓枼銆傛晥鐜囦笌姝?VOM 閫氬父鎶戝埗鍚屾椂鍏呮斁鐢碉紝浣嗗簲澧炲姞 QC锛屾姤鍛?`simultaneous_charge_discharge_hours` 鍜屾渶灏忔柟鍚戠數閲忋€?
缁撹锛氬偍鑳借繍琛岀害鏉熺殑褰撳墠鎶曞奖鏇撮€傚悎澶ц妯?LP锛涘閲忚竟鐣屾柟闈㈠簲琛ュ洖鐢垫睜涓嬬晫锛屽苟灏?GHT 2026 PHS 涓庤鏂?PHS 鍒嗕负涓嶅悓鎯呮櫙銆?
### 4.7 鐪侀檯杈撶數涓庡姛鐜囧钩琛★紙S4-51 鑷?S4-58锛?
褰撳墠 `1b6da28` 鍚庣殑杈撶數鐗╃悊涓?PDF 鍩烘湰瀵归綈锛?
- AC锛氭鍙嶅悜闈炶礋娴侀噺锛屽叡浜?`forward+reverse<=capacity`锛?- DC锛氬浐瀹氭柟鍚戯紱
- 娴侀噺鎯╃綒锛歚0.001 yuan/kWh = 1 yuan/MWh`锛?- 涓ユ牸鐪佺骇灏忔椂骞宠　锛屾棤 load shedding锛?- QC 纭鏌?AC 鍚屽皬鏃跺弻鍚戞祦涓?DC 鍙嶅悜娴併€?
褰撳墠鎶?PDF 鐨?`I_local` 鍜?S4-57/S4-58 涓や釜绛夊紡娑堝厓鎴愬崟涓?nodal balance锛坄monolithic.py:531-538`锛夈€傝繖鏄弗鏍肩瓑浠蜂笖鏇寸揣鍑戠殑鏀瑰啓锛屼紭浜庝繚鐣欎腑闂村彉閲忋€?
浠嶅瓨鍦ㄧ殑闂锛?
- 363 鏉?DC 鍙嶅悜鍙橀噺鍙鍥哄畾涓?0锛屾病鏈変粠鍙橀噺鍧楀垹闄ゃ€?- 褰撳墠 31 鐪佸拰 411 璧板粖涓?PDF 32 grid 鎷撴墤涓嶅悓銆?- 杩欐槸 transportation model锛屼笉婊¤冻 Kirchhoff 鐢靛帇瀹氬緥銆佺嚎璺浉瑙掋€丯-1 鎴栫渷鍐呭皬鏃舵嫢濉炪€傞€傜敤浜庨暱鏈熷閲忚鍒掞紝浣嗚鏂囩粨璁哄簲閬垮厤鍐欐垚鈥滅簿纭數缃戞疆娴佸彲琛屸€濄€?
### 4.8 澶囩敤銆佸閲忚搴︿笌鎯噺锛圫4-59 鑷?S4-71锛?
褰撳墠鎶?thermal/VRE/hydro 鐨勬樉寮?reserve variables 鎶曞奖涓?headroom 琛ㄨ揪寮忥紝鍙繚鐣欑郴缁熷鐢ㄤ笉绛夊紡锛涘湪澶囩敤鍙橀噺鏃犳垚鏈€佹棤璺ㄦ椂娈佃€﹀悎鏃朵笌 PDF 绛変环銆傝繖鏄珮浠峰€肩█鐤忓寲銆?
宸紓锛?
- PDF S4-70 鐨勫閲忚搴︿负 5%锛涘綋鍓嶄负 15%锛坄config/optimization_2030.json:81`锛夈€?5% 鏇翠繚瀹堬紝浣嗘病鏈?LOLE/ELCC 鏍囧畾锛屼笉鑳界洿鎺ユ柇瑷€鏇村悎鐞嗐€?- PDF 鎯噺闃堝€间负 `iota_tol 脳 3.5 s 脳 demand`锛涘綋鍓嶇洿鎺ヤ娇鐢?`3.0 s 脳 demand`锛坄config/optimization_2030.json:82`锛夛紝娌℃湁鏄惧紡 `iota_tol`銆?- 褰撳墠鎸夎鏈哄閲忕粰 hydro/PHS 鎯噺锛屼笌 PDF 涓€鑷达紝浣嗕細璁╂湭鍙戠數鎴栨湭鍚屾鐨勮澶囦粛璐＄尞鎯噺銆俠attery 褰撳墠涓?0 s銆?- 姘村簱涓婂鐢ㄥ彧鍙楄鏈哄噺鍑哄姏绾︽潫锛屼笉鍙楀彲鐢ㄦ按閲忓拰 reserve sustain duration 绾︽潫锛涜繖鏄?PDF 涓庡綋鍓嶅叡鍚岀殑涔愯鍋囪銆?
寤鸿锛氱敤鍘嗗彶浜嬫晠/杩愯瑙勫垯鏍囧畾 reserve锛涗互 LOLE/EUE 鎴栬嚦灏?peak-hour ELCC 璁＄畻瀹归噺淇＄敤锛涘皢鍚屾鎯噺涓庢満缁勮繍琛岀姸鎬佽€﹀悎锛涘 grid-forming inverter 寤虹珛鍗曠嫭鍙橀噺涓庢垚鏈€傝繖涓€閮ㄥ垎鍏锋湁杈冨己璁烘枃鎻愬崌娼滃姏銆?
### 4.9 Carbon銆丏AC 涓?CCS锛圫4-72 鑷?S4-77锛?
褰撳墠瀹炵幇浼樺娍锛?
- 鐪佺骇鎹曢泦閲忎笌 3,241 涓偣绾ф敞鍏ユ眹寤虹珛杩愯緭鍙橀噺锛?- source balance 浣跨敤涓ユ牸绛夊紡锛屼笉鍏佽鍑┖澶氳繍鎴栧皯杩?CO2锛?- 鎹曢泦銆佽繍杈撱€佹敞鍏ユ垚鏈垎寮€锛?- BECCS 浣跨敤鏄惧紡璐熸帓鏀惧洜瀛愬苟瑕佹眰姝ｅ悜杩愯緭灏佸瓨銆?
宸紓鍜岄闄╋細

- PDF S4-72 鐢?`eta_dac 脳 m_dac` 鎶垫墸鎺掓斁锛涘綋鍓嶇洿鎺ョ敤 `m_dac`锛岀瓑浠蜂簬闅愬惈 `eta_dac=1`锛屼絾杈撳叆鍜岄厤缃病鏈夋樉寮忚褰曘€傝礋鎺掓斁鎯呮櫙鍓嶅繀椤昏ˉ鍏呰鍙傛暟鎴栨槑纭浐瀹氫负 1.0銆?- PDF S4-77 鍐欐垚杩愯緭閲?`>=` 鎹曢泦閲忥紱褰撳墠鐢ㄧ瓑寮忋€傚湪鎵€鏈夎繍杈?娉ㄥ叆鎴愭湰涓ユ牸涓烘鏃朵袱鑰呮渶浼樿В绛変环锛岃€屽綋鍓嶇瓑寮忕墿鐞嗕笂鏇存竻鏅般€?- BECCS 鐨勨€滃噣璐熸帓鏀惧洜瀛愨€濆拰鈥滈渶瑕佽繍杈撶殑鎹曢泦閲忊€濅娇鐢ㄥ悓涓€缁濆鍊间唬鐞嗭紝鍙兘娣锋穯鐢熷懡鍛ㄦ湡鍑€鎺掓斁涓庣儫姘斿疄闄呮崟闆嗛噺銆傝鏂囧墠搴斿垎鍒弬鏁板寲 `gross_biogenic_CO2`銆乧apture rate 鍜?lifecycle emissions銆?- `co2_ship` 鏈夌害 100,471 涓浐瀹氬勾搴﹀彉閲忥紝涓嶆槸鍏ㄥ勾姹傝В涓昏鐡堕锛涜嫢杩涗竴姝ユ墿灞曟簮/姹囧垎杈ㄧ巼锛屽彲閲囩敤杩愯緭瀛愰棶棰樻垨鍒楃敓鎴愩€?
---

## 5. 鐩爣鍑芥暟宸紓

| 鎴愭湰椤?| CISPO.pdf | 褰撳墠 V0719 | 瀹℃煡缁撹 |
|---|---|---|---|
| VRE investment/FOM | 鎬诲閲忓勾鍖?+ FOM | 鎬诲閲忓勾鍖?+ FOM | 鍩烘湰涓€鑷淬€?|
| Hydro investment/FOM/VOM | 鎬诲閲忓勾鍖?+ FOM + generation VOM | 鎬诲閲忓勾鍖?+ FOM锛涙棤鏄惧紡 hydro VOM | 鑻?VOM 鍙?0 搴斿湪閰嶇疆鏄庣ず锛屽惁鍒欏睘浜庢紡椤广€?|
| Thermal/nuclear investment/FOM | 鎬诲閲忓勾鍖?+ FOM | 鎬诲閲忓勾鍖?+ FOM | 涓€鑷达紝浣嗏€滃瓨閲忎篃鎸夊綋鍓?capex 骞村寲鈥濅細鎶珮鎶ュ憡鎴愭湰銆?|
| Thermal VOM | 瀵?`u_load脳capacity` | 瀵?CCS loss 鍚庡噣鍑哄姏 `actual_thermal` | CCS 鏈虹粍 VOM 灏戣绾︽晥鐜囨崯澶辨瘮渚嬶紱鍗曚綅鍙ｅ緞闇€鏍稿銆?|
| Fuel | `f_load脳gross + f_on脳online` | gross generation 鍗曟鎴愭湰 | 缂?no-load fuel/intercept銆?|
| Startup/shutdown | 涓ら」 | 涓ら」 | 涓€鑷达紝宸叉寜 MW/GW 缂╂斁銆?|
| Ramp | 鐙珛 up/down 鎴愭湰 | 鍗曚竴缁濆鐖潯閲?| 褰撳墠浠呭湪涓婁笅鎴愭湰鐩稿悓鐨勯厤缃笅绛変环銆?|
| Storage | 鎬诲閲忓勾鍖?FOM + throughput VOM | 涓€鑷?| 鍩烘湰涓€鑷淬€?|
| Inter-grid transmission | 鎬诲閲忓勾鍖?+ FOM + flow VOM | 鎬诲閲忓勾鍖?+ flow regularization锛涙棤鏄惧紡 line FOM | 鍥哄畾 O&M 婕忛」鎴栨湭鏄惧紡璁鹃浂銆?|
| Spur/trunk | 鎬诲閲忔垚鏈?| 鍙 augmentation 鏀惰垂 | 鏇寸鍚堚€滄棦鏈夎祫浜т负娌夋病鎶曡祫鈥濓紝浣嗕笌鍙戠數/鐪侀檯绾跨殑鎬诲閲忚璐逛笉涓€鑷淬€?|
| DAC/CCS | capacity/FOM/VOM + capture/transport/injection | 宸插疄鐜?| `eta_dac` 涓?BECCS 鐗╃悊鍙ｅ緞闇€琛ラ綈銆?|
| Other technology `O` | 淇濈暀鎺ュ彛 | 鏈舰鎴愰€氱敤鎺ュ彛 | 瀵瑰綋鍓嶅熀鍑嗘棤褰卞搷锛涜嫢鍋?DR 绛夋儏鏅渶琛ャ€?|

### 5.1 鎴愭湰浼氳鐨勬帹鑽愮粺涓€鏂瑰紡

褰撳墠妯″瀷娣峰悎浜嗕袱绉嶄細璁★細鍙戠數銆佸偍鑳藉拰鐪侀檯绾胯矾鎸夋€诲閲忔敹骞村寲 CapEx锛宻pur/trunk 鍙鏂板澧炲己鏀惰垂銆傚缓璁湪涓嶆敼鍙?replication baseline 鐨勫墠鎻愪笅锛屾柊澧炰竴涓粡娴庤В閲婃洿娓呮櫚鐨勭洰鏍囩増鏈細

```text
annual system cost
  = annualized CapEx of active model-built cohorts
  + FOM of all active capacity
  + variable operation/fuel/start/ramp costs
  + network and carbon costs
```

璁烘枃鍚屾椂鎶ュ憡锛?
- `replication_objective`锛氬敖閲忛伒寰?CISPO 鎬诲閲忓勾鍖栧叕寮忥紱
- `incremental_planning_objective`锛氬彧瀵规柊澧?cohort 鏀?CapEx锛屽鍏ㄩ儴瀹归噺鏀?FOM銆?
杩欐牱鍙尯鍒嗏€滀紭鍖栧喅绛栨槸鍚︽敼鍙樷€濆拰鈥滅郴缁熸垚鏈細璁″彛寰勬槸鍚︽敼鍙樷€濄€?
---

## 6. 鍐椾綑鍙橀噺涓庡彲瑙ｆ€?
### 6.1 鍙畨鍏ㄥ垹闄ゆ垨鏀逛负 active-index 鐨勫彉閲?
| 浼樺厛绾?| 鍙橀噺/缁撴瀯 | 鍏ㄥ勾鍙噺灏戝彉閲?| 鏄惁鏀瑰彉鍙鍩?| 璇存槑 |
|---|---|---:|---|---|
| P0 | 363 鏉?DC 鐨?`flow_reverse` | 3,179,880 | 鍚?| 鍙 48 鏉?AC 鍒涘缓 reverse銆?|
| P1 | 涓嶅瓨鍦ㄧ殑 20 涓?VRE 鐪?鎶€鏈粍鍚?| 350,400 | 鍚?| 褰撳墠 124 涓?dense pair锛屽疄闄?104 涓€?|
| P1 | 鏃?ROR 鐨?3 鐪?`ror_available/generation` | 52,560 | 鍚?| 瀹為檯浠?28 鐪佹湁 ROR銆?|
| P1 | PHS upper=0 鐨勫ぉ娲ャ€佷笂娴?5 缁勫皬鏃跺彉閲?| 87,600 | 鍚?| 鍙负 active storage pairs 寤哄彉閲忋€?|
| P2 | 閲嶅鐨?`capacity` 涓?`new` 骞村害璐︽埛 | 40,171 | 鍚?| `new=capacity-floor` 鍙湪瀵煎嚭鏃惰绠椼€?|
| P2 | DPV 鍥哄畾闆?spur variables | 15,378 | 鍚?| 鍙负闈?DPV 寤?spur銆?|
| P2 | 鏃?VRE/hydro 璺敱鐨?trunk variables | 3,650 | 鍚?| 6,294 涓腑绾?2,644 涓?active銆?|

鍓嶅洓椤瑰悎璁″彲鍑忓皯 `3,670,440` 涓彉閲忥紝绾﹀崰褰撳墠鍏ㄥ勾鍙橀噺鐨?`8.32%`锛涜繛鍚屽浐瀹氬勾搴﹀潡绾﹀彲鍑忓皯 `8.46%`銆傝繖涓嶄細鑷姩鎸夊悓绛夋瘮渚嬮檷浣?barrier factor memory锛屼絾浼氭樉钁楀噺灏?Python/Gurobi 鏋勫缓銆乸resolve 鍜屽彉閲忓伐浣滃尯銆?
### 6.2 涓嶅缓璁洿鎺ュ垹闄ょ殑鍙橀噺

- `vre_available`銆乣ror_available`锛氳櫧鐒跺彲浠ｆ暟娑堝厓锛屼絾瀹冧滑閬垮厤鎶婂ぇ閲?site CF 绯绘暟澶嶅埗鍒?dispatch 涓?reserve 绾︽潫銆傚凡鏈夎瘯楠岃〃鏄庣洿鎺ュ垹闄ゅ弽鑰屽鍔犵煩闃甸潪闆跺厓銆?- `reservoir_spill_flow`锛氭湁闄愬簱瀹瑰拰鍙戠數鑳藉姏涓嬪繀椤诲厑璁稿純姘达紱鏀瑰悕涓?total release 涔熶笉鑳芥秷闄や竴涓嫭绔嬫按鎺у埗鑷敱搴︺€?- `online/startup/shutdown/gross`锛歋4-24 鑷?S4-29 鍜屽惎鍋滄垚鏈渶瑕佽繖浜涘彉閲忋€傚己琛屾秷鍏冧細閫犳垚鏇撮暱鐨勬椂闂磋€﹀悎琛屻€?- `storage_reserve_up/down`锛氬畠浠凡鏄洓缁勫師濮嬪偍鑳藉鐢ㄥ彉閲忕殑绮剧‘鎶曞奖锛屼笉鏄師濮嬪啑浣欍€?
### 6.3 鐪熸褰卞搷 barrier 鐨勭粨鏋?
1. Thermal RUC 鍜?station reservoir 鐨勯€愭椂鑰﹀悎鍗犲ぇ澶氭暟 rows/variables銆?2. 骞村害璐熻嵎涓績銆佸勾搴︽帓鏀惧拰骞村害鎹曢泦璐︽埛褰㈡垚灏戦噺瓒呴暱琛岋紱瀹冧滑鍙兘寮曡捣绋€鐤忔秷鍏冨～鍏呫€?3. 鏃?744h barrier 鐨?`Factor NZ=8.289e8`锛岀害 10 GB锛涙寜灏忔椂绾挎€ф斁澶у叏骞村凡绾?118 GB锛屽皻鏈鍘熷妯″瀷銆乸resolve銆佺嚎绋嬪拰 crossover銆?
鎺ㄨ崘灏嗗勾搴﹂暱姹傚拰鏀规垚**鍒嗗潡绱缃戠粶**锛氭寜 168h 鎴栨湀寤虹珛 block energy accumulator锛屽啀鎶?block 缁撴灉姹囨€诲埌骞村害绾︽潫銆傝鏀瑰啓鍙兘涓嶆樉钁楀噺灏戝師濮?nonzeros锛屽嵈鑳界缉鐭崟琛岃法搴︺€佹敼鍠勬椂闂村潡绠ご缁撴瀯锛屽簲浠?168h/744h 鐨?`AA' NZ`銆乣Factor NZ` 鍜屾€绘椂闂翠綔涓洪獙鏀舵寚鏍囥€?
---

## 7. 浠庢ā鍨嬫彁鍗囧拰璁烘枃鍙戣〃瑙掑害鐨勬敼杩涜矾绾?
### 7.1 Phase A锛氱瀛︽纭€ч棬妲涳紙蹇呴』鍏堝仛锛?
1. 鎺ュ叆鐪佺骇 nuclear potential upper锛屽苟娴嬭瘯 `floor <= upper`锛涘鍔?S4-36 缁撴瀯鍗曞厓娴嬭瘯銆?2. 鏍规嵁 `thermcal`銆佹晥鐜囧拰绛夋晥灏忔椂鐢熸垚 `bio+bioccs` 鍚堣瑁呮満涓婇檺锛涘鍔?S4-34 娴嬭瘯銆?3. 鎺ュ叆鏈€鏂?battery existing/committed floor锛岃嚦灏戜笉浣庝簬鍙牳楠岀殑 2025 瀛橀噺锛涗负璁烘枃 replication 鍙︿繚鐣?Table S16/S17 鎯呮櫙銆?4. 鏄惧紡鍔犲叆 `dac_sequestration_efficiency`锛涙媶鍒?BECCS gross capture 涓?lifecycle net emission銆?5. 鎶?hydro VOM銆乼ransmission FOM銆乼hermal `f_on` 鏍囪涓烘樉寮?0 鎴栬ˉ榻愭潵婧愶紝绂佹鈥滀唬鐮佺己椤圭瓑鍚屽弬鏁颁负 0鈥濈殑闅愬紡澶勭悊銆?6. 淇鎴栧垹闄ゆ棤鏁堢殑 `ruc_formula_variant` 閰嶇疆銆?
**鍋滄瑙勫垯锛?* Phase A 鏈畬鎴愬墠锛?760 鍙兘鐢ㄤ簬缁撴瀯/姹傝В鍣ㄧ爺绌讹紝涓嶅緱浣滀负璁烘枃瀹归噺涓庢垚鏈富缁撴灉銆?
### 7.2 Phase B锛氭暟瀛︾瓑浠风█鐤忓寲鍜屾眰瑙ｉ棬妲?
1. 鍒犻櫎 DC reverse fixed-zero block銆?2. VRE銆丷OR銆丳HS銆乼runk銆乻pur 鏀?active-index銆?3. 鍘婚櫎閲嶅 `capacity/new` 璐︽埛鍙橀噺锛屽鍑烘椂浠庡閲忎笌 floor 璁＄畻鏂板閲忋€?4. 骞村害瓒呴暱琛屾敼 block accumulator锛涙瘮杈?factor fill锛岃€屼笉浠呮瘮杈冨師濮?nonzeros銆?5. 淇濇寔 `Crossover=1` 浣滀负褰撳墠楠屾敹榛樿锛沗Crossover=0` 宸插湪 24h 杩斿洖 `SUBOPTIMAL` 涓?QC 澶辫触銆?6. 鍏堥€氳繃鏂扮殑 24h銆?68h銆?44h `OPTIMAL + QC PASS`锛涘啀鍦ㄥ彲鐢ㄥ唴瀛?鈮?6 GiB 鏃跺仛 8760 build-only銆?7. 鑻ラ璁?barrier 鎬诲唴瀛樹粛瓒呰繃 125 GiB锛屽簲閫夋嫨 鈮?56 GiB 鑺傜偣锛屾垨鍙﹁鎵瑰噯绮剧‘鍒嗚В锛涗笉瑕佹妸 `NodefileStart` 褰撲綔 LP barrier 鍐呭瓨鏂规銆?
### 7.3 Phase C锛氭彁楂樿鏂囪础鐚害

#### A. 鍙潬鎬т笌鐏垫椿鎬?
- 鐢?ELCC 鏇夸唬鍥哄畾 VRE/storage capacity credit锛?- 鐢?LOLE/EUE 鏍″噯 5%/15% capacity margin锛?- 澧炲姞 reserve sustain duration锛屽苟鎶婃按搴撳鐢ㄤ笌姘撮噺鐘舵€佽€﹀悎锛?- 鍖哄垎 synchronous inertia銆乬rid-following 鍜?grid-forming inverter锛?- 鎶ュ憡澶囩敤銆佹儻閲忋€佸閲忚搴﹀悇鑷殑杈归檯鎴愭湰鍜屽閲忓奖鍝嶃€?
杩欑粍鏀硅繘鍙舰鎴愯鏂囩殑鈥滈珮姣斾緥鍙啀鐢熻兘婧愪笅鍙潬鎬х害鏉熷浣曢噸濉戠┖闂撮€夊潃鍜岀伒娲绘€ч渶姹傗€濅富绾裤€?
#### B. 姘旇薄-姘存枃涓嶇‘瀹氭€?
- 杩愯鑷冲皯澶氫釜鐙珛 weather/hydrology years锛?- trunk 浣跨敤 1980-2019 coincident peak constraint generation锛?- 瀵?P30銆佽鏂?Q10 鍜屼笉鍚岀幆澧冩祦瑙勫垯鍋氭晱鎰熸€э紱
- 妫€楠?4 鏉′綆鐩稿叧銆?8 鏉?168h-bound cascade edges锛?- 鎶ュ憡瀹归噺缁勫悎鍦ㄦ皵璞?姘存枃鏍锋湰闂寸殑绋冲仴鎬э紝鑰屼笉鏄彧鎶ュ憡鍗曞勾鏈€浼樺€笺€?
#### C. 瑙勫垝鍓嶇灮鎬?
褰撳墠 2030鈫?060 鏄?myopic sequential銆傚彲澧炲姞涓€涓緝绮楃┖闂?鎶€鏈垎杈ㄧ巼鐨?perfect-foresight 瀵圭収妯″瀷锛屽洖绛旓細

- 杩戣瑙勫垝鏄惁杩囨棭寤鸿鐓ょ數 CCS銆丏AC銆佸偍鑳芥垨杈撶數锛?- 鏈潵璐熸帓鏀剧害鏉熸槸鍚︽敼鍙?2030/2040 鐨勬彁鍓嶆姇璧勶紱
- cohort 閫€褰逛笌 retrofit 鍋囪濡備綍褰卞搷 stranded assets銆?
涓嶅繀鐩存帴鎶?4 涓勾浠藉叏閮ㄥ仛鎴?4脳8760 鐨勮秴澶фā鍨嬶紱鍙厛浣跨敤瀹归噺灞傝仈鍚堣鍒?+ 骞村害杩愯楠岃瘉锛屾竻妤氬尯鍒嗚繎浼煎眰鍜屾渶缁堝皬鏃堕獙璇佸眰銆?
#### D. 缃戠粶琛ㄨ堪

- 灏嗗綋鍓?transportation model 涓庣渷绾?DC load flow/PTDF 瀵圭収锛?- 骞村害 278-center 灞傚仛 0.3/0.5/0.7 utilization銆佹崯鑰楀拰鎷撴墤鏁忔劅鎬э紱
- 瀵瑰叧閿法鐪佽蛋寤婁笌鐪佸唴鐡堕鎶ュ憡 shadow price锛?- 閬垮厤鎶婂勾搴︿腑蹇冧唬鐞嗗啓鎴愬皬鏃剁骇鐗╃悊娼祦銆?
### 7.4 鎺ㄨ崘璁烘枃鎯呮櫙鐭╅樀

| 鎯呮櫙 | 鐩殑 | 鍏抽敭璁惧畾 |
|---|---|---|
| `CISPO_replication` | 涓庡師璁烘枃瀵圭収 | 32 grid锛堣嫢鏁版嵁鍙緱锛夈€?% margin銆佽鏂?PHS/battery bounds銆佽鏂?Q10銆丼4-19 coincident peak銆丆SP |
| `V0719_adapted` | 褰撳墠鏁版嵁杈圭晫涓绘儏鏅?| 31 鐪併€?025 boundary銆丟HT 2026 PHS銆乧ore cascade銆?023 weather |
| `V0719_corrected` | 绉戝涓荤粨鏋?| 琛ラ綈 nuclear/bio/battery/DAC/cost 杈圭晫锛屽畬鎴愮█鐤忓寲 |
| `Reliability_enhanced` | 璁烘枃鍒涙柊 | ELCC/LOLE銆佸姩鎬佸鐢ㄣ€佸悓姝ユ儻閲?grid-forming |
| `Hydro_weather_robust` | 绋冲仴鎬?| 澶氬ぉ姘?姘存枃骞淬€佺幆澧冩祦涓?cascade sensitivity |
| `Perfect_foresight_check` | 瑙勫垝鍋忓樊 | 涓?myopic sequential 瀵圭収 |

---

## 8. 楠屾敹娴嬭瘯鍜屾柊澧?QC 寤鸿

淇鍓?29 椤规祴璇曞叏閮ㄩ€氳繃锛涙牎姝ｅ悗涓?32/32 鍗曞厓娴嬭瘯涓?139/139 鏁版嵁鍖?smoke checks 鍏ㄩ儴閫氳繃銆傛祴璇曢€氳繃鍙兘璇佹槑鈥滀唬鐮佺鍚堝綋鍓嶅疄鐜版剰鍥锯€濓紝涓嶈兘鍗曠嫭璇佹槑妯″瀷绉戝鍋囪宸插厖鍒嗐€備互涓嬪墠鍥涢」宸茬粡瀹炵幇锛屽叾浣欎粛鏄悗缁敼杩涳細

1. `test_nuclear_capacity_upper_is_enforced`
2. `test_biomass_pair_capacity_upper_is_enforced`
3. `test_battery_floor_is_nonzero_where_committed`
4. `test_no_dc_reverse_variables_are_created`
5. `test_only_active_vre_province_technology_pairs_are_created`
6. `test_dac_removal_uses_sequestration_efficiency`
7. `test_ruc_variant_config_is_consumed`
8. `test_trunk_coincident_peak_constraint_generation_closes`
9. `test_simultaneous_storage_charge_discharge_qc`
10. `test_objective_cost_contract_has_all_S4_1_components`

姣忔 24h/168h/744h/8760 楠屾敹鑷冲皯鎶ュ憡锛?
- objective 涓?cost-component closure锛?- 鏍哥數銆佺敓鐗╄川銆乥attery/PHS 涓婁笅鐣屾畫宸紱
- power balance銆乺eserve銆乮nertia銆丼OC銆佹按搴撱€丆O2 source/sink锛?- AC 鍙屽悜銆丏C 鍙嶅悜銆乻torage 鍚屾椂鍏呮斁鐢碉紱
- trunk/spur/intra-center 瀹归噺娈嬪樊锛?- `AA' NZ`銆乣Factor NZ`銆乥arrier/crossover 鍒嗘椂銆乸eak RSS锛?- Git commit銆侀厤缃?SHA256銆佽緭鍏?manifest 鍜岀粨鏋?manifest銆?
---

## 9. 鏈€缁堢粨璁轰笌寤鸿椤哄簭

### 9.1 璋佹洿鍚堢悊

鏈€缁堝垽瀹氫笉鏄簩閫変竴锛?
- **浣滀负鈥滃繝瀹炲鐜板熀绾库€?*锛歚CISPO.pdf` 鏇村悎鐞嗭紝鍥犱负瀹冩槑纭寘鍚牳鐢?鐢熺墿璐ㄥ閲忚竟鐣屻€佺數姹犱笅鐣屻€丆SP銆?2 grid 鍜屽巻鍙插嘲鍊艰鍒欍€?- **浣滀负鈥滃彲缁存姢銆佸彲杩芥函銆佹暟鍊肩ǔ鍋ョ殑宸ョ▼瀹炵幇鈥?*锛氬綋鍓?V0719 鏇村悎鐞嗭紝鍥犱负瀹冨叿鏈変弗鏍?QC銆佽緭鐢垫柟鍚戜慨姝ｃ€佺珯鐐规绾ф按閲忋€佽法骞?cohort銆佹暟鍊肩缉鏀惧拰澶氶」绛変环鎶曞奖銆?- **浣滀负鈥滃彲鍙戣〃鐨勭瀛︿富妯″瀷鈥?*锛氫簩鑰呭綋鍓嶉兘涓嶈冻銆傛渶浣宠矾绾挎槸浠ュ綋鍓嶄唬鐮佷负瀹炵幇搴曞骇锛岃ˉ榻?PDF 鐨勭‖瀹归噺杈圭晫锛屽啀閫氳繃鍙潬鎬с€佸姘旇薄姘存枃骞村拰缃戠粶鏁忔劅鎬у舰鎴愬彲鍙戣〃澧為噺銆?
### 9.2 鎺ㄨ崘鎵ц椤哄簭

```text
P0 scientific constraints
  nuclear upper
  biomass capacity upper
  battery floor
  DAC/BECCS/cost contract
        鈫?P0-P1 exact sparsification
  DC reverse removal
  active indices
  annual block accumulators
        鈫?24h 鈫?168h 鈫?corrected 744h gates
        鈫?8760 build-only and factor-risk review
        鈫?2030 full-year accepted solve
        鈫?2040 鈫?2050 鈫?2060 sequential runs
        鈫?replication/adapted/enhanced scenario paper package
```

褰撳墠姝ｅ湪杩愯鐨?744h 搴斾繚鐣欏苟瀹屾垚锛屽洜涓哄畠鑳芥彁渚?`5a9f4ab` 绋€鐤忕粨鏋勭殑 barrier/factor 璇佹嵁锛涗絾瀹冨彧鍥炵瓟鈥滃綋鍓嶇煩闃垫槸鍚﹀彲琚眰瑙ｂ€濓紝涓嶅洖绛斺€滃綋鍓嶇瀛︾害鏉熸槸鍚﹀凡缁忓畬鏁粹€濄€?
---

## 10. 鍏抽敭璇佹嵁绱㈠紩

- PDF 鍘熷鍏紡锛歚supplementary_materials/CISPO.pdf`锛孲4-1 鑷?S4-77銆?- 褰撳墠鍙橀噺涓庨€愭椂绾︽潫锛歚cispo_model/monolithic.py:34-752`銆?- 瀹归噺銆佹垚鏈€佸閲忚搴︺€佹簮姹囧拰 spur/trunk锛歚cispo_model/master.py:383-974`銆?- 278-center 骞村害缃戠粶锛歚cispo_model/load_center.py:15-352`銆?- 褰撳墠閰嶇疆鍏抽敭椤癸細`config/optimization_2030.json:15-155`銆?- 鍙В鎬у巻鍙茶瘉鎹細`MODEL_SOLVABILITY_AUDIT_20260719.md`銆?- 杈撶數淇璇佹嵁锛歚TRANSMISSION_FLOW_AUDIT_20260719.md`銆?- 褰撳墠浜ゆ帴鐪熷€硷細`CODEX_HANDOFF.md`銆乣MODEL_SERVER_STATUS.md`銆乣SERVER_RUNBOOK.md`銆?
---

## 11. V0719 瀹归噺杈圭晫涓?DC 绋€鐤忓寲瀹炴柦缁啓锛堝綋鍓嶆潈濞佺姸鎬侊級

### 11.1 淇鑼冨洿鍜岄闄╂帶鍒?
鏈疆鍙慨鏀瑰鏌ユ姤鍛婂凡璇嗗埆鐨勫洓椤圭‖缂哄彛锛屾病鏈夋敼鍙?31 鐪佺┖闂磋竟鐣屻€?025 鍩哄噯骞淬€?760 灏忔椂鏃跺簭銆佺洰鏍囧嚱鏁般€佺幇鏈夌噧鏂欎环鏍笺€丳HS 姘村姏琛ㄨ堪銆佸閲?cohort 鎴栨湇鍔″櫒姝ｅ湪杩愯鐨勬棫鐗?744h 浠诲姟锛?
1. 鏍哥數鏂板鐪佺骇瀹归噺涓婄晫锛?2. 鐢熺墿璐ㄤ笌 BECCS 鏂板鐪佺骇鍚堣瑁呮満涓婄晫锛屽悓鏃朵繚鐣欏勾搴︾噧鏂欑害鏉燂紱
3. 鐢垫睜鏂板 2030 鐪佺骇澶栫敓瀹归噺涓嬬晫锛?4. 363 鏉?DC 璧板粖涓嶅啀鍒涘缓鍙嶅悜閫愭椂鍙橀噺锛?8 鏉?AC 璧板粖浠嶄繚鎸佸弻鍚戙€?
鍙傛暟闆嗕腑鍦?`config/capacity_bounds_v0719.json`锛岀敓鎴愯剼鏈负 `scripts/build_v0719_capacity_bounds.py`锛屽苟宸叉帴鍏?`scripts/build_cispo_data_package.py`銆傜敓浜ф暟鎹绾﹀崌绾т负 `config/model_input_files.json` v2锛屾柊澧炰笁寮犲繀闇€琛細

- `data/thermal/nuclear_capacity_upper_by_year.csv`锛?- `data/biomass/capacity_upper_by_province_year.csv`锛?- `data/storage/battery_capacity_floor_by_province_year.csv`銆?
杩欎簺琛ㄧ敱鑴氭湰纭畾鎬х敓鎴愶紝鑰屼笉鏄墜宸ョ紪杈戙€傛湇鍔″櫒閮ㄧ讲鏃跺繀椤诲湪**鏂板鐗堟湰鍖栨暟鎹牴鐩綍**涓噸寤猴紝涓嶈兘瑕嗙洊褰撳墠 744h 浣跨敤鐨勬暟鎹牴銆?
### 11.2 鏍哥數锛氫粠鈥滃彧鏈夌绾夸笅鐣屸€濇敼涓衡€滅绾夸笅鐣?+ 鍙戝睍涓婄晫鈥?
褰撳墠鏍哥數涓嬬晫浠嶆部鐢?GEM committed/pipeline锛?030/2040/2050/2060 鍏ㄥ浗鍒嗗埆涓?`106.764/146.308/185.812/185.812 GW`銆傛柊澧炲叏鍥戒笂鐣屼负锛?
| 骞翠唤 | 鍏ㄥ浗涓婄晫锛圙W锛?| 璇佹嵁鎬ц川 | 澶勭悊鏂瑰紡 |
|---:|---:|---|---|
| 2030 | 110 | 瀹樻柟瑙勫垝閿氱偣 | 鍥藉鑳芥簮灞€鈥滃崄浜斾簲鈥濊鍒掓彁鍑?2030 骞磋繍琛屾牳鐢电害 1.1 浜垮崈鐡︼紝浣滀负涓绘儏鏅‖涓婄晫 |
| 2040 | 205 | 鐮旂┒鎯呮櫙鍖呯粶 | 鍦?2030 涓?2050 涔嬮棿璁剧疆鏄惧紡涓湡鍖呯粶锛屼笉瀹ｇО涓哄畼鏂圭洰鏍?|
| 2050 | 300 | CISPO 闀挎湡鐮旂┒鍖呯粶 | 瀵归綈 CISPO S4-36 绾?230 GW 鐨勬棫鍙ｅ緞鍚庯紝缁撳悎褰撳墠绠＄嚎涓庨暱鏈熸儏鏅缃殑澧炲己涓婄晫锛涘睘浜庣爺绌跺亣璁?|
| 2060 | 300 | 淇濆畧寤剁画 | 鏆備笉缁х画澶栨帹锛岄伩鍏嶆棤璇佹嵁鍦版墿澶ч暱鏈熸牳鐢电┖闂?|

鐪佺骇涓婄晫鍏堜繚璇佷笉浣庝簬鍚勭渷 GEM 涓嬬晫锛屽啀鎸?2050 绠＄嚎鐪佺骇鏉冮噸鍒嗛厤鍏ㄥ浗鍓╀綑绌洪棿銆傚洜姝ゆā鍨嬩笉鑳藉湪鏃犳牳鐢电绾挎潈閲嶇殑鐪佷唤鍑┖鎵╁紶锛屽悓鏃跺洓涓勾浠界殑鍏ㄥ浗涓婄晫绮剧‘闂悎涓?`110/205/300/300 GW`銆傞渶瑕佹槑纭細鍙湁 2030 鐨?110 GW 鏄渶鏂板畼鏂归敋鐐癸紱2040-2060 鏄彲閰嶇疆鐨勮鏂囨儏鏅紝涓嶅簲鍦ㄦ鏂囦腑鍐欐垚鏀跨瓥棰勬祴銆傛渶鏂板畼鏂圭姸鎬佽繕鏄剧ず锛?025 骞村簳鎴戝浗杩愯鏍哥數瑁呮満绾?`62.52 GW`锛?025 骞磋摑鐨功鍙ｅ緞鐨勫湪杩愩€佸湪寤轰笌鏍稿噯寰呭缓鍏?102 鍙般€佺害 `113 GW`锛岃鏄?2030 涓婄晫涓庡綋鍓嶉」鐩摼鏉″湪閲忕骇涓婄浉瀹广€?
### 11.3 鐢熺墿璐?BECCS锛氱渷绾ф綔鍔涘凡鏈夛紝缂虹殑鏄浜岀鐗╃悊鍚箟鐨勭害鏉?
鐢ㄦ埛璁板繂鏄纭殑锛氬綋鍓嶉」鐩師鏈凡缁忔湁 `data/biomass/fuel_potential_by_province_year.csv`锛岃鐩?31 鐪佸拰瑙勫垝骞翠唤鐨?`thermcal_gj_per_year`銆傛鍓嶁€滀笉瀹屽杽鈥濅笉鏄己灏戠渷绾ф綔鍔涜緭鍏ワ紝鑰屾槸杩欎唤娼滃姏鍙繘鍏?CISPO S4-35 寮忕殑**骞村害鐕冩枡娑堣€椾笂闄?*锛?
```text
annual_biomass_fuel_use[p,y] <= thermcal[p,y]
```

瀹冪害鏉熲€滄瘡骞存渶澶氬彲娑堣€楀灏戠敓鐗╄川鐕冩枡鈥濓紝鍗翠笉鑳戒弗鏍奸檺鍒垛€滀负浜嗗閲忚搴︺€佸鐢ㄦ垨鎯噺鏈€澶氬彲寤哄灏戜綆鍒╃敤灏忔椂瑁呮満鈥濄€傚湪褰撳墠 `minimum_online_fraction=0.5`銆乣pmin=0.35` 涓嬶紝鐕冩枡绾︽潫鏈€澶氬彧闅愬惈绾?`0.5 脳 0.35 脳 8760 = 1533` 绛夋晥灏忔椂鐨勫急瀹归噺闄愬埗锛屾樉钁楀浜?CISPO S4-34 浣跨敤鐨?`6132 h`銆傚洜姝ゆ湰杞柊澧炵敓鐗╄川涓?BECCS 鐨勫叡浜閲忎笂鐣岋細

```text
bio_capacity[p,y] + bioccs_capacity[p,y]
    <= max(
        thermcal[p,y] 脳 0.35 / 3600 / 6132,
        existing_bio_floor[p,y] + existing_bioccs_floor[p,y]
       )
```

鍏朵腑 `thermcal` 鍗曚綅涓?`GJ/year`锛岄櫎浠?`3600` 灏?GJ 杞负 GWh锛岄櫎浠?`6132 h` 寰楀埌 GW銆俙0.35` 鍜?`6132 h` 鎸?CISPO S4-34 澶嶇幇锛涘勾搴︾噧鏂欐牳绠椾粛浣跨敤鍚勬妧鏈嚜宸辩殑 heat rate锛屼笉琚浛浠ｃ€傚叏鍥藉叕寮忎笂闄愬湪 2030/2040/2050/2060 鍒嗗埆绾︿负 `473.418/567.332/661.245/661.245 GW`銆?
鍙鎬т繚鎶ゅ彧鍦ㄤ笂娴疯Е鍙戯細涓婃捣鍏紡涓婇檺涓?`0.191/0.212/0.233/0.233 GW`锛屼綆浜庡搴旀棦鏈?bio+BECCS 涓嬬晫 `0.627/0.627/0.586/0.340 GW`锛屽洜姝ゅ己鍒朵笂鐣屽彇鏃㈡湁涓嬬晫锛岄伩鍏嶆柊绾︽潫鍒堕€犵粨鏋勬€т笉鍙銆備繚鎶ゅ悗鍏ㄥ浗鍙墽琛屼笂鐣屼负 `473.854/567.747/661.598/661.352 GW`銆傝繖鍥涜琚〃涓?`capacity_upper_adjusted_to_floor=true` 鏄惧紡鏍囪锛屽彲鍦ㄨ鏂囨暟鎹璁′腑杩借釜銆?
褰撳墠鐢熺墿璐ㄦ綔鍔涙暟鎹笌 2023 骞村叕寮€鐨勪腑鍥界渷绾у啘涓氭畫浣欍€佹灄涓氭畫浣欏拰鑳芥簮浣滅墿璧勬簮妗嗘灦鐩哥銆?026 骞村凡鏈夋洿鏂版暟鎹泦鎵╁睍浜嗚祫婧愮被鍒苟缁欏嚭鑷?2050 骞撮娴嬶紝浣嗕笉鑳藉湪娌℃湁鍚屽彛寰勬牳瀵圭殑鎯呭喌涓嬮潤榛樻浛鎹㈠綋鍓嶄富鎯呮櫙銆傚缓璁悗缁妸 2026 鏁版嵁浣滀负 `updated_biomass_potential` 鏁忔劅鎬ф儏鏅紝姣旇緝璧勬簮绫诲埆銆佸惈姘寸巼/浣庝綅鐑€笺€佸彲鏀堕泦鐜囥€佺敓鎬佺暀瀛樺拰璺ㄧ渷杩愯緭鏄惁鏀瑰彉 BECCS 绌洪棿缁撹銆?
### 11.4 2030 鐢垫睜锛氶噰鐢?CISPO 鐪佺骇鍔熺巼涓嬬晫锛屼笉鎶婃渶鏂拌兘閲忔椂闀垮己濉炶繘鍥哄畾 4h 妯″瀷

鏂板涓嬬晫閫愮渷澶嶇幇 CISPO Table S17 鐨?2025 鐩爣锛屽苟灏?Mengdong `2 GW` 涓?Mengxi `3 GW` 鍚堝苟涓哄唴钂欏彜 `5 GW`銆?1 鐪佸彛寰勪笅鍏辨湁 24 涓潪闆剁渷浠斤紝鍏ㄥ浗 2030 鍔熺巼瀹归噺涓嬬晫涓?`65.85 GW`銆?040-2060 涓嶉噸澶嶅己鍒惰繖涓€ 2025 鎵胯 cohort锛涘湪褰撳墠鐢垫睜瀵垮懡 15 骞寸殑璺ㄥ勾璐︽埛涓紝瀹冨埌 2040 宸茶嚜鐒堕€€鍑猴紝鍚庣画瀹归噺鐢变紭鍖栧拰缁ф壙 cohort 鍐冲畾銆?
鏈€鏂板畼鏂圭粺璁℃樉绀猴紝2025 骞村簳鏂板瀷鍌ㄨ兘瑁呮満宸茶揪 `136 GW / 351 GWh`锛屽钩鍧囨椂闀?`2.58 h`锛屽叾涓攤绂诲瓙鐢垫睜鍗?96.1%锛涜繖璇存槑 CISPO 鐨?`65.85 GW` 鍔熺巼涓嬬晫瀵?2030 宸插亸淇濆畧锛岃€屼笉鏄縺杩涘亣璁俱€備絾褰撳墠妯″瀷鎶?battery 缁熶竴琛ㄧず涓哄浐瀹?`4 h`锛岃嫢鐩存帴鎶?136 GW 鍏ㄩ儴璁句负涓嬬晫锛屼細闅愬惈 `544 GWh`锛屾槑鏄鹃珮浜庡畼鏂?351 GWh锛岄€犳垚鑳介噺瀹归噺楂樹及銆傚洜姝ゆ湰鐗堥€夋嫨椋庨櫓鏇村皬鐨?CISPO 涓嬬晫锛涜鏂囧寮虹増搴旀媶鍒?`battery_power_capacity_gw` 涓?`battery_energy_capacity_gwh`锛屽啀鐢ㄧ渷绾у疄闄呭姛鐜?鑳介噺鍒嗗埆鏍″噯銆?
### 11.5 闀挎湡璧勬簮鍋囪锛氬摢浜涘凡杩涘叆涓绘ā鍨嬶紝鍝簺鍙簲浣滀负鎯呮櫙

| 璧勬簮/鎶€鏈?| V0719 褰撳墠澶勭悊 | 鏈€鏂板彛寰勪笌鍒ゆ柇 | 鍚庣画璁烘枃寤鸿 |
|---|---|---|---|
| 鏍哥數 | 110/205/300/300 GW 鍏ㄥ浗鍖呯粶锛岀渷绾ф寜绠＄嚎鏉冮噸 | 2030 110 GW 鏈夊畼鏂归敋鐐癸紱杩滄湡涓虹爺绌跺亣璁?| 瀵?2050 涓婄晫鍋?230/300/350 GW 鏁忔劅鎬э紝骞舵姤鍛婄渷绾ф潈閲嶈鍒?|
| 鐢熺墿璐?BECCS | 鐜版湁鐪佺骇鐑€煎悓鏃剁害鏉熺噧鏂欎笌鍏变韩瑁呮満 | 涓嶉潤榛樻浛鎹负 2026 鏂版暟鎹泦 | 璁剧疆 current/updated/conservative collection 涓夌粍璧勬簮鎯呮櫙 |
| 鐢垫睜 | 2030 CISPO Table S17 65.85 GW 鍔熺巼涓嬬晫锛屽浐瀹?4h | 2025 瀹為檯 136 GW/351 GWh銆?.58h | 鎷嗗垎 GW 涓?GWh锛涙寜 2h/4h/8h 鎶€鏈皣寤烘ā |
| PHS | GHT 椤圭洰姹犱笂鐣岋紝2030 鏃㈡湁涓嬬晫 65.94 GW | 鏈€鏂板畼鏂?2030 鐩爣绾?160 GW锛涢」鐩睜 249.191 GW 鏄綔鍔涜€岄潪鐩爣 | 灏?160 GW 浣滀负鏀跨瓥鎯呮櫙 floor 鎴?calibration target锛屼笉搴旇褰撶墿鐞?upper |
| CSP | 鍥犵珯鐐规綔鍔涗笌閫愭椂鍓栭潰缂哄け鑰岀鐢?| 鏈€鏂板畼鏂?2030 澶槼鑳界儹鍙戠數绾?15 GW | 鏁版嵁琛ラ綈鍓嶄笉寮哄埗 15 GW锛涜ˉ榻愬悗鍗曡 `CSP_enabled` 鎯呮櫙 |
| 姘存枃 | 2019 GRFR + 鍗曞勾 monthly P30 proxy | 涓嶆槸姝ｅ紡 1980-2019 P30/Q10 | 澶氭按鏂囧勾銆佺幆澧冩祦瑙勫垯鍜屾绾ф椂婊炴晱鎰熸€?|
| 椋庡厜/缃戠粶宄板€?| 2023 鍗曞ぉ姘斿勾 | 涓嶈兘浠ｈ〃鍘嗗彶鏋佺鍜岄暱鏈熻祫婧愮ǔ鍋ユ€?| 澶氬ぉ姘斿勾杩愯锛泃runk coincident peak 鐢?constraint generation |

鍥藉鑳芥簮灞€ 2026 骞粹€滃崄浜斾簲鈥濊鍒掑悓鏃剁粰鍑?2030 骞存娊姘磋搫鑳界害 `160 GW`銆佹柊鍨嬪偍鑳界害 `300 GW`銆佸お闃宠兘鐑彂鐢电害 `15 GW`銆傝繖浜涙暟鍊奸€傚悎鐢ㄤ簬鏀跨瓥涓€鑷存€ф儏鏅垨缁撴灉澶栭儴鏍￠獙锛屼絾鍏跺惈涔夊垎鍒槸鍙戝睍鐩爣/棰勬湡瑁呮満锛屼笉绛変簬妯″瀷涓殑鐪佺骇鐗╃悊璧勬簮涓婇檺锛屼笉鑳戒笉鍔犲尯鍒嗗湴鍏ㄩ儴鍐欐垚纭?upper bound銆?
### 11.6 DC 鍙嶅悜鍙橀噺娑堥櫎涓庢帴鍙ｅ吋瀹?
鐢熶骇鍗曚綋妯″瀷鐜板湪鍒涘缓锛?
```text
flow_forward_gw:    411 脳 H
flow_reverse_ac_gw:  48 脳 H
```

363 鏉?DC 璧板粖鍙繚鐣欑害瀹氭柟鍚戠殑 `flow_forward_gw`銆傜渷绾у姛鐜囧钩琛°€丄C 鍏变韩瀹归噺鍜屽勾搴﹁礋鑽蜂腑蹇冧氦鎹㈠潎浣跨敤 active AC row 鏄犲皠锛涚粨鏋滃鍑烘椂鍐嶉噸寤?`411 脳 H` 鐨勭瀵嗗弽鍚戞暟缁勶紝骞舵妸 DC 琛屽～ 0锛屽洜姝ゆ棦鏈?`interprovincial_flow_hourly.csv` 鍜屼笅娓哥粨鏋滄帴鍙ｄ笉鍙樸€傚叏骞寸簿纭秷闄わ細

```text
363 脳 8760 = 3,179,880 variables
```

鏂扮殑 8760 瑙勬ā浼拌涓?`40,911,296 variables / 67,603,283 constraints / 520,920,489 nonzeros`锛岄潤鎬佹ā鍨嬪唴瀛樹及璁＄害 `36.0 GiB`銆傚彉閲忔暟姣斾慨姝ｅ墠 `44,091,176` 涓嬮檷 `7.21%`锛涜繖涓嶇瓑浜?barrier 宄板€煎唴瀛樻垨姹傝В鏃堕棿蹇呯劧鍚屾瘮涓嬮檷锛屼粛椤婚€氳繃鏈嶅姟鍣?168h/744h 闂ㄦ瀹炴祴銆?
### 11.7 楠岃瘉缁撴灉

| 楠岃瘉 | 缁撴灉 |
|---|---|
| 鍗曞厓娴嬭瘯 | `32/32 PASS`锛?7.62 s |
| 鏁版嵁鍖?smoke test | `139/139 PASS`锛屽寘鎷柊澧炶〃琛屾暟銆?1 鐪佽鐩栥€佸敮涓€閿€佷笂涓嬬晫闂悎鍜岄潪璐熸€?|
| 鏈湴 24h 涓ユ牸姹傝В | `OPTIMAL + solution_qc=PASS` |
| 24h 妯″瀷瑙勬ā | `341,312 variables / 261,280 constraints / 1,768,956 nonzeros` |
| 24h 姹傝В | Gurobi 39.79 s锛涙€?elapsed 82.45 s锛沺eak RSS 0.702 GiB |
| 鏂板杈圭晫 QC | nuclear floor/upper銆乥io+BECCS shared upper銆乥attery/PHS floor 鐨勬渶澶ц繚绾﹀潎涓?0 |
| 杈撶數 QC | 鏈€澶?DC 鍙嶅悜娼祦 0锛汚C 鍚屽皬鏃跺弻鍚戞祦 0锛涙渶澶у姛鐜囧钩琛℃畫宸?`7.43e-12 GW` |

涓庝慨姝ｅ墠鏈湴 24h 鍩虹嚎鐩告瘮锛屽彉閲忔暟绮剧‘鍑忓皯 `8,712 = 363脳24`锛岀害 `-2.49%`锛涢潪闆跺厓鍑忓皯 43,498锛岀害 `-2.40%`锛涙柊澧?31 鏉＄渷绾?bio+BECCS 鍏变韩瀹归噺绾︽潫銆傝娆℃眰瑙ｈ€楁椂楂樹簬鏃у熀绾?32.00 s锛屽彲鑳芥潵鑷柊澧炲閲忚竟鐣屽拰鍗曟姹傝В娉㈠姩锛屽洜姝ゆ湰鎶ュ憡涓嶅０绉扳€滆繍琛屽姞閫熲€濓紝鍙‘璁ょ粨鏋勬€у彉閲忔秷闄ゅ拰绉戝杈圭晫淇鍧囧凡閫氳繃銆?
绗竴娆¤繃鐭秴鏃剁殑 24h 灏濊瘯淇濈暀鍦?`outputs/2030_24h_v0719_capacity_bounds_dc_sparse` 浣滀负涓柇璁板綍锛涢獙鏀剁粨鏋滀綅浜?`outputs/2030_24h_v0719_capacity_bounds_dc_sparse_rerun`銆?4h 鐨勫勾搴︽垚鏈拰鏀跨瓥绾︽潫鏈缉鏀撅紝鐩爣鍊间笉鍏锋湁绉戝瑙勫垝鍚箟銆?
### 11.8 褰撳墠缁撹鍜屼笅涓€闂ㄦ

鍥涢」 P0 淇宸茬粡瀹屾垚锛屽師瀹℃煡鎶ュ憡涓€滄牳鐢点€佺敓鐗╄川/BECCS銆佺數姹犲拰 DC 鍙橀噺鈥濆洓涓樆鏂」涓嶅啀鏄湰鍦颁唬鐮佺己鍙ｃ€傚綋鍓嶆洿鍑嗙‘鐨?BECCS 缁撹鏄細**鐪佺骇娼滃姏杈撳叆鍘熸湰瀛樺湪锛涙鍓嶇己灏戠殑鏄笌骞村害鐕冩枡绾︽潫浜掕ˉ鐨勫叡浜鏈轰笂闄愶紝鐜板凡琛ラ綈骞跺姞浜嗘棦鏈夊閲忓彲琛屾€т繚鎶ゃ€?*

浣嗚繖浠嶄笉鎺堟潈鐩存帴杩愯 8760銆備笅涓€姝ュ簲鍦ㄤ笉骞叉壈鏃х増 744h 鐨勫墠鎻愪笅锛屽皢 working tree 鍥哄寲涓哄疄鏂?commit锛屽湪鏈嶅姟鍣ㄦ柊寤虹増鏈寲鏁版嵁鏍癸紝杩愯鐢熸垚鑴氭湰涓?readiness锛屽啀渚濇閫氳繃 24h銆?68h 鍜?corrected 744h銆傚彧鏈?corrected 744h 杈惧埌 `OPTIMAL + solution_qc=PASS`锛屼笖鏈嶅姟鍣ㄥ唴瀛?浜ゆ崲鍖烘弧瓒抽棬妲涘悗锛屾墠鍙繘琛?8760 build-only 涓?factor-risk 澶嶆牳銆?
### 11.9 澶栭儴鏁版嵁鏉ユ簮

- 鍥藉鑳芥簮灞€锛氥€婃柊鍨嬭兘婧愪綋绯诲缓璁锯€滃崄浜斾簲鈥濊鍒掋€嬶紙2030 鏍哥數銆佹娊钃勩€佹柊鍨嬪偍鑳戒笌澶槼鑳界儹鍙戠數鍙ｅ緞锛夛細<https://www.nea.gov.cn/20260625/0ccfdc1674e84868b49480edf584eb5f/202606250ccfdc1674e84868b49480edf584eb5f_27b526ec29479c4fd4bbb6f42d3ce5bbca.pdf>
- 鍥藉鑳芥簮灞€锛?025 骞存柊鍨嬪偍鑳藉彂灞曟儏鍐碉紙136 GW/351 GWh銆佸钩鍧?2.58h锛夛細<https://www.nea.gov.cn/20260130/50f657ce87f848e1a9a1861d1fd9aa23/c.html>
- 鍥藉鏍稿畨鍏ㄥ眬锛?025 骞磋繍琛屾牳鐢靛巶瀹夊叏鐘跺喌锛堣繍琛岃鏈?62,518.74 MWe锛夛細<https://nnsa.mee.gov.cn/ywdt/hyzx/202602/t20260206_1143783.html>
- 鍥藉鏍稿畨鍏ㄥ眬锛氥€婁腑鍥芥牳鑳藉彂灞曟姤鍛婏紙2025锛夈€嬪彂甯冧俊鎭紙102 鍙般€佺害 113 GW锛夛細<https://nnsa.mee.gov.cn/ywdt/hyzx/202504/t20250430_1118672.html>
- Scientific Data 2023锛屼腑鍥界渷绾х敓鐗╄川璧勬簮娼滃姏鏁版嵁锛?https://www.nature.com/articles/s41597-023-02227-7>
- Scientific Data 2026锛屾墿灞曠被鍒笌 2050 棰勬祴鐨勬洿鏂版暟鎹泦锛?https://www.nature.com/articles/s41597-026-07689-z>
