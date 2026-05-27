# دمج أفكار NethServer و Fortinet في Mersal OS

## قانوني وعملي

| المصدر | ما نأخذها | التنفيذ في Mersal |
| --- | --- | --- |
| NethServer | وحدات خدمة، بوابة فرع | `mersal-gateway` + Cockpit |
| Fortinet | UTM, IPS, تحديثات تهديدات | nftables + Suricata + Update Orbit |
| Palo Alto (فكرة) | سياسة حسب التطبيق | تصنيف تدفقات في Policy Mesh |
| Wazuh (فكرة) | SIEM | تكامل سجلات `journald` → مركز |

## طبقات التوزيعة

1. **Base** — Debian Bookworm live + firmware
2. **Hardening** — AppArmor, sysctl, nftables default deny
3. **Gateway** — Suricata IPS, DNS filtering stub
4. **Guard** — Mersal Guard preinstalled
5. **Console** — Command Center on :8090
6. **Update Orbit** — `mersal-update` CLI

## التحديثات

| القناة | المحتوى | التكرار |
| --- | --- | --- |
| `stable` | ISO + حزم موقّعة | شهري |
| `security` | توقيعات IPS/IOC | يومي |
| `policy` | قواعد DLP | عند التغيير |
