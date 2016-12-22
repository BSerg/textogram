from django.test import TestCase

from articles.models import Article, ArticleContentHeader, ArticleContenLead, ArticleContentText


class ArticleContentTestCase(TestCase):
    def setUp(self):
        self.article = Article.objects.create(title='HELLO ARTICLE', slug='hello-article', owner_id=1)
        self.header1 = ArticleContentHeader.objects.create(article=self.article, position=0, text='Header for everyone')
        self.lead1 = ArticleContenLead.objects.create(article=self.article, position=1, text='Lorem lead')
        self.text1 = ArticleContentText.objects.create(article=self.article, position=2,
                                                       text='This is the first content block and it is the text')

    def test_content_instance_of_class(self):
        content_blocks = self.article.content.all()
        self.assertIsInstance(content_blocks[0], ArticleContentHeader)
        self.assertIsInstance(content_blocks[1], ArticleContenLead)
        self.assertIsInstance(content_blocks[2], ArticleContentText)
