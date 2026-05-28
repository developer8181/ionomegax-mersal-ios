# Mersal OS v5.0.0 — إصدار ISO Live

## العربية

**Mersal OS** توزيعة Linux أمنية تجريبية (Live ISO) مبنية على Debian 12 Bookworm، تتضمن **Mersal XDR Enterprise Platform v5.0** مدمجاً محلياً.

| البند | التفاصيل |
|--------|----------|
| **الإصدار** | 5.0.0 (codename: xdr) |
| **المعمارية** | amd64 |
| **المهندس** | محمود راسم بياري — رام الله، فلسطين |
| **الشركة** | Ionomegax / Extreme Technology |
| **الحقوق** | © 2009–2026 |

### التنزيل

- ملف ISO: `mersal-os-YYYYMMDD-amd64.iso`
- تحقق: `sha256sum -c mersal-os-YYYYMMDD-amd64.iso.sha256`

### التشغيل

1. احرق ISO على USB أو شغّله في QEMU/VMware/VirtualBox.
2. اختر **Mersal** من قائمة الإقلاع.
3. دخول تجريبي: `mersal` / `mersal`
4. مركز القيادة: http://127.0.0.1:8090/console/

```bash
qemu-system-x86_64 -m 4096 -smp 2 -cdrom mersal-os-*-amd64.iso -boot d
```

### المزايا المدمجة

- Mersal Command Center + XDR / SIEM / EDR / Log Vault
- Mersal Endpoint Agent و Gateway
- nftables، خدمات systemd للمنصة

---

## English

**Mersal OS** — security-focused Debian 12 live ISO with **Mersal XDR Platform v5.0** pre-installed.

Trial login: `mersal` / `mersal` · Command Center: http://127.0.0.1:8090/console/

Built with `./build/build-iso-debootstrap.sh` (see [BUILD_ISO_AR.md](BUILD_ISO_AR.md)).
