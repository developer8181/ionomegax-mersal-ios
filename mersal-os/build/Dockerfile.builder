FROM debian:bookworm
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    live-build debootstrap squashfs-tools xorriso isolinux syslinux-utils \
    grub-pc-bin grub-efi-amd64-bin mtools dosfstools rsync openssl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /mersal-os
