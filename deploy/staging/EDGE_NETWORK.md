# Host-loopback ingress network correction

Observed on Docker 29.9.1: proxy HostConfig.PortBindings contains 127.0.0.1:8443,
but NetworkSettings.Ports has null and host TCP connect is refused. Only the internal
staging network is attached. Backend and frontend health endpoints respond internally.

Compose now attaches proxy alone to an additional regular bridge, mihur-staging_edge.
The explicit published port remains 127.0.0.1:8443:8443; the network default binding
also uses loopback. All other containers remain solely on the internal staging network.
This grants the container proxy outbound connectivity; do not describe the entire
stack as egress-denied. The API, gateway and databases retain internal-only networking.
No daemon firewall changes, public Docker ports, host network mode or DB changes.

Inventory allows exactly this project-owned bridge, required loopback option, and
only proxy container IDs as members; nonproxy attachments to edge/default/foreign
networks are rejected. The host Caddy remains responsible for public HTTPS and QA
IP restrictions. Existing host/README.md still applies except its statement that
only the host edge has public egress: the container proxy now has egress as well.

After independent review and merge (also include frontend smoke correction #444),
build a single new exact-main release. Update the root-only manifest's application
image digests and SHA, preserving DB password and supporting-image digests, and
checkout that exact SHA cleanly. Run preflight/pull/start/smoke/metrics. No migration,
seed, volume deletion or network deletion is required for this change. Compose
recreates proxy with both networks. Existing internal network and database persist.

Verify docker port for proxy shows 8443/tcp -> 127.0.0.1:8443, then perform TLS request
with --cacert and hostname localhost as in host/README.md. Verify from another host
that public-IP port 8443 is inaccessible. Test API/gateway egress denial and inspect
edge membership; do not infer isolation solely from healthy containers. Test host
HTTPS, QA deny rules and browser sessions separately. No runtime success is claimed
until these execute. Container proxy egress is an explicit review consideration.

Reference: https://docs.docker.com/engine/network/ (dual-network frontend pattern).
