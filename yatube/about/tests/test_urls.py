from django.test import TestCase, Client


class StaticURLTests(TestCase):
    REFERENCE_TEMPLATE_DICT = {
        '/about/author/': 'about/author.html',
        '/about/tech/': 'about/tech.html'
    }

    def setUp(self):
        self.guest_client = Client()

    def test_about_url_exists_at_desired_location(self):
        """Проверка доступности адресов статических страниц."""
        for page_url in self.REFERENCE_TEMPLATE_DICT.keys():
            with self.subTest(url=page_url):
                response = self.guest_client.get(page_url)
                self.assertEqual(response.status_code, 200)

    def test_about_url_uses_correct_template(self):
        """Проверка шаблона для адресов статических страниц."""
        for page_url, page_template in self.REFERENCE_TEMPLATE_DICT.items():
            with self.subTest(url=page_url):
                response = self.guest_client.get(page_url)
                self.assertTemplateUsed(response, page_template)
