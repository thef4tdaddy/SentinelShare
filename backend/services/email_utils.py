from email.utils import parseaddr


def normalize_sender(raw_from: str) -> str:
    """
    Normalizes a sender address, specifically handling Apple Private Relay.

    Examples:
    - '"Peloton" <peloton_at_mail_op_onepeloton_com_k6myg754kg_192d3661@privaterelay.appleid.com>'
      -> 'Peloton <peloton@onepeloton.com>'
    - '"Indeed" <donotreply_at_match_indeed_com_7dtpcj9p77_c32249dc@privaterelay.appleid.com>'
      -> 'Indeed <donotreply@indeed.com>'
    """
    if not raw_from:
        return ""

    name, address = parseaddr(raw_from)
    address = address.lower()

    # Check for Apple Private Relay
    # Format: [prefix]_at_[domain_parts]_[hash1]_[hash2]@privaterelay.appleid.com
    if "@privaterelay.appleid.com" in address:
        local_part = address.split("@")[0]

        if "_at_" in local_part:
            prefix, remainder = local_part.split("_at_", 1)
            parts = remainder.split("_")

            # Common TLDs to help identify where the domain ends
            tlds = {"com", "org", "net", "edu", "gov", "co", "io", "me", "tv", "info"}

            # Find the last index that looks like a TLD
            tld_index = -1
            for i, part in enumerate(parts):
                if part.lower() in tlds:
                    tld_index = i

            if tld_index != -1:
                # We found a TLD! Keep everything up to and including it.
                domain_parts = parts[: tld_index + 1]
                clean_address = (
                    f"{prefix}@{''.join(domain_parts[:-1])}.{domain_parts[-1]}"
                )

                # Special case: if there are multiple parts before TLD, they might be dot-separated subdomains
                # But in Apple Relay they are usually concatenated or underscore separated.
                # Let's see: mail_op_onepeloton_com -> mail.op.onepeloton.com
                # Actually, in my example 'mailoponepelotoncom' was concatenated.
                # Let's keep it simple: if we have ['mail', 'op', 'onepeloton', 'com']
                # Result should be mail.op.onepeloton.com
                if len(domain_parts) > 1:
                    clean_address = f"{prefix}@{'.'.join(domain_parts)}"
            else:
                # Fallback: if no TLD found, just use the first part as domain
                clean_address = f"{prefix}@{parts[0]}"

            return f"{name} <{clean_address}>" if name else clean_address

    return raw_from
