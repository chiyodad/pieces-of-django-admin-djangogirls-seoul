from uuid import uuid4

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext as _


class Profile(models.Model):
    registration_routes = (
        ('direct', _('직접 방문 가입'), ),
        ('guestbook', _('게스트북'), ),
        ('cocoa', _('코코아톡'), ),
        ('goggle', _('고글'), ),
        ('navar', _('나바'), ),
    )
    user = models.OneToOneField(settings.AUTH_USER_MODEL)

    registration_route = models.CharField(_('가입 경로'), max_length=40,
                                          choices=registration_routes,
                                          default='direct')


class Product(models.Model):
    statuses = (
        ('active', _('정상'), ),
        ('sold_out', _('품절'), ),
        ('obsolete', _('단종'), ),
        ('deactive', _('비활성화'), ),
    )
    categories = (
        ('decoration', _('장식'), ),
        ('pan', _('팬'), ),
        ('roll', _('롤'), ),
    )

    category = models.CharField(_('상품 갈래'), max_length=20, choices=categories)
    name = models.CharField(_('상품명'), max_length=100)
    content = models.TextField(_('설명'))
    regular_price = models.PositiveIntegerField(_('정가'))
    selling_price = models.PositiveIntegerField(_('판매가'))
    status = models.CharField(_('상태'), max_length=20, choices=statuses)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'<{self.pk}> {self.name}'


class ProductImage(models.Model):
    product = models.ForeignKey(Product)
    content = models.ImageField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Order(models.Model):
    progresses = (
        ('requested', _('주문 요청'), ),
        ('checkout_payment', _('결제 확인 중'), ),
        ('paid', _('결제 완료'), ),
        ('failed_payment', _('결제 실패'), ),
        ('prepared_product', _('상품 준비'), ),
        ('prepared_delivery', _('출고 준비'), ),
        ('ongoing_delivery', _('배송 중'), ),
        ('refund_requested', _('반품/환불 요청'), ),
        ('done', _('거래 완료'), ),
        ('canceled', _('취소'), ),
        ('refunded', _('반품/환불 완료'), ),
        ('replaced', _('교환'), ),
    )

    sn = models.UUIDField(_('일련번호'), unique=True, editable=False, default=uuid4)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
    items = models.ManyToManyField(Product)
    product_cost = models.IntegerField(_('주문 총액'))
    progress = models.CharField(_('진행상태'), max_length=20, choices=progresses,
                                default='requested')
    comment = models.TextField(_('기타 요청사항'), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
