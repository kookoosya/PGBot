"""In-memory AI mode state for VK bot peers."""

_ai_peers: set[int] = set()


def enter_ai_mode(peer_id: int) -> None:
    _ai_peers.add(peer_id)


def exit_ai_mode(peer_id: int) -> None:
    _ai_peers.discard(peer_id)


def is_ai_mode(peer_id: int) -> bool:
    return peer_id in _ai_peers


def get_ai_peers() -> set[int]:
    return set(_ai_peers)
