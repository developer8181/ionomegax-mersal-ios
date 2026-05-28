# تنزيل Mersal OS ISO

## الطريقة 1 — GitHub Actions (موصى بها)

1. افتح المستودع على GitHub.
2. تبويب **Actions** → workflow **Mersal OS ISO Build**.
3. **Run workflow** (أو انتظر اكتمال آخر تشغيل).
4. من صفحة التشغيل الناجح: **Artifacts** → `mersal-os-iso`.
5. حمّل `mersal-os-YYYYMMDD-amd64.iso` وملف `.sha256`.

## الطريقة 2 — البناء المحلي (موصى به)

```bash
cd mersal-os
sudo apt-get install -y debootstrap squashfs-tools xorriso isolinux syslinux-utils grub-pc-bin rsync
sudo ./build/build-iso-debootstrap.sh
ls -lh dist/
```

أو عبر live-build داخل Debian:

```bash
./build/build-iso-docker.sh
```

## التجربة في QEMU

```bash
qemu-system-x86_64 -m 4096 -smp 2 -cdrom dist/mersal-os-*.iso -boot d
```

## بعد الإقلاع

| البند | القيمة |
| --- | --- |
| المستخدم | `mersal` |
| كلمة المرور | `mersal` |
| مركز القيادة | http://127.0.0.1:8090/console/ |
| الحالة | `mersal-status` |

**Powered by Extreme Technology Company**
