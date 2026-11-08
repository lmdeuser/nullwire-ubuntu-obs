FROM ubuntu:26.04
ENV DEBIAN_FRONTEND=noninteractive TMPDIR=/var/tmp/telegram
RUN mkdir -p "$TMPDIR" && chmod 1777 "$TMPDIR" && apt-get update && apt-get install -y --no-install-recommends \
 ca-certificates xdg-utils libglib2.0-0t64 libx11-6 libxcb1 libfontconfig1 libfreetype6 libegl1 libgl1 libxkbcommon0 libxkbcommon-x11-0 \
 libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-render-util0 libxcb-xinerama0 libxcb-randr0 libxcb-shape0 libxcb-xfixes0 libxcb-sync1 libxcb-render0 libxcb-shm0 \
 libgtk-3-0t64 libasound2t64 libpulse0 libsecret-1-0 libdbus-1-3 xvfb xauth x11-utils dbus-x11 desktop-file-utils python3 procps \
 && useradd --create-home tester && rm -rf /var/lib/apt/lists/*
COPY tools/container-check.sh /usr/local/bin/container-check
ENTRYPOINT ["/usr/local/bin/container-check"]
