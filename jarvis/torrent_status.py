"""Read-only torrent status responses for JARVIS dialogue."""


def summarize_torrents(client, cookie):
    entries = client.progress(cookie)
    if not entries:
        return "В торрент-клиенте нет загрузок."
    lines = []
    for entry in entries[:10]:
        speed = entry["download_speed_bps"]
        eta = entry["eta_seconds"]
        estimate = "время неизвестно" if eta is None else str(eta) + " секунд"
        lines.append(
            entry["name"] + ": " + str(entry["progress_percent"])
            + "%, " + str(speed) + " байт/с, " + estimate
        )
    return "Текущие загрузки:\n" + "\n".join(lines)
