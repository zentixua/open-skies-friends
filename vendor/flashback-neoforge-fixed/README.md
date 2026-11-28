# Flashback NeoForge Fixed 1.0.19+os1

A build of [Flashback NeoForge Fixed](https://github.com/tatuto-riku/flashback-neoforge-fixed) by tatuto-riku
(MIT License, `LICENSE`), from its tag `v1.0.19` with one change, `os1.patch`: the mod's list of payloads that are
never recorded or replayed (`ReplayPayloadPolicy.TRANSIENT_CLIENT_EFFECTS`) also holds the distant-terrain streams
`incoming:voxy_chunk_z`, `incoming:voxy_chunk`, `incoming:lod_batch_finished` and `lss:voxel_column`. During
playback the mod points Voxy at the recording client's own store, so a replay never uses these payloads; recording
them makes the recording buffer grow by copying and makes saving the replay freeze the game for seconds.
Every other class in the jar is byte-identical to the Modrinth jar of 1.0.19. The jar also carries the author's
license as `LICENSE_flashback_neoforge_fixed`.

Build: the tag's sources with the patch applied, `./gradlew build` (Java 21), the compile-only jars from `libs/README.md`
taken from the pack (Flashback 0.39.10 as remapped by Sinytra Connector, Sable 2.0.6). The file is named
`…-1.0.19-os1.jar` because a `+` in a URL path needs escaping; the mod's version inside is `1.0.19+os1`.

This build stays until the author offers a way to keep payloads out of recordings; then the pack returns to the
Modrinth release.
