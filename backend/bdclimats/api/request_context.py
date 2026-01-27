from contextvars import ContextVar

# Per-request id stored in a context var (safe for async).
_request_id = ContextVar("request_id", default=None)

def set_request_id(value):
    # Store request id for the current execution context.
    return _request_id.set(value)

def get_request_id(default=None):
    # Returns None when not set (default arg currently unused).
    if _request_id.get() is None:
        return None
    else:
        return _request_id.get()
