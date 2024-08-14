__version_info__ = {
    "major": 5,
    "minor": 2,
    "patch": 0,
    "releaselevel": "beta",
    "serial": 1
}


def get_version(short=False):
    assert __version_info__["releaselevel"] in ("alpha", "beta", "final")
    vers = ["%(major)i.%(minor)i" % __version_info__, ]
    if __version_info__["patch"]:
        vers.append(".%(patch)i" % __version_info__)
    if __version_info__["releaselevel"] != "final" and not short:
        vers.append(
            "%s%i" % (
                __version_info__["releaselevel"][0],
                __version_info__["serial"])
        )
    return "".join(vers)


__version__ = get_version()
