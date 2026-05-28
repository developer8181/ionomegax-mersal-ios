# Mersal OS 1.0.0 — إصدار تجريبي جاهز للتنزيل

**Ionomegax Mersal OS** — توزيعة Linux أمنية متكاملة  
**Powered by Extreme Technology Company**

---

## تنزيل سريع

| الملف | الرابط |
|-------|--------|
| **ISO (339 MB)** | [mersal-os-20260528-amd64.iso](https://github.com/developer8181/ionomegax-mersal-ios/releases/download/v1.0.0-mersal-os/mersal-os-20260528-amd64.iso) |
| **SHA256** | [mersal-os-20260528-amd64.iso.sha256](https://github.com/developer8181/ionomegax-mersal-ios/releases/download/v1.0.0-mersal-os/mersal-os-20260528-amd64.iso.sha256) |

```bash
sha256sum -c mersal-os-20260528-amd64.iso.sha256
```

---

## تسجيل الدخول بعد الإقلاع

| | |
|---|---|
| المستخدم | `mersal` |
| كلمة المرور | `mersal` |
| مركز القيادة | http://127.0.0.1:8090/console/ |

---

## لقطات من النظام

### مركز قيادة Mersal
![Command Center](https://github.com/developer8181/ionomegax-mersal-ios/releases/download/v1.0.0-mersal-os/01-command-center-ar.png)

### شاشة الإقلاع
![Boot](https://github.com/developer8181/ionomegax-mersal-ios/releases/download/v1.0.0-mersal-os/02-boot-screen.png)

### الشعار
![Logo](https://github.com/developer8181/ionomegax-mersal-ios/releases/download/v1.0.0-mersal-os/03-brand-logo.png)

### الطرفية — mersal-status
![Terminal](https://github.com/developer8181/ionomegax-mersal-ios/releases/download/v1.0.0-mersal-os/04-terminal-status.png)

---

## ما هو Mersal OS؟

ليس API فقط — **نظام تشغيل كامل** يجمع:

- **Mersal Command Center** — لوحة إدارة عربية/إنجليزية
- **Mersal Guard** — حماية نقاط النهاية و DLP
- **Mersal Gateway** — جدار ناري (nftables)
- **Mersal Update Orbit** — قناة تحديثات
- **Holonic Security Fabric** — سياسات موحّدة بين المركز والحافة

---

## التجربة في QEMU

```bash
qemu-system-x86_64 -m 4096 -smp 2 -cdrom mersal-os-20260528-amd64.iso -boot d
```

---

## الوثائق العربية الكاملة

[docs/README_AR.md](https://github.com/developer8181/ionomegax-mersal-ios/blob/cursor/mersal-os-distribution-eef7/mersal-os/docs/README_AR.md)

---

**Ionomegax · Mersal OS · Extreme Technology Company**
