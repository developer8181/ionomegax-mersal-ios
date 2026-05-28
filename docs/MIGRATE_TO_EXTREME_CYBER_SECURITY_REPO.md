# نقل المشروع إلى مستودع Extreme Cyber Security

## 1. إنشاء المستودع على GitHub

اسم مقترح: **`extreme-cyber-security`**  
العنوان: **Extreme Cyber Security**

من الواجهة: New repository → Public → لا تضف README (الدفع سيأتي من الفرع).

## 2. رفع الكود

```bash
cd /path/to/ionomegax-mersal-ios
git fetch origin cursor/extreme-cyber-security-rebrand-eef7
git checkout cursor/extreme-cyber-security-rebrand-eef7

git remote add ecs https://github.com/developer8181/extreme-cyber-security.git
git push -u ecs cursor/extreme-cyber-security-rebrand-eef7:main
```

## 3. التشغيل

```bash
cd xtreme-ip-guard
make enterprise-install
source mersal-guard.env
python3 -m xig
```

Command Center: http://127.0.0.1:8090/console/

## حقوق النشر

لم تتغير: **© 2009–2026 Extreme Technology Company · Eng. Mahmoud Rasem Bayari · Ramallah**

المنتج أُعيد تسميته إلى **Extreme Cyber Security** مع الإشارة إلى سلالة Ionomegax Mersal في `xig/brand.py`.
