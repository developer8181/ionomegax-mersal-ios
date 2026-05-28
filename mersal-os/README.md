# Mersal OS

**[الوثائق العربية الكاملة · لقطات · تنزيل ISO](docs/README_AR.md)**

**Mersal OS** is a secure enterprise Linux distribution by **Ionomegax**, powered by **Extreme Technology Company**.

## Download ISO (GitHub Release)

**[Releases — mersal-os-20260528-amd64.iso (~339 MB)](https://github.com/developer8181/ionomegax-mersal-ios/releases)**

Login: `mersal` / `mersal` · Console: http://127.0.0.1:8090/console/

It unifies:

- **Mersal Guard** — endpoint DLP and zero-trust enforcement
- **Mersal Gateway** — NGFW/UTM patterns (nftables + Suricata)
- **Mersal Policy Mesh** — one policy brain across gateway and endpoints
- **Mersal Update Orbit** — signed security and policy updates

## Download ISO (trial)

After building:

```bash
sudo apt-get install -y debootstrap squashfs-tools xorriso isolinux syslinux-utils
make iso
ls -lh dist/*.iso
```

Or download from GitHub Actions artifact **mersal-os-iso** on the latest workflow run.

## Quick try (VM)

1. Flash `dist/mersal-os-*.iso` to USB or attach to a VM (2 GB RAM, 20 GB disk).
2. Boot **Mersal OS Live**.
3. Login: user `mersal` / password `mersal` (change on first boot).
4. Open **http://127.0.0.1:8090/console/** for Command Center.
5. Run `mersal-status` for gateway + guard health.

## Documentation

- [Master plan (AR)](docs/MASTER_PLAN_AR.md)
- [Security stack — NethServer + Fortinet ideas (AR)](docs/SECURITY_STACK_AR.md)
- [Holonic architecture (AR)](docs/HOLONIC_ARCHITECTURE_AR.md)
- [Build ISO](docs/BUILD_ISO_AR.md)

## Brand

Logos: `brand/logo-mersal-os.svg`, `brand/logo-powered-by-extreme.svg`
