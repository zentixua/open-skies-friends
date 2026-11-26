# Servers and hosts (team reference; rules in .claude/rules/team.md)

Procedures: the `game-servers` skill. Live state (ports in use, settings, golden maps): the lead's project files.

## netcup
- 12 vCPU EPYC, 31 GiB, Ubuntu 24.04, no GPU, no sudo; Artem's Docker services are not ours; keep ≥ 4 GB free.
- The host reboots itself for kernel updates and Crafty servers do not autostart afterwards.
- CPU-rendered incoming clients (vanilla frames, incoming `client-scenario.md` "CPU rendering"): clone in
  `~/incoming-soft`, Java 21 in `~/jdk-21*`; environment `JAVA_HOME=~/jdk-21* ORG_GRADLE_PROJECT_noRecompile=1
  ORG_GRADLE_PROJECT_mcModsDir=run/ci-mods GRADLE_OPTS="-Dorg.gradle.daemon=false -Xmx1200m" INCOMING_SOFT_HEAP=1536m`,
  then `tools/sandbox.sh start` / `shot` as on the laptop; one client at a time; copy frames back with `scp`. A
  `tools/client_scenario.sh` run that generates a fresh world (`commands`) needs `INCOMING_SOFT_HEAP=3072m`: at 1536m
  its 3.5 GB job ceiling stops the client during world creation.
- Other work needing no GPU (probes, dumps, builds, GameTest; team.md Machines) uses the same clone and environment, one
  heavy JVM at a time beside the CPU client, at the lowest CPU priority (`nice -n 19`, Gradle `--max-workers=4`): the
  play servers keep their cores. Start it only when `free -m` leaves its heap (GameTest: a quarter of RAM unless `-Xmx`
  is given) plus the 4 GB reserve, and `df -h ~` has room for what it writes (world copies, frames).
- The laptop reaches it with `ssh vps` (Tailscale, user ubuntu). Slow Tailscale upload: check the laptop's wlan IPv6
  MTU first (a mobile router announces 1280; `nmcli` ipv6.mtu 1480 on that connection fixes it). Downloads through the
  tailnet carry about 2 MB/s, through netcup's public address 12–16 MB/s (the route players use): a laptop client
  measuring a netcup server tunnels over the public address (`ssh -o HostName=<public IP> -L …`), or the tailnet paces
  what players get faster.
- A netcup Remote Control session starts only on Artem's message in that thread, hears only his messages and returns
  text only; stop it once its task is done (it answers every message and burns quota); a replacement first checks for
  the old process and its jobs.

## Crafty container
- `~/airstrike-server/crafty/docker-compose.yml`, container `airstrike_crafty`. Game ports are published there, TCP and
  UDP (Sable syncs sub-levels over UDP on the game port); the panel and the Almighty bridge on loopback only. Changes
  to it recreate the container (`docker compose up -d crafty`), which stops every server: stop them first through
  Crafty, then start them again; Crafty does not start them by itself. A changed container address needs
  `tailscale serve --tcp 25571` again.
- `sysctls: net.ipv4.tcp_notsent_lowat=16384` caps unsent data per game socket at 16 KiB (the host default is
  unlimited). Without the cap a far-terrain or LOD burst queues megabytes in the socket ahead of movement and
  keepalive packets, which then wait 50–200 ms on a mobile line. With it, the kernel stops taking new data at the
  limit (kernel `Documentation/networking/ip-sysctl.rst`, tcp_notsent_lowat; default UINT_MAX), so the server keeps
  the queue and urgent packets are not stuck behind it. 16 KiB is Cloudflare's tuned value for low-latency streams
  (blog "HTTP/2 prioritization with NGINX"); Docker sets namespaced `net.*` sysctls per container (`docker run
  --sysctl`). Check:
  `docker exec airstrike_crafty cat /proc/sys/net/ipv4/tcp_notsent_lowat` prints 16384.

## Crafty play servers
- online-mode=false + TrueUUID (licensed players verified via Mojang, unknown names offline only), whitelist, op only
  ZentixUA; plain offline mode on a public IP is unsafe. A new player gets the right UUID in
  `config/trueuuid-registry.json` (Artem's brother plays with an offline UUID registered there). The Crafty panel is tailnet-only; its admin
  password file is never copied.
- Stops, restarts, world resets or deletions of any server, and starting a public one, need Artem's own line in the
  working thread.
- Golden worlds ship pre-generated chunks plus a prebuilt LSS store (`<world>/lss-lod/`, SQLite, copied with the
  world): Chunky on a prep server, then `/lsslod store backfill start` (never while Chunky runs). The store drops
  itself on registry drift: re-run backfill. A golden reset bumps .mca header stamps of changed chunks (reset.sh /
  mark_stale.py), or clients keep blasted LODs.
- `reset.sh` copies golden before it deletes the played world, then starts a background `--stage` that makes another
  full golden copy for the next reset: on a nearly full netcup disk both fail (a half copy fills the disk under
  running servers). Check `df -h ~` first; with less free than golden plus a margin, compare, delete the played world,
  then copy (mark_stale plan kept in memory) and skip the stage.
- Every Crafty server's `start.sh` (and `~/airstrike-server/template/start.sh`) installs the pack with
  packwiz-installer from `https://raw.githubusercontent.com/zentixua/open-skies-friends/main/pack/pack.toml`. A
  server still on `zentixua/open-skies/…` gets the public Open Skies pack once that repository switches (another mod
  set: friends cannot join). Moving a server: replace the address in its `start.sh` (takes effect at its next start;
  the same pack, so no restart is needed for the move itself).
- packwiz installs only mods on a server, not the loader: when `pack.toml` changes `[versions] neoforge`, install that
  NeoForge on each server with the official installer (Artem's line).
- A pre-release test jar on a server or in Artem's Prism needs packwiz disabled (server `start.sh`, Prism
  PreLaunchCommand) with backups; restore both right after the release, or neither gets pack updates again. Play
  servers run without `MaxTenuringThreshold=1`/`SurvivorRatio=32` (early promotion doubled heap peaks).
- `airstrike-world reset tiktok` deletes the played world; never say it is kept.
- Almighty full-map war for TikTok: driver `~/airstrike-server/gm-agent/war/war.py` (`tiktok prep` → `run --minutes N
  --follow ZentixUA [--mspt 30]` → `stop` → `teardown`); one spectator bot per side owns its SAMs (console strikes are
  hostile to every SAM); launch only on Artem's «го», stop on «стоп».

## Laptop
- Remote Control is the only way into the laptop from the cloud or netcup. Its Claude app can stay online in Tailscale
  yet stop picking up Remote Control sessions; new sessions then wait in their queue (up to 24 h) and nothing on the
  laptop is reachable: it answers `tailscale ping` from netcup, but every TCP port is refused (no sshd, no Tailscale
  SSH). Recovery is restarting the Claude app at the laptop. A fallback shell needs Artem at the laptop once:
  `sudo tailscale set --ssh` plus a Tailscale ACL rule allowing netcup → laptop SSH.
- TikTok recording: `mc-vertical` (~/.local/bin) toggles a borderless 9:16 Minecraft window; the «OBS TikTok»
  desktop shortcut records, F9 starts.
- Friends' PCs are 1.5–2× weaker than Artem's laptop: frame-cost limits must hold there (Artem, 02.10).
