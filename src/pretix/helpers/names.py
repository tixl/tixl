from pretix.base.settings import PERSON_NAME_SCHEMES


def build_name(parts, concatenation=None):
    if not parts:
        return ""
    if "_legacy" in parts:
        return parts["_legacy"]
    if "_scheme" in parts:
        scheme = PERSON_NAME_SCHEMES[parts["_scheme"]]
    else:
        raise TypeError("Invalid name given.")
    if not concatenation or concatenation not in scheme:
        concatenation = "concatenation"
    return scheme[concatenation](parts).strip()
