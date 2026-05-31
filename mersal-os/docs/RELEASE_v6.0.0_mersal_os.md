# Mersal OS 6.0.0 — Extreme Cyber Security Edition (Live ISO)

## العربية

**Mersal OS 6.0.0** (codename: `global-alternative`) — توزيعة Linux أمنية Live ISO تتضمن **Extreme Cyber Security Platform 1.1.0** كاملة محلياً.

| البند | التفاصيل |
|--------|----------|
| **إصدار النظام** | 6.0.0 |
| **حزمة المنصة** | extreme-cyber-security-1.1.0 |
| **المعمارية** | amd64 |
| **القاعدة** | Debian 12 Bookworm |
| **المهندس** | محمود راسم بياري — رام الله، فلسطين |
| **الحقوق** | © 2009–2026 Extreme Technology |

### التنزيل

- ملف ISO: `mersal-os-6.0.0-YYYYMMDD-amd64.iso`
- تحقق: `sha256sum -c mersal-os-6.0.0-*.iso.sha256`
- يُبنى تلقائياً عبر GitHub Actions: workflow **Mersal OS ISO Build**

### التشغيل

```bash
qemu-system-x86_64 -m 4096 -smp 2 -cdrom mersal-os-6.0.0-*-amd64.iso -boot d
```

1. اختر **Mersal** من قائمة الإقلاع  
2. دخول تجريبي: `mersal` / `mersal`  
3. مركز القيادة: http://127.0.0.1:8090/console/  
4. البديل العالمي: `POST /api/platform/global-alternative/activate`

### المزايا المدمجة (جديد في 6.0)

- Extreme Cyber Security Command Center (وضع داكن)
- XDR · SIEM · SOAR · EDR · امتثال · تكامل OIDC/SAML/SCIM
- مؤشر تكافؤ عالمي + تفعيل بديل متكامل
- وكيل نقطة نهاية + بوابة nftables/Suricata

### لقطات

راجع `mersal-os/docs/screenshots/` و `xtreme-ip-guard/docs/screenshots/` (20 شاشة للمنصة).

### البناء المحلي

```bash
cd mersal-os
./scripts/sync-iso-screenshots.sh
sudo ./build/build-iso-debootstrap.sh
```

---

## English

**Mersal OS 6.0.0** ships **Extreme Cyber Security 1.1.0** as an integrated global-alternative stack on a bootable Live ISO.

See `docs/BUILD_ISO_AR.md` for build steps and `docs/DOWNLOAD_AR.md` for distribution notes.

---

© Extreme Technology Company · Eng. Mahmoud Rasem Bayari
