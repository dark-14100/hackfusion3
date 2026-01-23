from . import extract_order, ParsedOrder

def debug_parse(text: str) -> ParsedOrder:
    """
    Convenience function you can use from a REPL or tests.
    """
    return extract_order(text)