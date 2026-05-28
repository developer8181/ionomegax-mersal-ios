# بناء ISO — Mersal OS

## على Linux (موصى به)

```bash
cd mersal-os
./build/build-iso.sh
```

المخرجات: `dist/mersal-os-YYYYMMDD.iso`

## عبر Docker

```bash
./build/build-iso-docker.sh
```

## في GitHub Actions

Workflow `mersal-os-iso.yml` يرفع الـ ISO كـ artifact بعد كل push على `mersal-os/**`.

## التحقق

```bash
sha256sum dist/mersal-os-*.iso
```

```bash
qemu-system-x86_64 -m 2048 -cdrom dist/mersal-os-*.iso -boot d
```
