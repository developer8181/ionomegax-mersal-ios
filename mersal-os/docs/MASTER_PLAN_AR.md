# الخطة الكاملة — Mersal OS

## الرؤية

توزيعة Linux مؤسسية **جاهزة للتجربة** تحمل علامة **Extreme Technology Company** ومنصة **Ionomegax Mersal Guard**.

## المراحل

### المرحلة 1 — ISO تجريبي (الحالي)

- [x] live ISO amd64
- [x] Mersal Guard + Command Center
- [x] Gateway أساسي (nftables)
- [x] شعار Extreme + Powered by
- [x] مستخدم تجريبي `mersal`

### المرحلة 2 — تثبيت على القرص

- مثبت Calamares أو debian-installer مخصص
- تشفير LUKS افتراضي

### المرحلة 3 — Update Orbit كاملة

- خادم تحديثات موقّع
- `mersal-update apply security`

### المرحلة 4 — شهادات وامتثال

- STIG/basic hardening profiles
- تقارير PDF من المركز

## متطلبات الأجهزة

| الاستخدام | RAM | قرص |
| --- | --- | --- |
| Live تجريبي | 2 GB | — |
| فرع Gateway | 4 GB | 32 GB |
| مركز إدارة | 8 GB | 100 GB |

## التسمية

- المنتج: **Mersal OS**
- الشركة: **Extreme Technology Company**
- المنصة الأم: **Ionomegax**
