from decimal import Decimal

from django import forms
from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST


PRODUCTS = [
    {
        "slug": "everyday-tote",
        "name": "Everyday Canvas Tote",
        "category": "Accessories",
        "price": Decimal("28.00"),
        "description": "A sturdy, thoughtfully sized carryall made for market runs, commutes, and everything in between.",
        "image": "https://images.unsplash.com/photo-1590874103328-eac38a683ce7?auto=format&fit=crop&w=900&q=85",
        "badge": "Bestseller",
    },
    {
        "slug": "ceramic-mug",
        "name": "Sunday Ceramic Mug",
        "category": "Home",
        "price": Decimal("22.00"),
        "description": "A hand-finished stoneware mug with a soft matte glaze. Made for slow mornings and second cups.",
        "image": "https://images.unsplash.com/photo-1514228742587-6b1558fcca3d?auto=format&fit=crop&w=900&q=85",
        "badge": "Small batch",
    },
    {
        "slug": "weekender-bottle",
        "name": "Weekender Water Bottle",
        "category": "Everyday",
        "price": Decimal("34.00"),
        "description": "Double-wall stainless steel keeps drinks cold for hours, with a leak-resistant lid for the road.",
        "image": "https://images.unsplash.com/photo-1602143407151-7111542de6e8?auto=format&fit=crop&w=900&q=85",
        "badge": "",
    },
    {
        "slug": "linen-notebook",
        "name": "Linen Pocket Notebook",
        "category": "Stationery",
        "price": Decimal("16.00"),
        "description": "A cloth-bound notebook with smooth, responsibly sourced paper for lists, sketches, and new ideas.",
        "image": "https://images.unsplash.com/photo-1531346878377-a5be20888e57?auto=format&fit=crop&w=900&q=85",
        "badge": "New",
    },
    {
        "slug": "weekend-cap",
        "name": "Weekend Cotton Cap",
        "category": "Accessories",
        "price": Decimal("30.00"),
        "description": "An easy-fitting, breathable cotton cap with an adjustable strap and a clean, everyday profile.",
        "image": "https://images.unsplash.com/photo-1588850561407-ed78c282e89b?auto=format&fit=crop&w=900&q=85",
        "badge": "",
    },
    {
        "slug": "woven-throw",
        "name": "Soft Woven Throw",
        "category": "Home",
        "price": Decimal("68.00"),
        "description": "A lightweight, textured throw that brings a little extra comfort to the sofa, bed, or reading chair.",
        "image": "https://images.unsplash.com/photo-1600369671236-e74521d4b6ad?auto=format&fit=crop&w=900&q=85",
        "badge": "Customer favorite",
    },
]
PRODUCT_BY_SLUG = {product["slug"]: product for product in PRODUCTS}
FREE_SHIPPING_THRESHOLD = Decimal("60.00")
STANDARD_SHIPPING = Decimal("5.00")


class CheckoutForm(forms.Form):
    name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={"autocomplete": "name"}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={"autocomplete": "email"}))
    address = forms.CharField(max_length=200, widget=forms.TextInput(attrs={"autocomplete": "street-address"}))
    city = forms.CharField(max_length=100, widget=forms.TextInput(attrs={"autocomplete": "address-level2"}))
    postcode = forms.CharField(max_length=20, widget=forms.TextInput(attrs={"autocomplete": "postal-code"}))


def _product_or_404(slug):
    product = PRODUCT_BY_SLUG.get(slug)
    if product is None:
        raise Http404("Product not found")
    return product


def _cart_summary(request):
    stored_cart = request.session.get("cart", {})
    items = []
    subtotal = Decimal("0.00")

    if isinstance(stored_cart, dict):
        for slug, raw_quantity in stored_cart.items():
            product = PRODUCT_BY_SLUG.get(slug)
            try:
                quantity = int(raw_quantity)
            except (TypeError, ValueError):
                continue
            if product is None or quantity < 1:
                continue
            line_total = product["price"] * quantity
            items.append({**product, "quantity": quantity, "line_total": line_total})
            subtotal += line_total

    shipping = Decimal("0.00") if subtotal == 0 or subtotal >= FREE_SHIPPING_THRESHOLD else STANDARD_SHIPPING
    return {
        "items": items,
        "item_count": sum(item["quantity"] for item in items),
        "subtotal": subtotal,
        "shipping": shipping,
        "total": subtotal + shipping,
        "free_shipping_threshold": FREE_SHIPPING_THRESHOLD,
        "amount_to_free_shipping": max(FREE_SHIPPING_THRESHOLD - subtotal, Decimal("0.00")),
    }


