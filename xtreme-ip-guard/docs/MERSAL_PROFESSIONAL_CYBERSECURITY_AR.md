# Mersal — منصة أمن سيبراني محترفة للمؤسسات

## لمن هذا النظام؟

**أي مؤسسة أو شركة أو منظمة** تحتاج منصة موحّدة لـ:

- حماية نقاط النهاية (DLP / EDR خفيف)
- SIEM وارتباط تهديدات (XDR)
- SOAR واستجابة حوادث
- GRC (NIST / ISO / SOC2)
- عزل مؤسسات (multi-tenant) وصلاحيات SOC (RBAC)

## مبادئ الأمان (تفكير خبير SOC)

| الطبقة | Mersal v7.1 |
|--------|-------------|
| **الهوية** | لا API مفتوح — مصادقة إلزامية (إلا `MERSAL_DEV_MODE=1` للمختبر) |
| **الصلاحيات** | RBAC على كل مسار — viewer / analyst / soc_admin / super_admin |
| **العزل** | `tenant_id` على البيانات الحساسة |
| **الوكلاء** | مفتاح لكل وكيل (`/api/agents/register-key`) — اختياري إلزامي في الإنتاج |
| **الشبكة** | TLS + mTLS للوكلاء، rate limiting، قائمة IP للدخول |
| **التدقيق** | سجل hash chain + `/api/audit/verify` |
| **الامتثال** | ضوابط NIST مرتبطة بإعدادات حقيقية (ليس دائماً «نعم») |

## التشغيل لأي شركة

```bash
cd xtreme-ip-guard
pip install -r requirements.txt
cp mersal-guard.organization.example.env mersal-guard.env
# عدّل الأسرار: openssl rand -hex 32
source mersal-guard.env
./scripts/provision-organization.sh
python3 -m xig
```

## وضع المختبر فقط

```bash
export MERSAL_DEV_MODE=1
python3 app.py
```

**لا تستخدم DEV_MODE في الإنترنت.**

## ما بعد v7.1 (طريق المنصات العالمية)

1. PostgreSQL + توسع أفقي  
2. EDR عميق (eBPF / kernel)  
3. SSO SAML/OIDC  
4. Suricata مُدار + قواعد YARA ملفات  
5. توقيع التحديثات والـ ISO  

---

© Extreme Technology · Ionomegax Mersal v7.1
