# تثبيت EPMS على VPS خاص بك

يمكنك تشغيل **Extreme Print Management System** على سيرفرك (Ubuntu/Debian) بشكل **إنتاجي حقيقي**: مصادقة إلزامية، قاعدة بيانات محلية، وواجهة على نطاقك.

> **ملاحظة:** الوكيل السحابي لا يملك وصول SSH إلى VPS الخاص بك. أنت تنفّذ الأوامر على السيرفر؛ هذا الدليل يجهّز كل ما تحتاجه.

---

## المتطلبات

| البند | التفاصيل |
|--------|-----------|
| نظام التشغيل | Ubuntu 22.04+ أو Debian 12+ |
| الموارد | 1 vCPU، 1 GB RAM كحد أدنى (2 GB مُفضّل) |
| المنافذ | 80 و 443 (و 8080 داخلياً) |
| النطاق | اختياري — مثال: `print.yourcompany.com` |

---

## الطريقة 1 — تثبيت تلقائي (موصى به)

### 1) انسخ المشروع إلى الـ VPS

```bash
sudo apt update && sudo apt install -y git
sudo mkdir -p /opt/epms
cd /opt/epms
sudo git clone https://github.com/developer8181/ionomegax-mersal-ios.git repo
cd repo/extreme-print-management-system
```

### 2) شغّل مثبّت الـ VPS

**مع Docker (الأسهل):**

```bash
sudo bash scripts/install_on_vps.sh \
  --method docker \
  --domain print.example.com \
  --email admin@example.com
```

**بدون Docker (systemd):**

```bash
sudo bash scripts/install_on_vps.sh \
  --method native \
  --domain print.example.com \
  --email admin@example.com
```

**بدون نطاق (IP فقط):**

```bash
sudo bash scripts/install_on_vps.sh --method docker --skip-nginx
```

### 3) اقرأ بيانات المسؤول

```bash
sudo cat /opt/epms/CREDENTIALS.txt
```

ستجد:

- رابط الواجهة
- مستخدم `admin` وكلمة المرور المُولَّدة
- أوامر السجلات والصيانة

---

## الطريقة 2 — يدوياً (Docker)

```bash
cd extreme-print-management-system
bash scripts/provision_production.sh
set -a && source deploy/production.generated.env && set +a

export EPMS_SESSION_SECRET
export EPMS_AGENT_TOKEN
export EPMS_BOOTSTRAP_ADMIN_PASSWORD

docker compose -f deploy/docker-compose.production.yml up --build -d
curl -s http://127.0.0.1:8080/api/health
```

---

## الطريقة 3 — يدوياً (systemd)

```bash
bash scripts/provision_production.sh
sudo mkdir -p /etc/epms
sudo cp deploy/production.generated.env /etc/epms/production.env
sudo chmod 600 /etc/epms/production.env
sudo useradd --system --home /opt/epms epms 2>/dev/null || true
sudo cp deploy/epms.service /etc/systemd/system/epms.service
# عدّل مسار WorkingDirectory في epms.service إن لزم
sudo systemctl daemon-reload
sudo systemctl enable --now epms
```

---

## Nginx + HTTPS

بعد التثبيت مع `--domain` و `--email`، يُفعَّل Let's Encrypt تلقائياً.

يدوياً:

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
sudo cp deploy/nginx/epms.conf.example /etc/nginx/sites-available/epms
# استبدل EPMS_DOMAIN بنطاقك
sudo ln -s /etc/nginx/sites-available/epms /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d print.example.com
```

---

## جدار الحماية (UFW)

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

لا تفتح المنفذ `8080` للعامة إذا استخدمت Nginx.

---

## ماذا يكون «حقيقياً» بعد التثبيت على VPS؟

| يعمل فعلياً | يحتاج ربطاً إضافياً |
|-------------|---------------------|
| تسجيل دخول المسؤولين وجلسات | طابعات فيكتورية → أجهزة حقيقية |
| قاعدة SQLite على السيرفر | Print Provider على Windows/Linux |
| سياسات الحصص والمهام | CUPS / مسارات الطباعة |
| محطة التحرير على نطاقك | SDK المصنع على MFD |

---

## النسخ الاحتياطي

```bash
cd /opt/epms/extreme-print-management-system
bash scripts/backup_epms.sh
```

---

## تحديث النسخة

```bash
cd /opt/epms/repo
sudo git pull
cd extreme-print-management-system
sudo docker compose -f deploy/docker-compose.production.yml up --build -d
# أو: sudo systemctl restart epms
```

---

## استكشاف الأخطاء

| المشكلة | الحل |
|---------|------|
| لا يفتح الموقع | `curl http://127.0.0.1:8080/api/health` على السيرفر |
| 401 بعد الدخول | تأكد من `EPMS_REQUIRE_AUTH=true` وكلمة المرور من `CREDENTIALS.txt` |
| Docker لا يبني | `docker compose logs -f` |
| certbot فشل | تأكد أن DNS يشير إلى IP الـ VPS |

---

## الدعم

بعد التثبيت أرسل (بدون كلمة المرور):

- ناتج `curl -s http://127.0.0.1:8080/api/production/checklist`
- نظام التشغيل وطريقة التثبيت (docker / native)