def home(request):
    products = PRODUCTS
    query = request.GET.get("q", "").strip()[:100]
    category = request.GET.get("category", "").strip()

    if query:
        lowered_query = query.casefold()
        products = [
            product for product in products
            if lowered_query in product["name"].casefold()
            or lowered_query in product["description"].casefold()
            or lowered_query in product["category"].casefold()
        ]
    if category in {product["category"] for product in PRODUCTS}:
        products = [product for product in products if product["category"] == category]
    else:
        category = ""

    context = _cart_summary(request)
    context.update({
        "products": products,
        "categories": sorted({product["category"] for product in PRODUCTS}),
        "query": query,
        "selected_category": category,
        "is_filtered": bool(query or category),
    })
    return render(request, "home.html", context)


def product_detail(request, slug):
    product = _product_or_404(slug)
    context = _cart_summary(request)
    context["product"] = product
    context["related_products"] = [
        item for item in PRODUCTS
        if item["category"] == product["category"] and item["slug"] != slug
    ][:3]
    return render(request, "product_detail.html", context)


def cart_view(request):
    return render(request, "cart.html", _cart_summary(request))


@require_POST
def cart_add(request, slug):
    product = _product_or_404(slug)
    try:
        quantity = int(request.POST.get("quantity", "1"))
    except (TypeError, ValueError):
        messages.error(request, "Please choose a valid quantity.")
        return redirect("product_detail", slug=slug)
    if not 1 <= quantity <= 99:
        messages.error(request, "You can add between 1 and 99 of an item.")
        return redirect("product_detail", slug=slug)

    cart = request.session.get("cart", {})
    if not isinstance(cart, dict):
        cart = {}
    try:
        current_quantity = int(cart.get(slug, 0))
    except (TypeError, ValueError):
        current_quantity = 0
    cart[slug] = min(current_quantity + quantity, 99)
    request.session["cart"] = cart
    messages.success(request, f"{product['name']} added to your bag.")
    return redirect("cart")


@require_POST
def cart_update(request, slug):
    _product_or_404(slug)
    try:
        quantity = int(request.POST.get("quantity", ""))
    except (TypeError, ValueError):
        messages.error(request, "Please enter a valid quantity.")
        return redirect("cart")
    if not 1 <= quantity <= 99:
        messages.error(request, "Quantity must be between 1 and 99.")
        return redirect("cart")

    cart = request.session.get("cart", {})
    if isinstance(cart, dict) and slug in cart:
        cart[slug] = quantity
        request.session["cart"] = cart
    return redirect("cart")


@require_POST
def cart_remove(request, slug):
    cart = request.session.get("cart", {})
    if isinstance(cart, dict) and slug in cart:
        cart.pop(slug)
        request.session["cart"] = cart
        messages.success(request, "Item removed from your bag.")
    return redirect("cart")


def checkout(request):
    summary = _cart_summary(request)
    if not summary["items"]:
        messages.info(request, "Your bag is empty. Find something you love first.")
        return redirect("home")

    form = CheckoutForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        request.session["cart"] = {}
        return render(request, "checkout_success.html", {
            "cart_count": 0,
            "order_name": form.cleaned_data["name"],
        })

    context = {**summary, "form": form}
    return render(request, "checkout.html", context)


def about(request):
    return render(request, "about.html", _cart_summary(request))


def contact(request):
    return render(request, "contact.html", _cart_summary(request))


def faq(request):
    return render(request, "faq.html", _cart_summary(request))


def shipping_returns(request):
    context = _cart_summary(request)
    context.update({
        "free_shipping_threshold": FREE_SHIPPING_THRESHOLD,
        "standard_shipping": STANDARD_SHIPPING,
    })
    return render(request, "shipping_returns.html", context)
