from django.test import TestCase
from django.urls import reverse


class StorefrontTests(TestCase):
    def test_home_displays_products_and_stylesheet(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "DjangoPixel")
        self.assertContains(response, "Everyday Canvas Tote")
        self.assertContains(response, "/static/css/style.css")
        self.assertContains(response, "/static/images/sun.jpg")

    def test_about_page_uses_project_photo(self):
        response = self.client.get(reverse("about"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "/static/images/pexel.jpg")

    def test_support_pages_render_and_are_linked_from_navigation(self):
        faq_response = self.client.get(reverse("faq"))
        self.assertEqual(faq_response.status_code, 200)
        self.assertContains(faq_response, "Can I place a real order or make a payment?")
        self.assertContains(faq_response, reverse("shipping_returns"))

        shipping_response = self.client.get(reverse("shipping_returns"))
        self.assertEqual(shipping_response.status_code, 200)
        self.assertContains(shipping_response, "$5.00")
        self.assertContains(shipping_response, "$60")
        self.assertContains(shipping_response, "doesn’t charge a payment method")
        self.assertContains(shipping_response, reverse("faq"))

    def test_search_filters_products(self):
        response = self.client.get(reverse("home"), {"q": "mug"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sunday Ceramic Mug")
        self.assertNotContains(response, "Everyday Canvas Tote")

    def test_product_detail_exists(self):
        response = self.client.get(reverse("product_detail", args=["ceramic-mug"]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Made for slow mornings")

    def test_cart_add_update_remove_and_shipping(self):
        add_url = reverse("cart_add", args=["ceramic-mug"])
        response = self.client.post(add_url, {"quantity": "2"})
        self.assertRedirects(response, reverse("cart"))
        response = self.client.get(reverse("cart"))
        self.assertContains(response, "$44.00")
        self.assertContains(response, "$5.00")

        self.client.post(reverse("cart_update", args=["ceramic-mug"]), {"quantity": "3"})
        response = self.client.get(reverse("cart"))
        self.assertContains(response, "$66.00")
        self.assertContains(response, "Lovely — your order ships free.")

        self.client.post(reverse("cart_remove", args=["ceramic-mug"]))
        response = self.client.get(reverse("cart"))
        self.assertContains(response, "Your bag is taking a breather.")

    def test_checkout_validates_and_clears_demo_cart(self):
        self.client.post(reverse("cart_add", args=["linen-notebook"]), {"quantity": "1"})
        invalid_response = self.client.post(reverse("checkout"), {"email": "not-an-email"})
        self.assertEqual(invalid_response.status_code, 200)
        self.assertContains(invalid_response, "Enter a valid email address.")

        response = self.client.post(reverse("checkout"), {
            "name": "Alex Example",
            "email": "alex@example.com",
            "address": "1 Example Street",
            "city": "Exampletown",
            "postcode": "12345",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "no order was saved")
        self.assertEqual(self.client.session.get("cart"), {})
