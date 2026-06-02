"""
Context processor — injects cart item count into every template.
Avoids an explicit cart fetch in every view.
"""

from . import services


def cart_context(request):
    try:
        sk = request.session.get("cart_session_key", "")
        if sk:
            cart = services.get_cart(sk)
            return {"cart_count": cart.get("total_items", 0)}
    except Exception:
        pass
    return {"cart_count": 0}
